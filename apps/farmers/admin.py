from django.contrib import admin

from .models import Crop, Farmer, Planting, Plot, Season

admin.site.register([Crop, Farmer, Planting, Plot, Season])
