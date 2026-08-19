from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    
    path("admin/",
       admin.site.urls),


    path(
        "accounts/",
        include("allauth.urls"),
    ),

    path(
        "api/accounts/token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),

    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),

    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema"
        ),
        name="swagger-ui",
    ),

    path(
        "api/accounts/",
        include("apps.accounts.urls"),

    ),

    path(
        "api/courses/",
        include("apps.courses.urls"),
    ),

    path(
        "api/categories/",
        include("apps.categories.urls"),
    ),

    path(
        "api/enrollments/",
        include("apps.enrollments.urls"),
    ),
    path(
        "api/progress/",
        include("apps.progress.urls"),
    ),
    ]