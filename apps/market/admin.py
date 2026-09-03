from django.contrib import admin

from .models import AwardRecord, Bid, Buyer, Declaration, Lot, Settlement

admin.site.register([AwardRecord, Bid, Buyer, Declaration, Lot, Settlement])
