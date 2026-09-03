from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.farmers.models import Crop, Farmer, Season
from apps.geo.models import District, Parish, Subcounty, Village
from apps.market.models import Bid, Buyer, Declaration, Grade, Lot
from apps.market.services import declare, maybe_close_lot, record_grading


@pytest.fixture
def data(db):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    parish = Parish.objects.create(subcounty=subcounty, name="Katosi", lot_min_bags=10)
    village = Village.objects.create(parish=parish, name="Kigunga")
    user = SystemUser.objects.create_user(
        phone="+256700000070", password="pin", full_name="Agent",
        role=Role.AGENT, scope_level=ScopeLevel.PARISH, scope_id=parish.id)
    farmer = Farmer.objects.create(village=village, full_name="Grace Nabirye", sex="F", registered_by=user)
    crop = Crop.objects.create(name="Maize")
    season = Season.objects.create(
        year=timezone.localdate().year, season_no=1,
        start_date=timezone.localdate().replace(month=1, day=1),
        end_date=timezone.localdate().replace(month=12, day=31))
    lot = Lot.objects.create(parish=parish, season=season, crop=crop, min_bags=10)
    return {"parish": parish, "user": user, "farmer": farmer, "crop": crop, "season": season, "lot": lot}


@pytest.mark.django_db
def test_declare_publishes_declaration_created(data, django_capture_on_commit_callbacks):
    with (
        patch("apps.market.services.events.publish") as mock_publish,
        django_capture_on_commit_callbacks(execute=True),
    ):
        d = declare(farmer=data["farmer"], crop=data["crop"], bags=3, moisture=None,
                    actor=data["user"], via="agent")
    mock_publish.assert_called_once_with(
        f"parish.{data['parish'].id}", "declaration.created",
        {"lot_id": d.lot_id, "declaration_id": d.id, "bags": 3, "grade": "ungraded",
         "lot_bags": 3, "lot_min_bags": 10})


@pytest.mark.django_db
def test_record_grading_publishes_declaration_graded_with_pct_grade1(data, django_capture_on_commit_callbacks):
    declaration = Declaration.objects.create(
        farmer=data["farmer"], lot=data["lot"], bags=6, grade=Grade.UNGRADED, declared_via="web")
    with (
        patch("apps.market.services.events.publish") as mock_publish,
        django_capture_on_commit_callbacks(execute=True),
    ):
        record_grading(declaration_id=declaration.id, moisture="12.5", actor=data["user"])
    mock_publish.assert_called_once_with(
        f"parish.{data['parish'].id}", "declaration.graded",
        {"declaration_id": declaration.id, "grade": "grade_1", "moisture_pct": "12.5", "pct_grade1": 100})


@pytest.mark.django_db
def test_lot_close_publishes_lot_closed_with_bags_and_bid_count(data, django_capture_on_commit_callbacks):
    Declaration.objects.create(farmer=data["farmer"], lot=data["lot"], bags=10, grade=Grade.G1, declared_via="web")
    buyer = Buyer.objects.create(name="Buyer Co", licence_no="LIC-9", user=SystemUser.objects.create_user(
        phone="+256700000071", full_name="Buyer", role=Role.BUYER, scope_level=ScopeLevel.NATIONAL))
    Bid.objects.create(lot=data["lot"], buyer=buyer, price_per_kg=1200, terms="cash")

    with (
        patch("apps.market.services.events.publish") as mock_publish,
        django_capture_on_commit_callbacks(execute=True),
    ):
        maybe_close_lot(data["lot"])
    # Closing also seals bids for disclosure and triggers the metrics
    # rollup (parish -> district -> national), each publishing its own event.
    mock_publish.assert_any_call(
        f"parish.{data['parish'].id}", "lot.closed",
        {"lot_id": data["lot"].id, "bags": 10, "bid_count": 1})
    mock_publish.assert_any_call(
        f"parish.{data['parish'].id}", "bid.disclosed",
        {"lot_id": data["lot"].id, "bids": [{"buyer_name": "Buyer Co", "price_per_kg": 1200, "terms": "cash"}]})
