from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # API endpoints (clean and isolated)
    path('api/', include('APP.urls')),

    # Frontend pages (HTML views)
    path('', include('APP.urls')),
]
