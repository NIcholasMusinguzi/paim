from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.accounts.admin_viewsets import SystemUserViewSet
from apps.farmers.admin_viewsets import CropViewSet, FarmerViewSet, SeasonViewSet
from apps.geo.admin_viewsets import DistrictViewSet, ParishViewSet, SubcountyViewSet, VillageViewSet
from apps.market.admin_viewsets import BidViewSet, BuyerViewSet, MarketPriceViewSet
from apps.market.views import HealthView

# The admin configuration API: geography, crops, seasons, users and buyers.
# Pure CRUD over reference/administration data — the one place ModelViewSet
# is appropriate, since none of this carries the domain rules that live in
# apps/*/services.py for everything else.
admin_router = DefaultRouter()
admin_router.register("districts", DistrictViewSet)
admin_router.register("subcounties", SubcountyViewSet)
admin_router.register("parishes", ParishViewSet)
admin_router.register("villages", VillageViewSet)
admin_router.register("farmers", FarmerViewSet)
admin_router.register("crops", CropViewSet)
admin_router.register("seasons", SeasonViewSet)
admin_router.register("buyers", BuyerViewSet)
admin_router.register("bids", BidViewSet)
admin_router.register("market-prices", MarketPriceViewSet)
admin_router.register("users", SystemUserViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", HealthView.as_view()),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.market.urls")),
    path("api/v1/", include("apps.farmers.urls")),
    path("api/v1/", include("apps.sync.urls")),
    path("api/v1/", include("apps.geo.urls")),
    path("api/v1/", include("apps.analytics.urls")),
    path("api/v1/", include("apps.advisory.urls")),
    path("api/v1/admin/", include(admin_router.urls)),
]
