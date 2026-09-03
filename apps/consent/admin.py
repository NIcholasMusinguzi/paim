from django.contrib import admin

from .models import AccessLog, Consent, Organisation

admin.site.register([AccessLog, Consent, Organisation])
