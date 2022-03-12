from django.conf import settings
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),

    path('', include("web.urls",namespace="web")),

    path('api/v1/accounts/',include('api.v1.accounts.urls', namespace="api_v1_accounts"))
]
