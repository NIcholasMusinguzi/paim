from django.contrib import admin

from .models import District, Parish, Subcounty, Village

admin.site.register([District, Parish, Subcounty, Village])
