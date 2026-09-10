import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.advisory.models import (
    AdvisoryContent,
    AdvisoryDelivery,
    AdvisoryRequest,
    AdvisoryResponse,
    Comment,
    Post,
)
from apps.advisory.services import add_comment, create_post, respond_to_request, submit_advisory_request
from apps.analytics.models import (
    DistrictSeasonMetric,
    NationalSeasonMetric,
    ParishSeasonMetric,
    TrendInsight,
)
from apps.analytics.trends import approve_insight
from apps.farmers.models import Crop, Farmer, Planting, Plot, Season
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import AwardRecord, Bid, Buyer, Declaration, Lot, MarketPrice, Settlement
from apps.market.services import award_lot, declare, grade_for, maybe_close_lot, submit_bid

DEMO_PASSWORD = "demo1234"
PHONE_PREFIX = "+256700"  # fictitious operator code, safe from colliding with real numbers

# Real Uganda districts/subcounties in the Lake Victoria Crescent maize-
# and-coffee belt. Parish and village names below are plausible for the
# area but invented for this dataset — this is demo data, not a gazetteer.
# Minimum 10 of each geo level; each district has nested subcounties.
GEOGRAPHY = {
    "Mukono": {
        "Kyampisi": [("Katosi", "Kigunga", "Katosi Landing"), ("Nakisunga", "Namawojjolo", "Nakisunga East")],
        "Nama": [("Nama", "Nakabago", "Nama Hill"), ("Namuganga", "Namuganga Town", "Namuganga West")],
    },
    "Wakiso": {
        "Nabweru": [("Nabweru", "Kawanda", "Kawanda South"), ("Kazo", "Kazo Angola", "Kazo Central")],
        "Kasangati": [("Kasangati", "Kito", "Kito Trading"), ("Gombe", "Gombe Central", "Gombe West")],
    },
    "Jinja": {
        "Budondo": [("Budondo", "Kiwafu", "Kiwafu East"), ("Kimaka", "Kimaka Cell", "Kimaka North")],
        "Butagaya": [("Butagaya", "Nawantege", "Nawantege A"), ("Buwenda", "Buwenda Central", "Buwenda Landing")],
    },
    "Buikwe": {
        "Lugazi": [("Lugazi Central", "Kikawula", "Kikawula B"), ("Kavule", "Kavule A", "Kavule Trading")],
        "Najja": [("Najja", "Busagazi", "Busagazi Shore"), ("Nyenga", "Nyenga Town", "Nyenga East")],
    },
    "Kayunga": {
        "Nazigo": [("Nazigo", "Kisoga", "Kisoga A"), ("Ntenjeru", "Ntenjeru Hill", "Ntenjeru B")],
        "Kangulumira": [("Kangulumira", "Wabirongo", "Wabirongo East"), ("Kitimbwa", "Kitimbwa A", "Kitimbwa Market")],
    },
    "Luweero": {
        "Bamunanika": [("Bamunanika", "Kikyusa", "Kikyusa Road"), ("Kalagala", "Kalagala Central", "Kalagala West")],
        "Zirobwe": [("Zirobwe", "Naluvule", "Naluvule A"), ("Kamira", "Kamira Village", "Kamira East")],
    },
    "Mpigi": {
        "Kammengo": [("Kammengo", "Buwe", "Buwe A"), ("Muduuma", "Muduuma A", "Muduuma Trading")],
        "Mpigi Town": [("Mpigi Central", "Kafumu", "Kafumu B"), ("Kiringente", "Kiringente A", "Kiringente West")],
    },
    "Masaka": {
        "Kyanamukaaka": [("Kyanamukaaka", "Buyaga", "Buyaga Landing"), ("Bukakata", "Bukakata Landing", "Bukakata Town")],
        "Mukungwe": [("Mukungwe", "Nyendo", "Nyendo Market"), ("Kimaanya", "Kimaanya A", "Kimaanya Hill")],
    },
    "Mityana": {
        "Busunju": [("Busunju", "Ttamu", "Ttamu East"), ("Ssekanyonyi", "Ssekanyonyi Town", "Ssekanyonyi West")],
        "Bbanda": [("Bbanda", "Naama", "Naama A"), ("Maanyi", "Maanyi Central", "Maanyi B")],
    },
    "Iganga": {
        "Nawandala": [("Nawandala", "Itanda", "Itanda East"), ("Nakigo", "Nakigo A", "Nakigo Market")],
        "Kigulu": [("Kigulu", "Bulamagi", "Bulamagi A"), ("Nambale", "Nambale Village", "Nambale Central")],
    },
}

DISTRICT_REGION = {
    "Jinja": "Eastern",
    "Iganga": "Eastern",
    "Kayunga": "Central",
}

CROPS = [
    ("Maize", 14),
    ("Coffee (Robusta)", 52),
    ("Beans", 12),
    ("Cassava", 48),
    ("Banana (Matooke)", 52),
    ("Sweet potato", 16),
    ("Groundnuts", 16),
    ("Rice", 18),
    ("Sorghum", 16),
    ("Irish potato", 14),
    ("Soybean", 14),
    ("Millet", 14),
]

FEMALE_NAMES = [
    "Nabirye Grace", "Namatovu Sarah", "Nakato Josephine", "Nansubuga Betty", "Namuli Harriet",
    "Naigaga Prossy", "Auma Christine", "Nakalembe Rose", "Namusoke Agnes", "Babirye Sylvia",
    "Nabukenya Ruth", "Nalwoga Peace", "Namubiru Joyce", "Kirabo Diana", "Nantongo Esther",
    "Nakawesi Mary", "Nabakooza Florence", "Nassuna Irene", "Namutebi Winnie", "Nyangoma Beatrice",
    "Namuddu Claire", "Nakitto Helen", "Akello Fiona", "Nalubega Joan", "Nabatanzi Lydia",
    "Namakula Stella", "Nambooze Rita", "Aanyu Gloria", "Nalwanga Edith", "Namukwaya Hope",
    "Nakirya Pauline", "Nankya Juliet", "Amongi Charity", "Naggayi Faith", "Nalubowa Alice",
    "Namugga Brenda", "Nakiwala Susan", "Acen Mercy", "Nalweyiso Carol", "Namusobya Doreen",
]
MALE_NAMES = [
    "Ssebunya John", "Kato Peter", "Mukasa David", "Wasswa Robert", "Kizza Moses",
    "Byaruhanga Emmanuel", "Kalyango Simon", "Ssempala Tom", "Mugisha Denis", "Waiswa Fred",
    "Balikuddembe Henry", "Kiggundu Paul", "Musisi Charles", "Kagimu Steven", "Nsubuga Isaac",
    "Lubega Vincent", "Kabuye Richard", "Ochieng Patrick", "Tumusiime Brian", "Muwonge Alex",
    "Sserwadda James", "Okello Daniel", "Kiwanuka George", "Mbabazi Allan", "Ssekandi Joseph",
    "Wamala Samuel", "Kasozi Michael", "Odongo Francis", "Nsubuga Mark", "Lwanga Phillip",
    "Mugabi Ronald", "Ssekitoleko Ivan", "Were Andrew", "Kato Nathan", "Muwanga Elvis",
    "Ssemakula Ben", "Okoth Martin", "Kizito Arnold", "Nsubuga Caleb", "Mugoya Derrick",
]

BUYERS = [
    ("Nile Grain Traders Ltd", "NGL-2024-001"),
    ("Mukono Produce Exchange", "MPE-2024-014"),
    ("Victoria Basin Millers Co.", "VBM-2024-027"),
    ("Busoga Commodity Buyers Ltd", "BCB-2024-039"),
    ("Crescent Coffee Exporters", "CCE-2024-052"),
    ("Lugazi Agro Processors", "LAP-2024-061"),
    ("Kayunga Fresh Markets Ltd", "KFM-2024-073"),
    ("Masaka Grain Stores", "MGS-2024-088"),
    ("Mpigi Farm Inputs Hub", "MFI-2024-094"),
    ("Iganga Commodity Desk", "ICD-2024-108"),
    ("Luweero Maize Union", "LMU-2024-115"),
    ("Mityana Horticulture Co.", "MHC-2024-122"),
]

MARKET_PRICES = [
    ("Maize grain", "produce", 1150, "UGX/kg", "Katosi landing", "Farm-gate survey"),
    ("Dry beans (Nambale)", "produce", 3200, "UGX/kg", "Nakasero market", "Farm-gate survey"),
    ("Robusta kiboko", "produce", 4500, "UGX/kg", "Mukono coffee mill", "UCDA weekly"),
    ("Cassava fresh", "produce", 800, "UGX/kg", "Jinja central", "Farm-gate survey"),
    ("Matooke bunch", "produce", 18000, "UGX/bunch", "Masaka taxi park", "Farm-gate survey"),
    ("Rice (upland)", "produce", 2800, "UGX/kg", "Iganga market", "Farm-gate survey"),
    ("Groundnuts unshelled", "produce", 2100, "UGX/kg", "Kayunga market", "Farm-gate survey"),
    ("Sweet potato", "produce", 900, "UGX/kg", "Wakiso stalls", "Farm-gate survey"),
    ("Sorghum", "produce", 1400, "UGX/kg", "Luweero market", "Farm-gate survey"),
    ("DAP fertiliser 50kg", "input", 165000, "UGX/bag", "Nalukolongo agro", "Input dealer list"),
    ("Urea 50kg", "input", 148000, "UGX/bag", "Nalukolongo agro", "Input dealer list"),
    ("Maize seed Longe 10H", "input", 8500, "UGX/kg", "NARO stockist", "Input dealer list"),
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
    (46, 52, "Pick only red ripe cherries. Keep harvested cherry in shade and deliver to the mill the same day."),
]
BEANS_ADVICE = [
    (0, 3, "Plant at the onset of rains. Inoculate seed if soils are tired from continuous maize."),
    (4, 8, "Weed early and watch for bean fly. Avoid walking the field when leaves are wet."),
    (9, 12, "Harvest when pods rattle. Dry on a raised rack to keep weevils down."),
]
CASSAVA_ADVICE = [
    (0, 12, "Plant disease-free cuttings on ridges. Space 1m x 1m for branching varieties."),
    (13, 36, "Keep the field weed-free in the first three months. Report cassava mosaic leaf symptoms to your agent."),
]

POSTS = [
    ("National", "Season B planting window", "Plant maize by mid-August where rains have started. Agents will share parish-level dates this week."),
    ("National", "Moisture before you sell", "Grade 1 maize is below 13% moisture. Dry on tarpaulins — not the roadside — or the lot will be discounted."),
    ("National", "Fall armyworm alert", "Scout the whorl twice a week. Report heavy infestation through Ask for advice so the parish chief can mobilise spray teams."),
    ("District", "Buyer day at the store", "Verified buyers will inspect the parish store on Friday. Bring declarations that are already graded."),
    ("District", "Input voucher reminder", "DAP and urea vouchers expire at month end. Collect from the subcounty store with your farmer card."),
    ("District", "Coffee cherry quality", "Only red ripe cherry will be accepted at the mill this week. Green cherry will be turned away."),
    ("Parish", "Lot closing this week", "The maize lot is close to the bag minimum. Declare remaining bags with your agent before Thursday."),
    ("Parish", "Drying demo Saturday", "Parish chief will run a drying demo at the store from 9am. Bring a sample of this week's harvest."),
    ("Parish", "Village meeting", "Village savings groups meet Sunday after prayers to discuss transport to the store."),
    ("Parish", "Grading hours", "The agent will be at the store 7am–1pm Tuesday and Thursday for moisture tests."),
    ("Parish", "Beans side-lot", "A beans lot is open alongside maize. Separate bags — mixed crop will not be accepted."),
    ("Parish", "Settlement timing", "Awarded lots are paid within 48 hours of the committee minute. Keep your mobile-money number active."),
]

COMMENTS = [
    "We will pass this to the village savings group tonight.",
    "Please confirm whether Gombe is included in Friday's buyer day.",
    "Moisture at our store was 14.2% yesterday — we will re-dry.",
    "Can the agent visit Katosi Landing on Wednesday?",
    "Farmers in Nama asked for more tarpaulins before the demo.",
    "Coffee farmers want the mill opening hours posted again.",
    "Understood — we will keep maize and beans in separate bags.",
    "Is the DAP voucher valid at Lugazi stockists as well?",
    "Fall armyworm is already in two gardens in Kawanda.",
    "Thank you. We will bring remaining bags on Thursday morning.",
    "Please share the buyer licence numbers before Friday.",
    "The Saturday demo clashes with the market day — can it move to 7am?",
]

ADVICE_QUESTIONS = [
    "My maize leaves are ragged at the whorl. Is this fall armyworm and what should I spray?",
    "Moisture is 14.8% after two days on a tarpaulin. How much longer before I can declare?",
    "Can I mix last season's maize with this season's lot?",
    "Coffee cherries are turning yellow, not red. Should I still pick?",
    "Where do I collect the DAP voucher for Nama parish?",
    "The lot closed before I declared 4 bags. What happens to them?",
    "Beans have holes in the pods. Is that bean fly or weevils in store?",
    "What price should I expect for grade 2 maize this week?",
    "Can a buyer collect from the village or only from the parish store?",
    "Cassava leaves are mottled yellow. Should I uproot the plants?",
    "How do I change the mobile-money number used for settlement?",
    "Is there a beans lot open in Kasangati this season?",
]


class Command(BaseCommand):
    help = "Seed a realistic Ugandan demo dataset — geography, crops, farmers, a full market cycle, metrics and trend insights — so the UI has real data to show instead of empty states."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing demo data (matched by district name) before reseeding.")

    def handle(self, *args, **options):
        if District.objects.filter(name__in=GEOGRAPHY).exists():
            if not options["reset"]:
                self.stdout.write(self.style.WARNING(
                    "Demo data already present. Re-run with --reset to rebuild the larger dataset."))
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
            self._seed_market_prices()

        # Historical seasons run outside the outer atomic block so each
        # service call's own @transaction.atomic really commits and its
        # on_commit hooks (event publish, metric rollup) fire as they would
        # in production, rather than being nested inside one giant savepoint.
        self._seed_history(geo, crops, seasons, users, farmers, buyers)
        self._seed_current_season(geo, crops, seasons["current"], users, farmers, buyers)
        self._seed_posts(geo, users, farmers)
        self._seed_advisory_requests(geo, users, farmers)
        self._seed_trends(geo, crops)

        self._print_summary(users, buyers)

    # -- geography ----------------------------------------------------

    def _seed_geography(self):
        geo = {"districts": {}, "subcounties": {}, "parishes": {}, "villages": {}, "villages_by_parish": {}}
        for district_name, subcounties in GEOGRAPHY.items():
            district, _ = District.objects.get_or_create(
                name=district_name,
                defaults={"region": DISTRICT_REGION.get(district_name, "Central")})
            geo["districts"][district_name] = district
            for subcounty_name, parishes in subcounties.items():
                subcounty, _ = Subcounty.objects.get_or_create(district=district, name=subcounty_name)
                geo["subcounties"][subcounty_name] = subcounty
                for parish_name, *village_names in parishes:
                    parish, _ = Parish.objects.get_or_create(
                        subcounty=subcounty, name=parish_name,
                        defaults={"agro_zone": "Lake Victoria Crescent", "lot_min_bags": 15})
                    geo["parishes"][parish_name] = parish
                    geo["villages_by_parish"][parish_name] = []
                    for village_name in village_names:
                        village, _ = Village.objects.get_or_create(parish=parish, name=village_name)
                        geo["villages_by_parish"][parish_name].append(village)
                    geo["villages"][parish_name] = geo["villages_by_parish"][parish_name][0]
        return geo

    # -- reference data -------------------------------------------------

    def _seed_crops(self):
        crops = {}
        for name, weeks in CROPS:
            crop, _ = Crop.objects.get_or_create(name=name, defaults={"cycle_weeks": weeks})
            key = "coffee" if name.startswith("Coffee") else "banana" if name.startswith("Banana") else name.split()[0].lower()
            crops[key] = crop
        return crops

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
        for week_from, week_to, body in BEANS_ADVICE:
            AdvisoryContent.objects.get_or_create(
                crop=crops["beans"], agro_zone="", week_from=week_from, week_to=week_to, language="en",
                defaults={"body": body, "source": "NARO", "status": "validated"})
        for week_from, week_to, body in CASSAVA_ADVICE:
            AdvisoryContent.objects.get_or_create(
                crop=crops["cassava"], agro_zone="", week_from=week_from, week_to=week_to, language="en",
                defaults={"body": body, "source": "NARO", "status": "validated"})

    def _seed_market_prices(self):
        today = timezone.localdate()
        for i, (item_name, category, price, unit, market, source) in enumerate(MARKET_PRICES):
            MarketPrice.objects.get_or_create(
                item_name=item_name, price_date=today - timedelta(days=i % 5), market=market,
                defaults={
                    "category": category, "price": price, "unit": unit,
                    "source": f"PAIM demo seed — {source}",
                })

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
        crop_cycle = [crops["maize"], crops["maize"], crops["maize"], crops["coffee"],
                      crops["beans"], crops["cassava"], crops["banana"], crops["rice"],
                      crops["groundnuts"], crops["sorghum"]]
        farmers = []
        today = timezone.localdate()

        for i, (full_name, sex) in enumerate(names):
            parish_name = parish_names[i % len(parish_names)]
            parish = geo["parishes"][parish_name]
            villages = geo["villages_by_parish"][parish_name]
            village = villages[i % len(villages)]
            district_name = parish.subcounty.district.name
            agent = users["agents"][district_name]
            crop = crop_cycle[i % len(crop_cycle)]
            crop_key = next(k for k, v in crops.items() if v == crop)

            phone = self._phones.next() if i % 4 == 0 else None
            farmer = Farmer.objects.create(
                village=village, full_name=full_name, sex=sex, language="en",
                reach_channel="agent" if phone is None else "sms",
                phone=phone, registered_by=agent)

            if phone:
                login = self._user(phone, full_name, Role.FARMER, ScopeLevel.PARISH, parish.id)
                farmer.user = login
                farmer.save(update_fields=["user"])

            plot = Plot.objects.create(farmer=farmer, area_acres=rng.choice(["0.75", "1.0", "1.5", "2.0", "2.5"]))
            Planting.objects.create(
                plot=plot, season=current_season, crop=crop,
                planting_date=today - timedelta(weeks=rng.randint(1, 10)))

            farmers.append({"farmer": farmer, "parish": parish_name, "crop": crop_key})
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

    def _fill_closed_lot(self, *, parish, season, crop, farmers, buyers, chief, rng, minute_ref, base_price):
        if not farmers:
            return
        lot = Lot.objects.create(parish=parish, season=season, crop=crop, min_bags=parish.lot_min_bags)
        for farmer in farmers[:6]:
            bags = rng.randint(3, 8)
            moisture = rng.choice(["11.5", "12.8", "13.5", "14.9", "16.2"])
            Declaration.objects.create(
                farmer=farmer, lot=lot, bags=bags, moisture_pct=moisture,
                grade=grade_for(moisture), declared_via="agent")
        lot.refresh_from_db()
        price = base_price + rng.randint(-80, 120)
        taken = rng.sample(buyers, min(3, len(buyers)))
        for i, buyer in enumerate(taken):
            submit_bid(lot=lot, buyer=buyer, price_per_kg=price - i * rng.randint(10, 40),
                       terms="Cash on delivery" if i == 0 else "Mobile money, 48h")
        lot = maybe_close_lot(lot)
        if lot.status == "closed":
            top_bid = lot.bids.order_by("-price_per_kg").first()
            award_lot(lot_id=lot.id, bid_id=top_bid.id, actor=chief, minute_ref=minute_ref)

    def _seed_history(self, geo, crops, seasons, users, farmers, buyers):
        """Closed-and-settled seasons per parish so metrics, district rollups
        and the national ranking have real numbers instead of empty tables."""
        rng = random.Random(7)
        for season_key in ("past_b", "past_a"):
            season = seasons[season_key]
            base_price = 950 if season_key == "past_b" else 1050
            for parish_name, parish in geo["parishes"].items():
                chief = users["chiefs"][parish_name]
                parish_farmers = [f["farmer"] for f in farmers if f["parish"] == parish_name]
                self._fill_closed_lot(
                    parish=parish, season=season, crop=crops["maize"], farmers=parish_farmers,
                    buyers=buyers, chief=chief, rng=rng,
                    minute_ref=f"{parish_name}-{season.year}{season.season_no}-maize",
                    base_price=base_price)
        for parish_name, parish in list(geo["parishes"].items())[:12]:
            chief = users["chiefs"][parish_name]
            parish_farmers = [f["farmer"] for f in farmers if f["parish"] == parish_name]
            self._fill_closed_lot(
                parish=parish, season=seasons["past_a"], crop=crops["coffee"], farmers=parish_farmers,
                buyers=buyers, chief=chief, rng=rng,
                minute_ref=f"{parish_name}-{seasons['past_a'].year}A-coffee",
                base_price=1350)

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
                for i, buyer in enumerate(buyers[:4]):
                    submit_bid(lot=lot, buyer=buyer, price_per_kg=1120 - i * 20,
                               terms="Cash on delivery" if i == 0 else "Mobile money, 48h")
                declare(farmer=parish_farmers[min(1, len(parish_farmers) - 1)], crop=crops["maize"],
                       bags=parish.lot_min_bags, moisture="12.8", actor=agent, via="agent")
                continue

            take = max(1, len(parish_farmers) // 2)
            for farmer in parish_farmers[:take]:
                moisture = rng.choice(["12.1", "13.0", "14.2", None])
                declare(farmer=farmer, crop=crops["maize"], bags=rng.randint(2, 6),
                       moisture=moisture, actor=agent, via="agent")

        extra_keys = ["beans", "cassava", "banana", "rice", "groundnuts",
                      "sorghum", "sweet", "irish", "soybean", "millet"]
        parish_items = list(geo["parishes"].items())
        for i, key in enumerate(extra_keys):
            crop = crops.get(key)
            if crop is None:
                continue
            parish_name, parish = parish_items[i % len(parish_items)]
            agent = users["agents"][parish.subcounty.district.name]
            parish_farmers = [f["farmer"] for f in farmers if f["parish"] == parish_name]
            if not parish_farmers:
                continue
            declare(farmer=parish_farmers[0], crop=crop, bags=rng.randint(2, 5),
                    moisture=rng.choice(["12.4", "13.1", None]), actor=agent, via="agent")
            lot = Lot.objects.filter(parish=parish, season=season, crop=crop).order_by("-opened_at").first()
            if lot and lot.status == "open":
                for j, buyer in enumerate(rng.sample(buyers, min(2, len(buyers)))):
                    submit_bid(lot=lot, buyer=buyer, price_per_kg=900 + i * 40 - j * 15,
                               terms="Cash on delivery")

    # -- posts / advisory requests -----------------------------------------

    def _seed_posts(self, geo, users, farmers):
        admin = users["national_admin"]
        district_names = list(geo["districts"])
        parish_names = list(geo["parishes"])
        farmer_users = [f["farmer"].user for f in farmers if f["farmer"].user_id]
        comment_i = 0
        for i, (kind, title, body) in enumerate(POSTS):
            if kind == "National":
                post = create_post(author=admin, scope_level=ScopeLevel.NATIONAL, scope_id=None,
                                   title=title, body=body)
            elif kind == "District":
                name = district_names[i % len(district_names)]
                post = create_post(author=users["district_officers"][name],
                                   scope_level=ScopeLevel.DISTRICT, scope_id=geo["districts"][name].id,
                                   title=f"{name}: {title}", body=body)
            else:
                name = parish_names[i % len(parish_names)]
                post = create_post(author=users["chiefs"][name],
                                   scope_level=ScopeLevel.PARISH, scope_id=geo["parishes"][name].id,
                                   title=f"{name}: {title}", body=body)
            authors = [admin, users["agents"][district_names[i % len(district_names)]]]
            if farmer_users:
                authors.append(farmer_users[i % len(farmer_users)])
            add_comment(post=post, author=authors[0], body=COMMENTS[comment_i % len(COMMENTS)])
            comment_i += 1
            add_comment(post=post, author=authors[1], body=COMMENTS[comment_i % len(COMMENTS)])
            comment_i += 1

    def _seed_advisory_requests(self, geo, users, farmers):
        parish_names = list(geo["parishes"])
        logged_in = [f for f in farmers if f["farmer"].user_id]
        for i, message in enumerate(ADVICE_QUESTIONS):
            if logged_in:
                row = logged_in[i % len(logged_in)]
                req = submit_advisory_request(
                    requester=row["farmer"].user, message=message, farmer=row["farmer"])
            else:
                name = parish_names[i % len(parish_names)]
                req = submit_advisory_request(
                    requester=users["chiefs"][name], message=message)
            if i % 2 == 0:
                parish_name = (logged_in[i % len(logged_in)]["parish"] if logged_in
                               else parish_names[i % len(parish_names)])
                respond_to_request(
                    advisory_request=req, responder=users["chiefs"][parish_name],
                    body="Visit the parish store this week — the agent will advise on the next step for your crop.")

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
        Comment.objects.filter(author__phone__startswith=PHONE_PREFIX).delete()
        Post.objects.filter(author__phone__startswith=PHONE_PREFIX).delete()
        AdvisoryResponse.objects.filter(responder__phone__startswith=PHONE_PREFIX).delete()
        AdvisoryRequest.objects.filter(requester__phone__startswith=PHONE_PREFIX).delete()
        MarketPrice.objects.filter(source__startswith="PAIM demo seed").delete()
        AdvisoryDelivery.objects.filter(
            farmer__village__parish__subcounty__district__name__in=GEOGRAPHY).delete()
        TrendInsight.objects.all().delete()
        ParishSeasonMetric.objects.filter(parish__subcounty__district__name__in=GEOGRAPHY).delete()
        DistrictSeasonMetric.objects.filter(district__name__in=GEOGRAPHY).delete()
        NationalSeasonMetric.objects.all().delete()
        Farmer.objects.filter(village__parish__subcounty__district__name__in=GEOGRAPHY).delete()
        crop_names = [name for name, _ in CROPS]
        AdvisoryContent.objects.filter(crop__name__in=crop_names).delete()
        Buyer.objects.filter(licence_no__in=[b[1] for b in BUYERS]).delete()
        SystemUser.objects.filter(phone__startswith=PHONE_PREFIX).delete()
        Village.objects.filter(parish__subcounty__district__name__in=GEOGRAPHY).delete()
        Parish.objects.filter(subcounty__district__name__in=GEOGRAPHY).delete()
        Subcounty.objects.filter(district__name__in=GEOGRAPHY).delete()
        District.objects.filter(name__in=GEOGRAPHY).delete()
        Crop.objects.filter(name__in=crop_names).delete()

    def _print_summary(self, users, buyers):
        self.stdout.write(self.style.SUCCESS("\nDemo data seeded. Every account's password is: " + DEMO_PASSWORD))
        self.stdout.write(
            f"  Districts {District.objects.count()}  Subcounties {Subcounty.objects.count()}  "
            f"Parishes {Parish.objects.count()}  Villages {Village.objects.count()}")
        self.stdout.write(
            f"  Crops {Crop.objects.count()}  Market prices {MarketPrice.objects.count()}  "
            f"Lots {Lot.objects.count()}  Bids {Bid.objects.count()}  "
            f"Declarations {Declaration.objects.count()}")
        self.stdout.write(
            f"  Posts {Post.objects.count()}  Comments {Comment.objects.count()}  "
            f"Advisory requests {AdvisoryRequest.objects.count()}")
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
