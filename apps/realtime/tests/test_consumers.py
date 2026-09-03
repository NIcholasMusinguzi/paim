import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser

from apps.accounts.models import Role, ScopeLevel, SystemUser
from apps.geo.models import District, Parish, Subcounty
from apps.realtime.consumers import ParishConsumer


@pytest.fixture
def parish(db):
    district = District.objects.create(name="Mukono")
    subcounty = Subcounty.objects.create(district=district, name="Kyampisi")
    return Parish.objects.create(subcounty=subcounty, name="Katosi", lot_min_bags=10)


async def _connect(parish_id, user):
    communicator = WebsocketCommunicator(ParishConsumer.as_asgi(), f"/ws/parish/{parish_id}/")
    communicator.scope["url_route"] = {"kwargs": {"parish_id": str(parish_id)}}
    communicator.scope["user"] = user
    connected, _subprotocol = await communicator.connect()
    return communicator, connected


@pytest.mark.django_db(transaction=True)
async def test_anonymous_is_refused_with_4401(parish):
    communicator, connected = await _connect(parish.id, AnonymousUser())
    assert connected is False
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_out_of_scope_user_is_refused_with_4403(parish):
    from asgiref.sync import sync_to_async

    other_district = await sync_to_async(District.objects.create)(name="Wakiso")
    other_subcounty = await sync_to_async(Subcounty.objects.create)(district=other_district, name="Nabweru")
    other_parish = await sync_to_async(Parish.objects.create)(subcounty=other_subcounty, name="Elsewhere")
    user = await sync_to_async(SystemUser.objects.create_user)(
        phone="+256700000020", full_name="Chief", role=Role.PARISH_CHIEF,
        scope_level=ScopeLevel.PARISH, scope_id=other_parish.id,
    )
    communicator, connected = await _connect(parish.id, user)
    assert connected is False
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_scoped_user_connects_and_receives_hello(parish):
    from asgiref.sync import sync_to_async

    user = await sync_to_async(SystemUser.objects.create_user)(
        phone="+256700000021", full_name="Chief", role=Role.PARISH_CHIEF,
        scope_level=ScopeLevel.PARISH, scope_id=parish.id,
    )
    communicator, connected = await _connect(parish.id, user)
    assert connected is True
    hello = await communicator.receive_json_from()
    assert hello["type"] == "hello"
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_declaration_created_flows_from_service_to_a_live_socket(parish):
    """This is the milestone from IMPLEMENTATION_REACT.md section 15, sprint
    4: a declaration made through the domain service must reach a connected
    parish socket with no polling — the whole pipeline, not a mock."""
    from datetime import timedelta

    from asgiref.sync import sync_to_async
    from django.utils import timezone

    from apps.farmers.models import Crop, Farmer, Season
    from apps.geo.models import Village
    from apps.market.services import declare

    def setup():
        village = Village.objects.create(parish=parish, name="Kigunga")
        crop = Crop.objects.create(name="Maize")
        today = timezone.localdate()
        Season.objects.create(
            year=today.year, season_no=1,
            start_date=today - timedelta(days=5), end_date=today + timedelta(days=100))
        chief = SystemUser.objects.create_user(
            phone="+256700000022", full_name="Chief", role=Role.PARISH_CHIEF,
            scope_level=ScopeLevel.PARISH, scope_id=parish.id)
        farmer = Farmer.objects.create(village=village, full_name="Grace Nabirye", sex="F", registered_by=chief)
        return crop, farmer, chief

    crop, farmer, chief = await sync_to_async(setup)()

    communicator, connected = await _connect(parish.id, chief)
    assert connected is True
    await communicator.receive_json_from()  # hello

    declaration = await sync_to_async(declare)(
        farmer=farmer, crop=crop, bags=3, moisture=None, actor=chief, via="agent")

    event = await communicator.receive_json_from(timeout=2)
    assert event == {
        "type": "declaration.created", "at": event["at"],
        "lot_id": declaration.lot_id, "declaration_id": declaration.id,
        "bags": 3, "grade": "ungraded", "lot_bags": 3, "lot_min_bags": parish.lot_min_bags,
    }
    await communicator.disconnect()
