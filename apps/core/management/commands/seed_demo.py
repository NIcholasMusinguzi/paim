import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.advisory.models import AdvisoryContent
from apps.analytics.models import (
    DistrictSeasonMetric,
    NationalSeasonMetric,
    ParishSeasonMetric,
    TrendInsight,
)
from apps.analytics.trends import approve_insight
from apps.farmers.models import Crop, Farmer, Planting, Plot, Season
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import AwardRecord, Bid, Buyer, Declaration, Lot, Settlement
from apps.market.services import award_lot, declare, grade_for, maybe_close_lot, submit_bid

DEMO_PASSWORD = "demo1234"
PHONE_PREFIX = "+256700"  # fictitious operator code, safe from colliding with real numbers

# Real Uganda districts/subcounties, in the Lake Victoria Crescent maize-
# and-coffee belt. Parish and village names below are plausible for the
# area but invented for this dataset — this is demo data, not a gazetteer.
GEOGRAPHY = {
    "Mukono": {
        "Kyampisi": [("Katosi", "Kigunga"), ("Nakisunga", "Namawojjolo")],
        "Nama": [("Nama", "Nakabago"), ("Namuganga", "Namuganga Town")],
    },
    "Wakiso": {
        "Nabweru": [("Nabweru", "Kawanda"), ("Kazo", "Kazo Angola")],
        "Kasangati": [("Kasangati", "Kito"), ("Gombe", "Gombe Central")],
    },
    "Jinja": {
        "Budondo": [("Budondo", "Kiwafu"), ("Kimaka", "Kimaka Cell")],
        "Butagaya": [("Butagaya", "Nawantege"), ("Buwenda", "Buwenda Central")],
    },
}

FEMALE_NAMES = [
    "Nabirye Grace", "Namatovu Sarah", "Nakato Josephine", "Nansubuga Betty", "Namuli Harriet",
    "Naigaga Prossy", "Auma Christine", "Nakalembe Rose", "Namusoke Agnes", "Babirye Sylvia",
    "Nabukenya Ruth", "Nalwoga Peace", "Namubiru Joyce", "Kirabo Diana", "Nantongo Esther",
    "Nakawesi Mary", "Nabakooza Florence", "Nassuna Irene", "Namutebi Winnie", "Nyangoma Beatrice",
]
MALE_NAMES = [
    "Ssebunya John", "Kato Peter", "Mukasa David", "Wasswa Robert", "Kizza Moses",
    "Byaruhanga Emmanuel", "Kalyango Simon", "Ssempala Tom", "Mugisha Denis", "Waiswa Fred",
    "Balikuddembe Henry", "Kiggundu Paul", "Musisi Charles", "Kagimu Steven", "Nsubuga Isaac",
    "Lubega Vincent", "Kabuye Richard", "Ochieng Patrick", "Tumusiime Brian", "Muwonge Alex",
]

BUYERS = [
    ("Nile Grain Traders Ltd", "NGL-2024-001"),
    ("Mukono Produce Exchange", "MPE-2024-014"),
    ("Victoria Basin Millers Co.", "VBM-2024-027"),
    ("Busoga Commodity Buyers Ltd", "BCB-2024-039"),
]

MAIZE_ADVICE = [
    (0, 2, "Plant in rows 75cm apart, 2 seeds per hole 25cm apart. Apply DAP at planting if soil is depleted."),
    (3, 6, "First weeding by week 4. Top-dress with CAN or urea once plants are knee-high."),
    (7, 10, "Scout for fall armyworm weekly — check the whorl for ragged holes and frass. Report heavy infestation to your agent."),
    (11, 14, "Check moisture before harvest: below 13% is grade 1. Dry on a tarpaulin, not bare ground, to protect grade."),
]
COFFEE_ADVICE = [
    (0, 20, "Mulch around the base to retain moisture and suppress weeds during establishment."),
    (21, 45, "Prune to a single stem in the first year. Watch for coffee berry borer as cherries begin to form."),
]


class Command(BaseCommand):
    help = "Seed a realistic Ugandan demo dataset — geography, crops, farmers, a full market cycle, metrics and trend insights — so the UI has real data to show instead of empty states."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing demo data (matched by district name) before reseeding.")

    def handle(self, *args, **options):
        if District.objects.filter(name__in=GEOGRAPHY).exists():
            if not options["reset"]:
                self.stdout.write(self.style.WARNING(
                    "Demo data already present (Mukono/Wakiso/Jinja). Re-run with --reset to rebuild it."))
                return
            self._wipe()

        with transaction.atomic():
            crops = self._seed_crops()
            seasons = self._seed_seasons()
            self._seed_advisory(crops)
            geo = self._seed_geography()
            users = self._seed_users(geo)
            farmers = self._seed_farmers(geo, users, crops, seasons["current"])
            buyers = self._seed_buyers()

        # Historical seasons run outside the outer atomic block so each
        # service call's own @transaction.atomic really commits and its
        # on_commit hooks (event publish, metric rollup) fire as they would
        # in production, rather than being nested inside one giant savepoint.
        self._seed_history(geo, crops, seasons, users, farmers, buyers)
        self._seed_current_season(geo, crops, seasons["current"], users, farmers, buyers)
        self._seed_trends(geo, crops)

        self._print_summary(users, buyers)

    # -- geography ----------------------------------------------------

    def _seed_geography(self):
        geo = {"districts": {}, "subcounties": {}, "parishes": {}, "villages": {}}
        for district_name, subcounties in GEOGRAPHY.items():
            district, _ = District.objects.get_or_create(name=district_name, defaults={"region": "Central"})
            geo["districts"][district_name] = district
            for subcounty_name, parishes in subcounties.items():
                subcounty, _ = Subcounty.objects.get_or_create(district=district, name=subcounty_name)
                geo["subcounties"][subcounty_name] = subcounty
                for parish_name, village_name in parishes:
                    parish, _ = Parish.objects.get_or_create(
                        subcounty=subcounty, name=parish_name,
                        defaults={"agro_zone": "Lake Victoria Crescent", "lot_min_bags": 15})
                    geo["parishes"][parish_name] = parish
                    village, _ = Village.objects.get_or_create(parish=parish, name=village_name)
                    geo["villages"][parish_name] = village
        return geo

    # -- reference data -------------------------------------------------

    def _seed_crops(self):
        maize, _ = Crop.objects.get_or_create(name="Maize", defaults={"cycle_weeks": 14})
        coffee, _ = Crop.objects.get_or_create(name="Coffee (Robusta)", defaults={"cycle_weeks": 52})
        return {"maize": maize, "coffee": coffee}

    def _seed_seasons(self):
        today = timezone.localdate()
        current_year = today.year if today.month >= 8 else today.year - 1
        seasons = {}
        seasons["past_b"], _ = Season.objects.get_or_create(
            year=current_year - 1, season_no=2,
            defaults={"start_date": date(current_year - 1, 8, 1), "end_date": date(current_year - 1, 12, 15)})
        seasons["past_a"], _ = Season.objects.get_or_create(
            year=current_year, season_no=1,
            defaults={"start_date": date(current_year, 2, 15), "end_date": date(current_year, 6, 30)})
        seasons["current"], _ = Season.objects.get_or_create(
            year=current_year, season_no=2,
            defaults={"start_date": date(current_year, 8, 1), "end_date": date(current_year, 12, 15)})
        return seasons

    def _seed_advisory(self, crops):
        for week_from, week_to, body in MAIZE_ADVICE:
            AdvisoryContent.objects.get_or_create(
                crop=crops["maize"], agro_zone="", week_from=week_from, week_to=week_to, language="en",
                defaults={"body": body, "source": "MAAIF and NARO", "status": "validated"})
        for week_from, week_to, body in COFFEE_ADVICE:
            AdvisoryContent.objects.get_or_create(
                crop=crops["coffee"], agro_zone="", week_from=week_from, week_to=week_to, language="en",
                defaults={"body": body, "source": "UCDA", "status": "validated"})

    # -- users ------------------------------------------------------------

    def _seed_users(self, geo):
        phones = _PhoneSequence()
        users = {"agents": {}, "chiefs": {}, "subcounty_officers": {}, "district_officers": {}, "national_admin": None}

        users["national_admin"] = self._user(
            phones.next(), "Sarah Namutebi", Role.NATIONAL_ADMIN, ScopeLevel.NATIONAL, None)

        for district_name, district in geo["districts"].items():
            users["district_officers"][district_name] = self._user(
                phones.next(), f"{district_name} District Officer", Role.DISTRICT_OFFICER,
                ScopeLevel.DISTRICT, district.id)
            users["agents"][district_name] = self._user(
                phones.next(), f"{district_name} Field Agent", Role.AGENT, ScopeLevel.DISTRICT, district.id)

        for subcounty_name, subcounty in geo["subcounties"].items():
            users["subcounty_officers"][subcounty_name] = self._user(
                phones.next(), f"{subcounty_name} Subcounty Officer", Role.SUBCOUNTY_OFFICER,
                ScopeLevel.SUBCOUNTY, subcounty.id)

        for parish_name, parish in geo["parishes"].items():
            users["chiefs"][parish_name] = self._user(
                phones.next(), f"{parish_name} Parish Chief", Role.PARISH_CHIEF, ScopeLevel.PARISH, parish.id)

        self._phones = phones
        return users

    def _user(self, phone, full_name, role, scope_level, scope_id):
        user, created = SystemUser.objects.get_or_create(
            phone=phone, defaults={"full_name": full_name, "role": role,
                                   "scope_level": scope_level, "scope_id": scope_id})
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save(update_fields=["password"])
        return user

    # -- farmers ------------------------------------------------------------

    def _seed_farmers(self, geo, users, crops, current_season):
        rng = random.Random(42)
        names = [(n, "F") for n in FEMALE_NAMES] + [(n, "M") for n in MALE_NAMES]
        rng.shuffle(names)
        parish_names = list(geo["parishes"])
        farmers = []
        today = timezone.localdate()

        for i, (full_name, sex) in enumerate(names):
            parish_name = parish_names[i % len(parish_names)]
            parish = geo["parishes"][parish_name]
            village = geo["villages"][parish_name]
            district_name = parish.subcounty.district.name
            agent = users["agents"][district_name]
            crop = crops["maize"] if i % 4 != 0 else crops["coffee"]

            phone = self._phones.next() if i % 5 == 0 else None  # most farmers reach only via agent
            farmer = Farmer.objects.create(
                village=village, full_name=full_name, sex=sex, language="en",
                reach_channel="agent" if phone is None else "sms",
                phone=phone, registered_by=agent)

            if phone and i % 10 == 0:  # a handful of farmers also get a web login
                login = self._user(phone, full_name, Role.FARMER, ScopeLevel.PARISH, parish.id)
                farmer.user = login
                farmer.save(update_fields=["user"])

            plot = Plot.objects.create(farmer=farmer, area_acres=rng.choice(["0.75", "1.0", "1.5", "2.0", "2.5"]))
            Planting.objects.create(
                plot=plot, season=current_season, crop=crop,
                planting_date=today - timedelta(weeks=rng.randint(1, 10)))

            farmers.append({"farmer": farmer, "parish": parish_name, "crop": "maize" if crop == crops["maize"] else "coffee"})
        return farmers

    def _seed_buyers(self):
        buyers = []
        for name, licence_no in BUYERS:
            phone = self._phones.next()
            user = self._user(phone, name, Role.BUYER, ScopeLevel.NATIONAL, None)
            buyer, _ = Buyer.objects.get_or_create(
                licence_no=licence_no, defaults={"name": name, "user": user, "verified_at": timezone.now()})
            buyers.append(buyer)
        return buyers

    # -- market cycles ------------------------------------------------------

    def _seed_history(self, geo, crops, seasons, users, farmers, buyers):
        """Two full, closed-and-settled seasons per parish/crop so metrics,
        district rollups and the national ranking have real numbers instead
        of empty tables."""
        rng = random.Random(7)
        for season_key in ("past_b", "past_a"):
            season = seasons[season_key]
            base_price = 950 if season_key == "past_b" else 1050
            for parish_name, parish in geo["parishes"].items():
                chief = users["chiefs"][parish_name]
                for crop_key, crop in (("maize", crops["maize"]), ("coffee", crops["coffee"])):
                    parish_farmers = [f["farmer"] for f in farmers if f["parish"] == parish_name]
                    if not parish_farmers:
                        continue
                    lot = Lot.objects.create(parish=parish, season=season, crop=crop, min_bags=parish.lot_min_bags)
                    for farmer in parish_farmers[:6]:
                        bags = rng.randint(3, 8)
                        moisture = rng.choice(["11.5", "12.8", "13.5", "14.9", "16.2"])
                        Declaration.objects.create(
                            farmer=farmer, lot=lot, bags=bags, moisture_pct=moisture,
                            grade=grade_for(moisture), declared_via="agent")
                    lot.refresh_from_db()
                    price = base_price + rng.randint(-80, 120) + (300 if crop_key == "coffee" else 0)
                    b1, b2 = rng.sample(buyers, 2)
                    submit_bid(lot=lot, buyer=b1, price_per_kg=price, terms="Cash on delivery")
                    submit_bid(lot=lot, buyer=b2, price_per_kg=price - rng.randint(10, 40), terms="Mobile money, 48h")
                    lot = maybe_close_lot(lot)
                    if lot.status == "closed":
                        top_bid = lot.bids.order_by("-price_per_kg").first()
                        award_lot(lot_id=lot.id, bid_id=top_bid.id, actor=chief,
                                 minute_ref=f"{parish_name}-{season.year}{season.season_no}-{crop_key}")

    def _seed_current_season(self, geo, crops, season, users, farmers, buyers):
        """The in-progress season: most parishes show a partially filled
        lot; one — whichever actually has the most maize growers, not just
        "the first parish" — runs all the way to a closed-but-unawarded lot
        so the officer's award action and the buyer's disclosed-bid view
        both have something real to show."""
        rng = random.Random(99)
        by_parish: dict[str, list] = {}
        for f in farmers:
            if f["crop"] == "maize":
                by_parish.setdefault(f["parish"], []).append(f["farmer"])
        if not by_parish:
            return
        showcase = max(by_parish, key=lambda p: len(by_parish[p]))

        for parish_name, parish_farmers in by_parish.items():
            parish = geo["parishes"][parish_name]
            agent = users["agents"][parish.subcounty.district.name]

            if parish_name == showcase:
                # Bids must go in while the lot is still open — that is the
                # whole sealing mechanism — so: declare short of min_bags,
                # take bids while sealed, then push over the line so the
                # lot really closes and the bids become disclosed. Left
                # unawarded on purpose, for the officer/buyer award demo.
                declare(farmer=parish_farmers[0], crop=crops["maize"],
                       bags=max(1, parish.lot_min_bags - 5), moisture="12.5", actor=agent, via="agent")
                lot = Lot.objects.filter(parish=parish, season=season, crop=crops["maize"]).order_by("-opened_at").first()
                b1, b2 = rng.sample(buyers, 2)
                submit_bid(lot=lot, buyer=b1, price_per_kg=1120, terms="Cash on delivery")
                submit_bid(lot=lot, buyer=b2, price_per_kg=1080, terms="Mobile money, 48h")
                declare(farmer=parish_farmers[min(1, len(parish_farmers) - 1)], crop=crops["maize"],
                       bags=parish.lot_min_bags, moisture="12.8", actor=agent, via="agent")
                continue

            take = max(1, len(parish_farmers) // 2)
            for farmer in parish_farmers[:take]:
                moisture = rng.choice(["12.1", "13.0", "14.2", None])
                declare(farmer=farmer, crop=crops["maize"], bags=rng.randint(2, 6),
                       moisture=moisture, actor=agent, via="agent")

    # -- trend insights -------------------------------------------------

    def _seed_trends(self, geo, crops):
        mukono = geo["districts"]["Mukono"]
        katosi = geo["parishes"]["Katosi"]
        published = TrendInsight.objects.create(
            scope_level=ScopeLevel.DISTRICT, scope_id=mukono.id, crop=crops["maize"], metric="avg_price_per_kg",
            direction="up", magnitude="8.00", window_weeks=3,
            message="Maize prices in Mukono have risen 8% over the last three seasons as more buyers compete at harvest.")
        approve_insight(insight_id=published.id, actor=SystemUser.objects.filter(role=Role.NATIONAL_ADMIN).first())

        TrendInsight.objects.create(
            scope_level=ScopeLevel.PARISH, scope_id=katosi.id, crop=crops["maize"], metric="moisture_pct",
            direction="up", magnitude="15.00", window_weeks=2,
            message="Moisture readings in Katosi are running higher than usual this week — check drying practice before the next lot closes.")
        TrendInsight.objects.create(
            scope_level=ScopeLevel.NATIONAL, scope_id=None, crop=crops["coffee"], metric="pct_grade1",
            direction="down", magnitude="6.00", window_weeks=4,
            message="Grade 1 share for coffee has slipped nationally — sample coverage is below 60% of registered farmers, so treat this as a hypothesis, not a finding.")

    # -- cleanup / reporting ------------------------------------------------

    def _wipe(self):
        Settlement.objects.all().delete()
        AwardRecord.objects.all().delete()
        Bid.objects.all().delete()
        Declaration.objects.filter(lot__parish__subcounty__district__name__in=GEOGRAPHY).delete()
        Lot.objects.filter(parish__subcounty__district__name__in=GEOGRAPHY).delete()
        TrendInsight.objects.all().delete()
        ParishSeasonMetric.objects.filter(parish__subcounty__district__name__in=GEOGRAPHY).delete()
        DistrictSeasonMetric.objects.filter(district__name__in=GEOGRAPHY).delete()
        NationalSeasonMetric.objects.all().delete()
        Farmer.objects.filter(village__parish__subcounty__district__name__in=GEOGRAPHY).delete()
        AdvisoryContent.objects.filter(crop__name__in=["Maize", "Coffee (Robusta)"]).delete()
        Buyer.objects.filter(licence_no__in=[b[1] for b in BUYERS]).delete()
        SystemUser.objects.filter(phone__startswith=PHONE_PREFIX).delete()
        Village.objects.filter(parish__subcounty__district__name__in=GEOGRAPHY).delete()
        Parish.objects.filter(subcounty__district__name__in=GEOGRAPHY).delete()
        Subcounty.objects.filter(district__name__in=GEOGRAPHY).delete()
        District.objects.filter(name__in=GEOGRAPHY).delete()

    def _print_summary(self, users, buyers):
        self.stdout.write(self.style.SUCCESS("\nDemo data seeded. Every account's password is: " + DEMO_PASSWORD))
        self.stdout.write("\nSign in as:")
        self.stdout.write(f"  National admin      {users['national_admin'].phone}")
        for name, u in users["district_officers"].items():
            self.stdout.write(f"  {name} district officer   {u.phone}")
        for name, u in list(users["chiefs"].items())[:3]:
            self.stdout.write(f"  {name} parish chief        {u.phone}")
        for buyer in buyers[:2]:
            self.stdout.write(f"  {buyer.name:<24} {buyer.user.phone}")
        farmer_login = Farmer.objects.filter(user__isnull=False).select_related("user").first()
        if farmer_login:
            self.stdout.write(f"  {farmer_login.full_name:<24} {farmer_login.user.phone}  (farmer)")


class _PhoneSequence:
    def __init__(self):
        self._n = 0

    def next(self) -> str:
        self._n += 1
        return f"{PHONE_PREFIX}{self._n:05d}"
