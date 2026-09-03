# PAIM — Implementation Specification

**Parish Agricultural Information and Market Linkage**
Phase 1 (web release). Target: a single Django application serving farmer, agent, officer, national administrator and buyer roles, with the service layer written channel-blind so the Phase 2 USSD/IVR adapters attach without touching business logic.

This document is the build contract. Anything in it marked **MUST** is a correctness requirement, not a preference.

---

## 1. Scope of this build

| In scope (P1) | Out of scope (later phase) |
|---|---|
| F1–F14, F19–F24 from the design report | F15–F17 USSD, IVR, SMS self-service menus |
| Web UI for 5 roles, responsive to 360 px | F18 NIRA / PDMIS / UNMA / AFAAS integrations |
| Offline-capable agent PWA | On-device AI pest diagnosis |
| Outbound SMS notification (one-way) | Warehouse receipt and SACCO credit |
| Parish → district → national rollup and trend engine | Mobile money settlement (stub the interface, log intent) |

**Non-negotiable architectural rule.** No business rule may live in a view, template, serializer or JS file. Views validate input and call a service function in `services.py`. Phase 2 adds a USSD view that calls the same service functions. If a rule cannot be exercised from a plain Python call with no HTTP request, it is in the wrong place.

---

## 2. Stack

| Concern | Choice | Version |
|---|---|---|
| Language | Python | 3.12 |
| Framework | Django | 5.0 LTS |
| API | Django REST Framework | 3.15 |
| Database | PostgreSQL | 16 |
| Cache / broker | Redis | 7 |
| Async tasks | Celery + django-celery-beat | 5.4 |
| Templates | Django templates + htmx 1.9 | server-rendered |
| Offline client | Service worker + IndexedDB (idb 8) | vanilla JS |
| Auth | Django auth, phone + PIN for field roles | — |
| SMS | Africa's Talking (adapter pattern) | — |
| Testing | pytest, pytest-django, factory_boy, Playwright | — |
| Lint / format | ruff, black, djlint | — |
| Deployment | gunicorn + nginx, Docker Compose | — |

**Why server-rendered templates and htmx rather than a SPA.** N1 requires first contentful paint under 5 s on a simulated 2G link and N2 caps the farmer view at 150 KB compressed. A React bundle costs 40–130 KB gzipped before any application code. htmx is 14 KB and gives partial updates where they are needed (declaration confirmation, lot progress, grading result). The agent PWA is the only client with real offline state, and it uses vanilla JS with IndexedDB rather than a framework.

---

## 3. Repository layout

```
paim/
├── manage.py
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   ├── celery.py
│   └── asgi.py  wsgi.py
├── apps/
│   ├── accounts/        # SystemUser, roles, scoping, auth
│   ├── geo/             # District, Subcounty, Parish, Village
│   ├── farmers/         # Farmer, Plot, Planting, Crop, Season
│   ├── advisory/        # AdvisoryContent, AdvisoryDelivery, WeatherAdvisory, PestReport
│   ├── market/          # Lot, Declaration, Bid, Buyer, Settlement, PriceObservation, Market
│   ├── consent/         # Organisation, Consent, AccessLog + enforcement
│   ├── analytics/       # ParishSeasonMetric, DistrictSeasonMetric, NationalSeasonMetric, TrendInsight
│   └── notify/          # Notification, channel adapters (SMS now, USSD/IVR later)
├── templates/
│   ├── base.html
│   ├── farmer/  agent/  officer/  national/  buyer/
│   └── partials/        # htmx fragments
├── static/
│   ├── css/paim.css     # design tokens + components (see mockups)
│   ├── js/agent-sw.js   # service worker
│   └── js/agent-sync.js # IndexedDB queue + sync
├── fixtures/
│   ├── geo_mukono.json
│   ├── crops_seasons.json
│   └── advisory_maize_beans_cassava.json
└── tests/
    ├── unit/  integration/  e2e/
```

**Every app MUST contain** `models.py`, `services.py`, `selectors.py`, `views.py`, `urls.py`, `admin.py`, `tests/`. `services.py` writes; `selectors.py` reads. Views import from those two only.

---

## 4. Environment and local setup

`.env.example`:

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.dev
SECRET_KEY=change-me
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://paim:paim@localhost:5432/paim
REDIS_URL=redis://localhost:6379/0
SMS_PROVIDER=console            # console | africastalking
AT_USERNAME=
AT_API_KEY=
AT_SENDER_ID=PAIM
DEFAULT_LOT_MIN_BAGS=800
GRADE1_MAX_MOISTURE=13.0
GRADE2_MAX_MOISTURE=15.0
BUYER_COMMISSION_PCT=1.5
METRICS_RECOMPUTE_CRON=0 2 * * *
```

Bring-up:

```bash
cp .env.example .env
docker compose up -d db redis
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python manage.py migrate
python manage.py loaddata fixtures/geo_mukono.json fixtures/crops_seasons.json fixtures/advisory_maize_beans_cassava.json
python manage.py createsuperuser
python manage.py seed_demo --district Mukono --parish Kyampisi --farmers 40   # management command, section 15
python manage.py runserver
celery -A config worker -l info &
celery -A config beat -l info &
```

---

## 5. Data model

Models map one-to-one onto the ERDs in the design report. Abbreviated field definitions; all models inherit `TimeStampedModel` (`created_at`, `updated_at`).

### 5.1 `apps/geo/models.py`

```python
class District(models.Model):
    name = models.CharField(max_length=64, unique=True)
    region = models.CharField(max_length=32, choices=Region.choices)

class Subcounty(models.Model):
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="subcounties")
    name = models.CharField(max_length=64)
    class Meta:
        unique_together = [("district", "name")]

class Parish(models.Model):
    subcounty = models.ForeignKey(Subcounty, on_delete=models.PROTECT, related_name="parishes")
    name = models.CharField(max_length=64)
    agro_zone = models.CharField(max_length=32, choices=AgroZone.choices)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    lot_min_bags = models.PositiveIntegerField(default=800)

    @property
    def district(self):        # traversal, never stored
        return self.subcounty.district

class Village(models.Model):
    parish = models.ForeignKey(Parish, on_delete=models.PROTECT, related_name="villages")
    name = models.CharField(max_length=64)
```

**MUST NOT** denormalise `district_id` onto `Farmer` or any metric row other than the aggregate tables in `analytics`. A single traversal path is what guarantees that two dashboards cannot disagree.

### 5.2 `apps/accounts/models.py`

```python
class Role(models.TextChoices):
    NATIONAL_ADMIN = "national_admin"
    DISTRICT_OFFICER = "district_officer"
    SUBCOUNTY_OFFICER = "subcounty_officer"
    PARISH_CHIEF = "parish_chief"
    AGENT = "agent"
    BUYER = "buyer"
    FARMER = "farmer"

class ScopeLevel(models.TextChoices):
    NATIONAL = "national"; DISTRICT = "district"
    SUBCOUNTY = "subcounty"; PARISH = "parish"

class SystemUser(AbstractBaseUser, PermissionsMixin):
    phone = PhoneField(unique=True)                 # E.164, +256...
    full_name = models.CharField(max_length=120)
    role = models.CharField(max_length=24, choices=Role.choices)
    scope_level = models.CharField(max_length=16, choices=ScopeLevel.choices)
    scope_id = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    USERNAME_FIELD = "phone"
```

`scope_id` references the row at `scope_level`. It is a soft reference by design so one column serves four tables; integrity is enforced in `accounts.services.validate_scope()` and in a `CheckConstraint` that `scope_id IS NOT NULL` unless `scope_level = 'national'`.

### 5.3 `apps/farmers/models.py`

```python
class Crop(models.Model):
    name = models.CharField(max_length=48, unique=True)
    cycle_weeks = models.PositiveSmallIntegerField()

class Season(models.Model):
    year = models.PositiveSmallIntegerField()
    season_no = models.PositiveSmallIntegerField(choices=[(1, "A"), (2, "B")])
    start_date = models.DateField(); end_date = models.DateField()
    class Meta:
        unique_together = [("year", "season_no")]

class Farmer(models.Model):
    village = models.ForeignKey("geo.Village", on_delete=models.PROTECT, related_name="farmers")
    full_name = models.CharField(max_length=120)
    sex = models.CharField(max_length=1, choices=[("F", "Female"), ("M", "Male")])
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    phone = PhoneField(null=True, blank=True, db_index=True)
    language = models.CharField(max_length=16, choices=Language.choices, default=Language.LUGANDA)
    reach_channel = models.CharField(max_length=16, choices=ReachChannel.choices)  # web|agent|sms
    nin_hash = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    nin_consent = models.BooleanField(default=False)
    registered_by = models.ForeignKey("accounts.SystemUser", on_delete=models.PROTECT)

class Plot(models.Model):
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name="plots")
    area_acres = models.DecimalField(max_digits=5, decimal_places=2)
    gps_point = models.CharField(max_length=64, null=True, blank=True)

class Planting(models.Model):
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="plantings")
    season = models.ForeignKey(Season, on_delete=models.PROTECT)
    crop = models.ForeignKey(Crop, on_delete=models.PROTECT)
    planting_date = models.DateField()
    variety = models.CharField(max_length=64, blank=True)
    class Meta:
        unique_together = [("plot", "season", "crop")]
```

**NIN storage rule (MUST).** The raw National Identification Number is never stored. `nin_hash = sha256(nin + settings.NIN_PEPPER)`, written only when `nin_consent` is true, and the pepper lives in the secret store, not in the database. Verification against NIRA in Phase 2 compares hashes.

### 5.4 `apps/market/models.py`

```python
class LotStatus(models.TextChoices):
    OPEN = "open"; CLOSED = "closed"; AWARDED = "awarded"; SETTLED = "settled"; CANCELLED = "cancelled"

class Lot(models.Model):
    parish = models.ForeignKey("geo.Parish", on_delete=models.PROTECT, related_name="lots")
    season = models.ForeignKey("farmers.Season", on_delete=models.PROTECT)
    crop = models.ForeignKey("farmers.Crop", on_delete=models.PROTECT)
    min_bags = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=LotStatus.choices, default=LotStatus.OPEN)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    awarded_bid = models.OneToOneField("Bid", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["parish", "season", "crop"],
            condition=Q(status__in=["open", "closed", "awarded"]),
            name="one_active_lot_per_parish_season_crop")]

class Grade(models.TextChoices):
    G1 = "grade_1"; G2 = "grade_2"; UNGRADED = "ungraded"; REJECT = "reject"

class Declaration(models.Model):
    farmer = models.ForeignKey("farmers.Farmer", on_delete=models.PROTECT, related_name="declarations")
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name="declarations")
    bags = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(200)])
    moisture_pct = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    grade = models.CharField(max_length=10, choices=Grade.choices, default=Grade.UNGRADED)
    graded_by = models.ForeignKey("accounts.SystemUser", null=True, blank=True, on_delete=models.PROTECT)
    graded_at = models.DateTimeField(null=True, blank=True)
    declared_via = models.CharField(max_length=16, choices=ReachChannel.choices)

class Buyer(models.Model):
    name = models.CharField(max_length=120)
    licence_no = models.CharField(max_length=48, unique=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey("accounts.SystemUser", null=True, on_delete=models.PROTECT)
    user = models.OneToOneField("accounts.SystemUser", on_delete=models.PROTECT, related_name="buyer_profile")

class Bid(models.Model):
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name="bids")
    buyer = models.ForeignKey(Buyer, on_delete=models.PROTECT)
    price_per_kg = models.PositiveIntegerField()       # UGX, integer
    terms = models.CharField(max_length=160)
    submitted_at = models.DateTimeField(auto_now_add=True)
    sealed_until = models.DateTimeField(null=True, blank=True)
    class Meta:
        unique_together = [("lot", "buyer")]           # one live bid per buyer per lot

class Settlement(models.Model):
    declaration = models.OneToOneField(Declaration, on_delete=models.PROTECT)
    bid = models.ForeignKey(Bid, on_delete=models.PROTECT)
    gross_amount = models.PositiveIntegerField()
    commission = models.PositiveIntegerField()
    net_amount = models.PositiveIntegerField()
    mm_reference = models.CharField(max_length=64, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
```

`Bid.price_per_kg` is an integer in UGX. **MUST NOT** use float anywhere in money or moisture arithmetic; use `int` for currency and `Decimal` for moisture.

### 5.5 `apps/consent/models.py`

```python
class Organisation(models.Model):
    name = models.CharField(max_length=120)
    org_type = models.CharField(max_length=24, choices=OrgType.choices)  # sacco|mfi|insurer|govt|platform
    accredited_at = models.DateTimeField(null=True, blank=True)

class Consent(models.Model):
    farmer = models.ForeignKey("farmers.Farmer", on_delete=models.CASCADE, related_name="consents")
    organisation = models.ForeignKey(Organisation, on_delete=models.PROTECT)
    purpose = models.CharField(max_length=64, choices=Purpose.choices)
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    channel = models.CharField(max_length=16, choices=ReachChannel.choices)

    @property
    def is_active(self):
        return self.revoked_at is None

class AccessLog(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.PROTECT)
    farmer = models.ForeignKey("farmers.Farmer", on_delete=models.PROTECT)
    consent = models.ForeignKey(Consent, null=True, blank=True, on_delete=models.SET_NULL)
    purpose = models.CharField(max_length=64)
    outcome = models.CharField(max_length=12, choices=[("allowed", "Allowed"), ("refused", "Refused")])
    requested_at = models.DateTimeField(auto_now_add=True)
    actor = models.CharField(max_length=120)
```

**AccessLog is append-only (MUST).** No `update()` or `delete()` anywhere in the codebase; enforce with a database trigger and a `pre_save` guard that raises on any instance with a primary key.

### 5.6 `apps/analytics/models.py`

```python
class ParishSeasonMetric(models.Model):
    parish = models.ForeignKey("geo.Parish", on_delete=models.CASCADE)
    season = models.ForeignKey("farmers.Season", on_delete=models.CASCADE)
    crop = models.ForeignKey("farmers.Crop", on_delete=models.CASCADE)
    farmers_registered = models.PositiveIntegerField(default=0)
    farmers_active = models.PositiveIntegerField(default=0)
    bags_declared = models.PositiveIntegerField(default=0)
    pct_grade1 = models.PositiveSmallIntegerField(default=0)
    avg_price_per_kg = models.PositiveIntegerField(null=True)
    est_loss_pct = models.PositiveSmallIntegerField(null=True)
    agent_reach_pct = models.PositiveSmallIntegerField(default=0)
    computed_at = models.DateTimeField()
    class Meta:
        unique_together = [("parish", "season", "crop")]
        indexes = [models.Index(fields=["season", "crop", "-avg_price_per_kg"])]

# DistrictSeasonMetric and NationalSeasonMetric mirror this, keyed on district/season/crop
# and season/crop respectively, plus parishes_reporting / districts_reporting and rank_national.

class TrendInsight(models.Model):
    scope_level = models.CharField(max_length=16, choices=ScopeLevel.choices)
    scope_id = models.PositiveIntegerField(null=True)
    crop = models.ForeignKey("farmers.Crop", on_delete=models.PROTECT)
    metric = models.CharField(max_length=48)
    direction = models.CharField(max_length=8, choices=[("up", "Up"), ("down", "Down"), ("flat", "Flat")])
    magnitude = models.DecimalField(max_digits=6, decimal_places=2)
    window_weeks = models.PositiveSmallIntegerField()
    message = models.TextField(max_length=600)
    approved_by = models.ForeignKey("accounts.SystemUser", null=True, blank=True, on_delete=models.PROTECT)
    published_at = models.DateTimeField(null=True, blank=True)
```

### 5.7 `apps/advisory/models.py`

```python
class AdvisoryContent(models.Model):
    crop = models.ForeignKey("farmers.Crop", on_delete=models.PROTECT)
    agro_zone = models.CharField(max_length=32, choices=AgroZone.choices, blank=True)  # blank = all zones
    week_from = models.PositiveSmallIntegerField()
    week_to = models.PositiveSmallIntegerField()
    language = models.CharField(max_length=16, choices=Language.choices)
    body = models.TextField(max_length=480)
    source = models.CharField(max_length=64)                 # "MAAIF and NARO"
    validated_by = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=12, choices=[("draft", "Draft"), ("validated", "Validated"), ("retired", "Retired")])
    class Meta:
        constraints = [models.CheckConstraint(check=Q(week_to__gte=F("week_from")), name="week_range_valid")]

class AdvisoryDelivery(models.Model):
    content = models.ForeignKey(AdvisoryContent, on_delete=models.PROTECT)
    farmer = models.ForeignKey("farmers.Farmer", on_delete=models.CASCADE, related_name="deliveries")
    trend = models.ForeignKey("analytics.TrendInsight", null=True, blank=True, on_delete=models.SET_NULL)
    channel = models.CharField(max_length=16, choices=ReachChannel.choices)
    sent_at = models.DateTimeField(auto_now_add=True)
    acted_on_reported = models.BooleanField(null=True)
```

**Only `status='validated'` content may be delivered (MUST).** Enforce in the selector, not in the view.

---

## 6. Role and permission matrix

| Capability | Farmer | Agent | Parish chief | Sub-county officer | District officer | National admin | Buyer |
|---|---|---|---|---|---|---|---|
| View own records | ✓ | — | — | — | — | — | — |
| Register farmer | self | ✓ | ✓ | ✓ | — | — | — |
| Declare harvest | own | on behalf | — | — | — | — | — |
| Record grading | — | ✓ | ✓ | — | — | — | — |
| Answer pest report | — | — | — | ✓ | ✓ | — | — |
| View parish dashboard | — | own parish | own parish | own subcounty | own district | all | — |
| Close / award lot | — | — | ✓ (records committee decision) | ✓ | — | — | — |
| Submit bid | — | — | — | — | — | — | ✓ |
| View bids before closure | — | — | — | — | — | — | own only |
| Approve trend insight | — | — | — | — | ✓ | ✓ | — |
| Export bulk data | — | — | — | — | dual auth | dual auth | — |

Implement as a single scoping mixin:

```python
# apps/accounts/scoping.py
def parish_ids_for(user) -> QuerySet[int]:
    if user.role == Role.NATIONAL_ADMIN:
        return Parish.objects.values_list("id", flat=True)
    if user.scope_level == ScopeLevel.DISTRICT:
        return Parish.objects.filter(subcounty__district_id=user.scope_id).values_list("id", flat=True)
    if user.scope_level == ScopeLevel.SUBCOUNTY:
        return Parish.objects.filter(subcounty_id=user.scope_id).values_list("id", flat=True)
    if user.scope_level == ScopeLevel.PARISH:
        return Parish.objects.filter(id=user.scope_id).values_list("id", flat=True)
    return Parish.objects.none()

class ScopedQuerysetMixin:
    parish_path = "parish_id"          # override per view, e.g. "lot__parish_id"
    def get_queryset(self):
        return super().get_queryset().filter(**{f"{self.parish_path}__in": parish_ids_for(self.request.user)})
```

Every list and detail view for officer/admin data **MUST** use this mixin. A view that filters by scope inline is a defect.

---

## 7. Core services

### 7.1 Advisory selection — `apps/advisory/selectors.py`

The single most important rule in the system: advice is chosen by the farmer's own crop week, never by a calendar broadcast.

```python
def crop_week(planting: Planting, on: date | None = None) -> int:
    """Whole weeks elapsed since this farmer planted. Week 0 is planting week."""
    on = on or timezone.localdate()
    return max(0, (on - planting.planting_date).days // 7)

def advice_for(farmer: Farmer, on: date | None = None) -> list[AdvisoryContent]:
    plantings = (Planting.objects
                 .filter(plot__farmer=farmer, season=current_season(on))
                 .select_related("crop", "plot__farmer__village__parish"))
    zone = farmer.village.parish.agro_zone
    out = []
    for p in plantings:
        wk = crop_week(p, on)
        qs = (AdvisoryContent.objects
              .filter(crop=p.crop, status="validated", language=farmer.language,
                      week_from__lte=wk, week_to__gte=wk)
              .filter(Q(agro_zone=zone) | Q(agro_zone=""))
              .order_by("-agro_zone"))          # zone-specific beats generic
        if not qs.exists():                      # language fallback, never silence
            qs = qs.model.objects.filter(crop=p.crop, status="validated",
                                         language=Language.ENGLISH,
                                         week_from__lte=wk, week_to__gte=wk)
        out.extend(qs[:2])
    return out
```

Rules:
- If two content rows match, the zone-specific one wins over the generic one.
- If no content exists in the farmer's language, fall back to English rather than returning nothing, and record the fallback on the delivery so content gaps are visible in reporting.
- Delivery is recorded on every send (`AdvisoryDelivery`), including web views. Without it the evaluation cannot separate "ignored the advice" from "never received it".

### 7.2 Grading — `apps/market/services.py`

```python
def grade_for(moisture: Decimal) -> str:
    if moisture <= settings.GRADE1_MAX_MOISTURE:  return Grade.G1
    if moisture <= settings.GRADE2_MAX_MOISTURE:  return Grade.G2
    return Grade.REJECT

@transaction.atomic
def record_grading(*, declaration_id: int, moisture: Decimal, actor: SystemUser) -> Declaration:
    d = Declaration.objects.select_for_update().get(pk=declaration_id)
    if d.lot.status != LotStatus.OPEN:
        raise DomainError("Cannot grade a declaration once the lot has closed.")
    d.moisture_pct = moisture
    d.grade = grade_for(moisture)
    d.graded_by, d.graded_at = actor, timezone.now()
    d.save(update_fields=["moisture_pct", "grade", "graded_by", "graded_at", "updated_at"])
    notify.farmer(d.farmer, template="grading_result", ctx={"declaration": d})
    return d
```

A `reject` grade does not delete the declaration. It stays in the lot with `grade=reject` and is excluded from `bags_declared` in the metrics, so the parish can see how much produce failed and why.

### 7.3 Declaration and lot lifecycle

```
        declare()                close_lot()              award_lot()          settle()
OPEN ─────────────────► OPEN ──────────────────► CLOSED ──────────────► AWARDED ─────────► SETTLED
  │  (bags accumulate)   │ (auto at min_bags      │ (bids become        │ (committee       │
  │                      │  or manual by chief)   │  readable)          │  decision)       │
  └──────────────────────┴─────────── cancel_lot() ──────────────────► CANCELLED
```

```python
@transaction.atomic
def declare(*, farmer: Farmer, crop: Crop, bags: int, moisture: Decimal | None,
            actor: SystemUser, via: str) -> Declaration:
    if not 1 <= bags <= 200:
        raise DomainError("Bags must be between 1 and 200.")
    lot = get_or_open_lot(parish=farmer.village.parish, crop=crop, season=current_season())
    if lot.status != LotStatus.OPEN:
        raise DomainError("The lot for this parish has already closed.")
    d = Declaration.objects.create(
        farmer=farmer, lot=lot, bags=bags, moisture_pct=moisture,
        grade=grade_for(moisture) if moisture is not None else Grade.UNGRADED,
        declared_via=via)
    if d.grade == Grade.UNGRADED:
        tasks.queue_agent_grading_visit.delay(d.id)
    maybe_close_lot(lot)
    return d

@transaction.atomic
def maybe_close_lot(lot: Lot) -> Lot:
    lot = Lot.objects.select_for_update().get(pk=lot.pk)
    if lot.status != LotStatus.OPEN or sellable_bags(lot) < lot.min_bags:
        return lot
    lot.status, lot.closed_at = LotStatus.CLOSED, timezone.now()
    lot.save(update_fields=["status", "closed_at", "updated_at"])
    Bid.objects.filter(lot=lot).update(sealed_until=lot.closed_at)
    tasks.broadcast_bids_to_lot_farmers.delay(lot.id)     # F8: every farmer sees every bid
    tasks.recompute_parish_metric.delay(lot.parish_id, lot.season_id, lot.crop_id)
    return lot
```

**Bid sealing (MUST).** `Bid` rows are written on submission but are unreadable until closure. Enforce in the selector, not the template:

```python
def visible_bids(lot: Lot, viewer) -> QuerySet[Bid]:
    if lot.status in (LotStatus.CLOSED, LotStatus.AWARDED, LotStatus.SETTLED):
        return lot.bids.select_related("buyer").order_by("-price_per_kg")
    if getattr(viewer, "role", None) == Role.BUYER:
        return lot.bids.filter(buyer__user=viewer)        # a buyer may see only their own
    return Bid.objects.none()
```

Award records the committee's decision; it does not make it. The highest bid is shown as the default but any bid may be selected, and the selection stores who recorded it.

```python
@transaction.atomic
def award_lot(*, lot_id: int, bid_id: int, actor: SystemUser, minute_ref: str) -> Lot:
    lot = Lot.objects.select_for_update().get(pk=lot_id)
    if lot.status != LotStatus.CLOSED:
        raise DomainError("Only a closed lot can be awarded.")
    bid = lot.bids.get(pk=bid_id)
    lot.awarded_bid, lot.status = bid, LotStatus.AWARDED
    lot.save(update_fields=["awarded_bid", "status", "updated_at"])
    AwardRecord.objects.create(lot=lot, bid=bid, recorded_by=actor, committee_minute_ref=minute_ref)
    tasks.create_settlements.delay(lot.id)
    return lot
```

Settlement splits the awarded price across declarations by grade:

```python
GRADE_FACTOR = {Grade.G1: Decimal("1.00"), Grade.G2: Decimal("0.88"), Grade.REJECT: Decimal("0")}

def settlement_amounts(d: Declaration, bid: Bid) -> tuple[int, int, int]:
    kg = d.bags * 100
    gross = int(Decimal(bid.price_per_kg * kg) * GRADE_FACTOR[d.grade])
    commission = int(gross * Decimal(settings.BUYER_COMMISSION_PCT) / 100)   # borne by the buyer
    return gross, commission, gross                                          # farmer net == gross
```

The commission is added to the buyer's invoice, not deducted from the farmer. `net_amount == gross_amount` is an invariant with a test asserting it; if that ever changes, it is a policy decision requiring sign-off, not a code change.

### 7.4 Consent enforcement — `apps/consent/services.py`

Every external read of farmer data passes through one function. There is no other path.

```python
class ConsentRefused(PermissionDenied): pass

def read_farmer_data(*, farmer: Farmer, organisation: Organisation,
                     purpose: str, actor: str, fields: list[str]) -> dict:
    consent = (Consent.objects
               .filter(farmer=farmer, organisation=organisation, purpose=purpose, revoked_at__isnull=True)
               .first())
    AccessLog.objects.create(organisation=organisation, farmer=farmer, consent=consent,
                             purpose=purpose, actor=actor,
                             outcome="allowed" if consent else "refused")
    if not consent:
        raise ConsentRefused(f"No active consent for {organisation} / {purpose}.")
    return {f: PURPOSE_FIELDS[purpose][f](farmer) for f in fields if f in PURPOSE_FIELDS[purpose]}
```

`PURPOSE_FIELDS` is an explicit allowlist per purpose. A purpose can never return a field it does not declare, so adding a field to a model does not silently widen disclosure.

Revocation is immediate:

```python
def revoke(*, consent_id: int, farmer: Farmer) -> Consent:
    c = Consent.objects.get(pk=consent_id, farmer=farmer, revoked_at__isnull=True)
    c.revoked_at = timezone.now(); c.save(update_fields=["revoked_at"])
    cache.delete(f"consent:{farmer.id}:{c.organisation_id}:{c.purpose}")
    return c
```

### 7.5 Metrics rollup — `apps/analytics/services.py`

```python
@shared_task
def recompute_parish_metric(parish_id: int, season_id: int, crop_id: int) -> None:
    agg = (Declaration.objects
           .filter(lot__parish_id=parish_id, lot__season_id=season_id, lot__crop_id=crop_id)
           .exclude(grade=Grade.REJECT)
           .aggregate(bags=Coalesce(Sum("bags"), 0),
                      g1=Coalesce(Sum("bags", filter=Q(grade=Grade.G1)), 0),
                      actives=Count("farmer", distinct=True)))
    registered = Farmer.objects.filter(village__parish_id=parish_id).count()
    agent_reached = Farmer.objects.filter(village__parish_id=parish_id,
                                          reach_channel__in=["agent", "sms"]).count()
    awarded = Lot.objects.filter(parish_id=parish_id, season_id=season_id, crop_id=crop_id,
                                 status__in=[LotStatus.AWARDED, LotStatus.SETTLED]).first()
    ParishSeasonMetric.objects.update_or_create(
        parish_id=parish_id, season_id=season_id, crop_id=crop_id,
        defaults=dict(
            farmers_registered=registered,
            farmers_active=agg["actives"],
            bags_declared=agg["bags"],
            pct_grade1=pct(agg["g1"], agg["bags"]),
            avg_price_per_kg=awarded.awarded_bid.price_per_kg if awarded else None,
            est_loss_pct=estimated_loss_pct(parish_id, season_id, crop_id),
            agent_reach_pct=pct(agent_reached, registered),
            computed_at=timezone.now()))
    rollup_district.delay(Parish.objects.get(pk=parish_id).subcounty.district_id, season_id, crop_id)
```

District and national rollups are **volume-weighted, never a mean of means**:

```python
def weighted(rows, value_field, weight_field="bags_declared"):
    total = sum(getattr(r, weight_field) for r in rows) or 0
    if not total: return None
    return round(sum(getattr(r, value_field) * getattr(r, weight_field) for r in rows if getattr(r, value_field)) / total)
```

Schedule: `recompute_parish_metric` fires on lot closure, on award, and nightly at 02:00 for every active parish-season-crop; `rollup_district` and `rollup_national` chain from it. Dashboards read `*SeasonMetric` only and **MUST NOT** aggregate `Declaration` at request time.

### 7.6 Trend engine — `apps/analytics/trends.py`

```python
RULES = [
    PriceAfterPeakHarvest(min_seasons=3, min_pct=10),
    GradingPremiumGap(min_gap_pct=15),
    MoistureOutlier(z=1.5),
    ActiveUseDecline(min_drop_pp=10),
]

@shared_task
def generate_trend_insights(season_id: int) -> list[int]:
    drafts = []
    for rule in RULES:
        for scope_level, scope_id, crop_id, payload in rule.evaluate(season_id):
            drafts.append(TrendInsight.objects.create(
                scope_level=scope_level, scope_id=scope_id, crop_id=crop_id,
                metric=rule.metric, direction=payload["direction"],
                magnitude=payload["magnitude"], window_weeks=rule.window_weeks,
                message=rule.render(payload)).id)
    return drafts
```

**A TrendInsight is never delivered until approved (MUST).** `publish()` requires an approver whose role is district officer or national admin, sets `approved_by` and `published_at`, and enqueues `AdvisoryDelivery` rows for the farmers in scope. Publishing without an approver raises. There is no code path that sends an unapproved insight.

Every rule must state its sample size in the rendered message when parish coverage is below 60 per cent of registered farmers, because a trend drawn from a thin sample is a hypothesis, not a finding.

### 7.7 Notification — `apps/notify/`

```python
class Channel(Protocol):
    name: str
    def send(self, *, to: str, body: str, meta: dict) -> str: ...   # returns provider ref

class SMSChannel:  ...     # Africa's Talking
class ConsoleChannel: ...  # dev
# Phase 2: USSDPushChannel, IVRCallbackChannel — same Protocol, no service-layer change
```

Outbound is always queued, never synchronous, and rate-shaped to the gateway's throughput. Harvest-period pushes go out in batches with a token bucket; a district-wide advisory must not be dispatched in one burst.

---

## 8. HTTP surface

Server-rendered pages for humans; a small REST API for the agent PWA and, in Phase 2, for accredited systems.

### 8.1 Pages

| Path | Role | Purpose |
|---|---|---|
| `/` | any | Role-aware landing, redirects to the right home |
| `/sign-in` | any | Phone + PIN (field roles), phone + password (office roles) |
| `/farmer/` | farmer | Season summary, this week's advice, weather, prices |
| `/farmer/declare/` | farmer | Declare harvest, htmx-updated confirmation |
| `/farmer/consent/` | farmer | Grant, revoke, access history |
| `/farmer/trends/` | farmer | Published insights for the farmer's scope and crop |
| `/agent/` | agent | Today's queue, sync status |
| `/agent/register/` | agent | Four-step registration wizard |
| `/agent/grade/<declaration_id>/` | agent | Moisture entry and result |
| `/agent/pest/` | agent | Pest report with photo |
| `/parish/` | chief, officer | Parish dashboard |
| `/parish/lot/<id>/` | chief, officer | Lot detail, bids, award |
| `/national/` | district officer, national admin | District ranking, drill-down |
| `/national/trends/` | district officer, national admin | Insight queue and approval |
| `/buyer/` | buyer | Open lots |
| `/buyer/lot/<id>/bid/` | buyer | Submit sealed bid |

### 8.2 API (agent PWA and Phase 2)

| Method | Endpoint | Notes |
|---|---|---|
| `POST` | `/api/v1/auth/token/` | Phone + PIN, returns short-lived JWT + refresh |
| `GET` | `/api/v1/sync/bootstrap/?parish=<id>` | Farmers, crops, content, open lot for offline cache |
| `POST` | `/api/v1/sync/batch/` | Idempotent batch of queued offline operations |
| `GET/POST` | `/api/v1/farmers/` | Scoped list, create |
| `POST` | `/api/v1/declarations/` | Declare on behalf of a farmer |
| `POST` | `/api/v1/declarations/<id>/grade/` | Record moisture |
| `POST` | `/api/v1/pest-reports/` | Multipart with photo |
| `GET` | `/api/v1/metrics/parish/<id>/` | Scoped metrics |
| `POST` | `/api/v1/partner/farmer-data/` | Phase 2, consent-gated, always logged |

`POST /api/v1/sync/batch/` request:

```json
{ "device_id": "a3f2-...",
  "operations": [
    {"op_id":"c1b0-...","type":"farmer.create","at":"2026-08-14T09:12:03Z",
     "payload":{"full_name":"Nabirye Grace","village_id":41,"sex":"F","language":"lug",
                "reach_channel":"agent","crop_id":1,"planting_date":"2026-08-04",
                "area_acres":"2.0","nin_consent":false}},
    {"op_id":"c1b1-...","type":"declaration.grade","at":"2026-08-14T09:31:44Z",
     "payload":{"declaration_id":9182,"moisture_pct":"12.8"}}
  ]}
```

Response reports each operation independently so one failure does not block the batch:

```json
{"results":[{"op_id":"c1b0-...","status":"applied","farmer_id":5521},
            {"op_id":"c1b1-...","status":"rejected","reason":"lot_closed"}],
 "server_time":"2026-08-14T11:02:10Z"}
```

`op_id` is a client-generated UUID and is the idempotency key. Replaying a batch **MUST** be a no-op.

---

## 9. Offline agent client

**Cache on bootstrap:** the agent's parish roster, crop and season reference data, validated advisory content in the parish languages, and the open lot. Typical parish payload is 60–120 KB gzipped.

**Queue:** every write goes to an IndexedDB `outbox` store as `{op_id, type, payload, at, attempts, status}`. The UI reads optimistically from a local mirror so the agent sees their own work immediately.

**Sync:** background sync on connectivity, plus a manual "Sync now" control, because rural connectivity is intermittent enough that agents will want to force it when they reach a signal. Exponential backoff, capped at 6 attempts, then flagged for manual review in the UI.

**Conflict rules (fixed, not negotiable per case):**

| Situation | Resolution |
|---|---|
| Farmer created offline already exists (same name + village + phone) | Server returns the existing id; client merges, no duplicate |
| Grading arrives after lot closed | Rejected with `lot_closed`; agent sees it in a "needs attention" list |
| Two agents grade the same declaration | Last write wins by server receipt time; both attempts retained in an audit trail |
| Declaration arrives after lot closed | Rejected; farmer notified and rolled into the next lot if one is open |

**Device security.** The offline cache holds a whole parish's records. Encrypt the IndexedDB payload with a key derived from the agent's PIN, expire the session after 12 hours, and support remote revocation that wipes the cache on next contact.

---

## 10. Frontend implementation notes

Design tokens live in `static/css/paim.css` and mirror the mockup file exactly:

```css
:root{
  --page:#E7E9E3; --panel:#FAFBF7; --ink:#15181A; --soft:#586059; --rule:#C6CCC2;
  --sea:#26424D;      /* chrome, primary actions */
  --grain:#C08A2E;    /* lot progress, the one bold element */
  --leaf:#3D6B3A;     /* good state: grade 1, consent allowed */
  --murram:#9C3B1B;   /* attention: reject, revoked, below target */
}
```

Rules:
- Numeric columns use a monospace face and `font-variant-numeric: tabular-nums`. Bag counts and prices are compared down a column; proportional figures make that harder.
- Prices are shown per kilogram **and** per 100 kg bag everywhere a farmer sees them. Markets quote in kilograms, farmers transact in bags.
- Minimum touch target 44 × 44 px. Agents use this outdoors, standing, often one-handed.
- No web fonts. System font stack only, to hold the payload budget.
- Every destructive or consequential action states its consequence in the button label: "Stop it" and "Allow it", not "Submit".
- htmx partials return only the fragment that changed; full-page reloads on a declaration are a budget violation.

---

## 11. Testing

| Layer | Tool | Coverage requirement |
|---|---|---|
| Domain services | pytest | 90% on `services.py` across all apps |
| Selectors and scoping | pytest | Every role × every scoped view |
| API | pytest + DRF test client | Contract tests for all endpoints in 8.2 |
| Offline sync | pytest + Playwright | Batch idempotency, all four conflict rules |
| UI journeys | Playwright | The seven journeys in 11.1 |
| Load | k6 | Harvest peak profile, section 12 |

### 11.1 Journeys that MUST have an end-to-end test

1. Agent registers a farmer offline, syncs, farmer appears in parish roster.
2. Farmer declares 14 bags ungraded; agent grading visit is queued; agent records 12.8%; grade 1 applied; farmer notified.
3. Declarations accumulate to `min_bags`; lot closes automatically; all bids become visible; every farmer in the lot receives them.
4. Buyer submits a bid before closure and cannot read any other buyer's bid.
5. Committee awards a non-highest bid with a minute reference; settlements are created with grade factors applied; commission is charged to the buyer, not the farmer.
6. Farmer grants SACCO consent, the SACCO reads harvest history successfully, farmer revokes, the next read is refused, and both the allowed and refused attempts appear in the access log.
7. Parish metric recomputes on closure, district and national rollups follow, and the district ranking reorders.

### 11.2 Invariants asserted in tests

- `Settlement.net_amount == Settlement.gross_amount` (commission never falls on the farmer).
- No `AccessLog` row is ever updated or deleted.
- `visible_bids()` returns empty for a non-owner while `lot.status == OPEN`, for every role.
- District metric equals the volume-weighted aggregate of its parish metrics, never the arithmetic mean.
- No delivery of `AdvisoryContent` with `status != 'validated'`.
- No `TrendInsight` delivery where `approved_by IS NULL`.

---

## 12. Performance and load

The load case is the harvest peak, not the average day.

| Scenario | Profile | Target |
|---|---|---|
| Steady season day | 200 concurrent, 80% reads | p95 < 500 ms |
| Harvest peak | 2,000 concurrent, 60% writes, declaration-heavy | p95 < 800 ms, no errors |
| District advisory push | 40,000 SMS queued in 60 s | drained within gateway limits, no dropped messages |
| National dashboard | 130 districts, 10,500 parishes ranked | < 1.5 s, served from `*SeasonMetric` only |

k6 script lives at `tests/load/harvest_peak.js`. Run before every release that touches `market` or `analytics`.

---

## 13. Security and data protection checklist

Mapped to the Data Protection and Privacy Act, 2019. Each item is a release gate.

- [ ] Registered with the Personal Data Protection Office before any live farmer data
- [ ] TLS 1.3 enforced; HSTS; secure and httpOnly cookies
- [ ] Database encryption at rest; encrypted, tested backups
- [ ] `nin_hash` only, peppered; raw NIN never stored or logged
- [ ] Identity fields in a separate schema with separate role grants from behavioural data
- [ ] `AccessLog` append-only, enforced by trigger and application guard
- [ ] Consent checked at the boundary for every external read; refusals logged
- [ ] Farmer can view their own access history in the UI
- [ ] Bulk export requires dual authorisation and writes an audit record
- [ ] Agent device cache encrypted; 12-hour session expiry; remote wipe
- [ ] Rate limiting on auth endpoints; PIN lockout after 5 failures
- [ ] Dependency scanning in CI; no known high-severity CVEs at release
- [ ] Independent penetration test passed — **blocking gate, not a finding for later**
- [ ] Logs scrubbed of phone numbers and identity fields

---

## 14. Deployment

```
nginx (TLS, static) → gunicorn (3 workers × 2 threads) → Django
                          ├── PostgreSQL 16 (primary + nightly base backup + WAL)
                          ├── Redis 7 (cache, celery broker, sessions)
                          └── Celery worker ×2 + beat
```

Hosted in the NITA-U national data centre for data residency. Media (pest photographs) on object storage with private ACLs and signed URLs.

Release procedure: migrate on a maintenance window only if a migration is destructive; otherwise use expand-and-contract so deploys are zero-downtime. Every release runs the invariant tests in 11.2 in CI and blocks on failure.

Monitoring: uptime probe on `/healthz`, error tracking, Celery queue depth alarm, and a dashboard alarm if `computed_at` on any active parish metric falls more than 36 hours behind — a stale metric shown as current is worse than no metric.

---

## 15. Seed and demo data

`python manage.py seed_demo --district Mukono --parish Kyampisi --farmers 40` creates a district, sub-county, three parishes, villages, crops, the current season, forty farmers with staggered planting dates across weeks 1–14, an open lot, four verified buyers, and three seasons of historical metrics so the trend engine has something to detect. This command backs the mockups and the acceptance demo; it **MUST NOT** be importable in production settings.

---

## 16. Delivery plan

| Sprint | Weeks | Deliverable | Acceptance |
|---|---|---|---|
| 0 | 1–2 | Repo, CI, settings, geo + accounts models, auth, scoping mixin | A district officer and a parish chief see different parish sets from the same view |
| 1 | 3–4 | Farmer registry, plots, plantings, agent registration wizard | Journey 1 passes end to end |
| 2 | 5–6 | Advisory content model, ingestion of validated MAAIF/NARO content, advisory engine, farmer home | Two farmers with planting dates two weeks apart receive different advice on the same day |
| 3 | 7–8 | Declaration, grading, lot lifecycle, parish dashboard | Journeys 2 and 3 pass |
| 4 | 9–10 | Buyer portal, sealed bidding, award, settlement | Journeys 4 and 5 pass; sealing verified for every role |
| 5 | 11–12 | Consent centre, access log, partner read endpoint | Journey 6 passes; access history visible to the farmer |
| 6 | 13–14 | Metrics rollup, district and national dashboards, ranking | Journey 7 passes; national dashboard under 1.5 s on seeded scale data |
| 7 | 15–16 | Trend engine, approval workflow, delivery to farmers | An unapproved insight cannot reach a farmer by any code path |
| 8 | 17–18 | Offline PWA hardening, SMS notification, load test, penetration test, pilot readiness | Section 12 targets met; section 13 checklist fully green |

Definition of done for every ticket: tests written and passing, `ruff` and `black` clean, no business rule outside `services.py`, migration reviewed, and the relevant checklist item in section 13 still green.

---

## 17. Phase 2 extension contract

The USSD adapter, when it is built, **MUST** satisfy these constraints, and the Phase 1 code is written so that it can:

1. It calls `farmers.services.register_farmer`, `market.services.declare`, `consent.services.grant` / `revoke` and `advisory.selectors.advice_for` directly. It reimplements nothing.
2. Each USSD screen body stays within 182 characters. `advisory.selectors.advice_for` already returns bodies capped at 480 characters, so the adapter is responsible for paging, not for truncation — truncated agronomic advice can be dangerous.
3. Session state lives in Redis keyed by MSISDN with a 180-second expiry. No session state in the database.
4. `Declaration.declared_via` and `AdvisoryDelivery.channel` record the channel, so the evaluation can compare outcomes between agent-mediated and self-service farmers. That comparison is a stated research question, and it only works if the field is populated from day one — which is why it exists in Phase 1 despite there being only one channel.
