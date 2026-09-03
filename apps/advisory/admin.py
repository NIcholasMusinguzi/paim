from django.contrib import admin

from .models import AdvisoryContent, AdvisoryDelivery

admin.site.register([AdvisoryContent, AdvisoryDelivery])
