from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from apps.core.models import TimeStampedModel


class Role(models.TextChoices):
    NATIONAL_ADMIN = "national_admin"
    DISTRICT_OFFICER = "district_officer"
    SUBCOUNTY_OFFICER = "subcounty_officer"
    PARISH_CHIEF = "parish_chief"
    AGENT = "agent"
    BUYER = "buyer"
    FARMER = "farmer"


class ScopeLevel(models.TextChoices):
    NATIONAL = "national"
    DISTRICT = "district"
    SUBCOUNTY = "subcounty"
    PARISH = "parish"


class SystemUserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        # A superuser is, by definition, top-of-scope: default it to
        # national_admin/national rather than leaving role/scope_level
        # blank, which trips the user_scope_matches_level CHECK constraint
        # (createsuperuser only prompts for USERNAME_FIELD + REQUIRED_FIELDS).
        extra_fields.setdefault("role", Role.NATIONAL_ADMIN)
        extra_fields.setdefault("scope_level", ScopeLevel.NATIONAL)
        extra_fields.setdefault("scope_id", None)
        return self.create_user(phone, password, **extra_fields)


class SystemUser(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    phone = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=120)
    role = models.CharField(max_length=24, choices=Role.choices)
    scope_level = models.CharField(max_length=16, choices=ScopeLevel.choices)
    scope_id = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    objects = SystemUserManager()
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        constraints = [models.CheckConstraint(
            check=models.Q(scope_level=ScopeLevel.NATIONAL,
                           scope_id__isnull=True)
            | models.Q(scope_level__in=[ScopeLevel.DISTRICT, ScopeLevel.SUBCOUNTY, ScopeLevel.PARISH], scope_id__isnull=False),
            name="user_scope_matches_level",
        )]
