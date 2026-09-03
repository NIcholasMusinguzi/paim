from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.analytics.models import DistrictSeasonMetric, NationalSeasonMetric
from apps.analytics.services import rollup_district, rollup_national, weighted
from apps.farmers.models import Crop, Farmer, Season
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import Bid, Buyer, Declaration, Grade, Lot
from apps.market.services import award_lot, maybe_close_lot


class Row:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_weighted_is_volume_weighted_not_a_mean_of_means():
    rows = [Row(pct_grade1=100, bags_declared=90), Row(pct_grade1=0, bags_declared=10)]
    assert weighted(rows, "pct_grade1") == 90


def test_weighted_excludes_rows_with_no_value_from_both_numerator_and_weight():
    rows = [Row(avg_price_per_kg=None, bags_declared=100), Row(avg_price_per_kg=1200, bags_declared=10)]
    assert weighted(rows, "avg_price_per_kg") == 1200


def test_weighted_returns_none_when_no_row_has_a_value():
    rows = [Row(avg_price_per_kg=None, bags_declared=100)]
    assert weighted(rows, "avg_price_per_kg") is None


@pytest.fixture
def two_districts(db):
    crop = Crop.objects.create(name="Maize")
    today = timezone.localdate()
    season = Season.objects.create(
        year=today.year, season_no=1,
        start_date=today - timedelta(days=10), end_date=today + timedelta(days=100))

    def make_parish(district_name, subcounty_name, parish_name, min_bags):
        district = District.objects.create(name=district_name)
        subcounty = Subcounty.objects.create(district=district, name=subcounty_name)
        return Parish.objects.create(subcounty=subcounty, name=parish_name, lot_min_bags=min_bags)

    parish_a = make_parish("Mukono", "Kyampisi", "Katosi", 5)
    parish_b = make_parish("Wakiso", "Nabweru", "Elsewhere", 5)
    village_a = Village.objects.create(parish=parish_a, name="Kigunga")
    village_b = Village.objects.create(parish=parish_b, name="Kasangati")
    chief = SystemUser.objects.create_user(
        phone="+256700000080", full_name="Chief", role=Role.PARISH_CHIEF,
        scope_level=ScopeLevel.PARISH, scope_id=parish_a.id)
    farmer_a = Farmer.objects.create(village=village_a, full_name="Farmer A", sex="F", registered_by=chief)
    farmer_b = Farmer.objects.create(village=village_b, full_name="Farmer B", sex="F", registered_by=chief)
    return {"crop": crop, "season": season, "parish_a": parish_a, "parish_b": parish_b,
            "farmer_a": farmer_a, "farmer_b": farmer_b, "chief": chief}


@pytest.mark.django_db
def test_district_rollup_has_no_price_until_a_lot_is_awarded(two_districts, django_capture_on_commit_callbacks):
    lot = Lot.objects.create(
        parish=two_districts["parish_a"], season=two_districts["season"], crop=two_districts["crop"], min_bags=5)
    Declaration.objects.create(farmer=two_districts["farmer_a"], lot=lot, bags=5, grade=Grade.G1, declared_via="web")
    with django_capture_on_commit_callbacks(execute=True):
        maybe_close_lot(lot)

    district_row = DistrictSeasonMetric.objects.get(
        district=two_districts["parish_a"].subcounty.district, season=two_districts["season"], crop=two_districts["crop"])
    assert district_row.bags_declared == 5
    assert district_row.avg_price_per_kg is None


@pytest.mark.django_db
def test_national_ranking_orders_districts_by_price_after_award(two_districts, django_capture_on_commit_callbacks):
    lot_a = Lot.objects.create(
        parish=two_districts["parish_a"], season=two_districts["season"], crop=two_districts["crop"], min_bags=5)
    Declaration.objects.create(farmer=two_districts["farmer_a"], lot=lot_a, bags=5, grade=Grade.G1, declared_via="web")
    lot_b = Lot.objects.create(
        parish=two_districts["parish_b"], season=two_districts["season"], crop=two_districts["crop"], min_bags=5)
    Declaration.objects.create(farmer=two_districts["farmer_b"], lot=lot_b, bags=5, grade=Grade.G1, declared_via="web")

    buyer_user = SystemUser.objects.create_user(
        phone="+256700000081", full_name="Buyer", role=Role.BUYER, scope_level=ScopeLevel.NATIONAL)
    buyer = Buyer.objects.create(name="Buyer Co", licence_no="LIC-ROLLUP", user=buyer_user)

    with django_capture_on_commit_callbacks(execute=True):
        maybe_close_lot(lot_a)
        maybe_close_lot(lot_b)
        bid_a = Bid.objects.create(lot=lot_a, buyer=buyer, price_per_kg=1000, terms="cash")
        bid_b = Bid.objects.create(lot=lot_b, buyer=buyer, price_per_kg=2000, terms="cash")
        award_lot(lot_id=lot_a.id, bid_id=bid_a.id, actor=two_districts["chief"], minute_ref="MIN-A")
        award_lot(lot_id=lot_b.id, bid_id=bid_b.id, actor=two_districts["chief"], minute_ref="MIN-B")

    national = NationalSeasonMetric.objects.get(season=two_districts["season"], crop=two_districts["crop"])
    assert national.districts_reporting == 2
    assert national.avg_price_per_kg == 1500  # 5 bags at 1000 + 5 bags at 2000, weighted

    ranked = list(DistrictSeasonMetric.objects.filter(
        season=two_districts["season"], crop=two_districts["crop"]).order_by("rank_national"))
    assert [r.district.name for r in ranked] == ["Wakiso", "Mukono"]
    assert [r.rank_national for r in ranked] == [1, 2]


@pytest.mark.django_db
def test_rollup_district_and_national_are_idempotent(two_districts):
    lot = Lot.objects.create(
        parish=two_districts["parish_a"], season=two_districts["season"], crop=two_districts["crop"], min_bags=5)
    Declaration.objects.create(farmer=two_districts["farmer_a"], lot=lot, bags=5, grade=Grade.G1, declared_via="web")
    maybe_close_lot(lot)

    rollup_district(district_id=two_districts["parish_a"].subcounty.district_id,
                    season_id=two_districts["season"].id, crop_id=two_districts["crop"].id)
    rollup_national(season_id=two_districts["season"].id, crop_id=two_districts["crop"].id)

    assert DistrictSeasonMetric.objects.count() == 1
    assert NationalSeasonMetric.objects.count() == 1
