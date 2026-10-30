from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from apps.accounts.frontend_dev import frontend_asset


def health(request):
    return JsonResponse({"service": "movego-api", "status": "ok", "version": "0.1"})


urlpatterns = [
    path('api/payments/', include('apps.rides.payment_urls')),
    path('api/trips/', include('apps.rides.trip_urls')),
    path("api/", include("apps.accounts.avatar_urls")),
    path("api/dispatch/", include("apps.rides.dispatch_urls")),
    path("api/driver-discovery/", include("apps.rides.discovery_urls")),
    path("api/ride-management/", include("apps.rides.manage_urls")),
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/", include("apps.accounts.urls")),
]

# Development only. In production, serve built frontend assets via an actual web server.
# Same-origin requests avoid disabling CSRF or opening permissive CORS rules.

urlpatterns += [
        path("", RedirectView.as_view(url="/app/passenger/", permanent=False)),
        path("app/", RedirectView.as_view(url="/app/passenger/", permanent=False)),
        path("app/passenger/", RedirectView.as_view(url="/app/passenger/index.html", permanent=False)),
        re_path(r"^app/(?P<asset_path>.+)$", frontend_asset, name="frontend-dev-asset"),
        path("api/rides/", include("apps.rides.urls")),
        path(
    "api/locations/",
    include("apps.rides.location_urls")
),
        path("api/fares/", include("apps.rides.fare_urls")),
        path("api/ride-requests/", include("apps.rides.request_urls")),
        path("api/drivers/", include("apps.drivers.urls")),
    ]
