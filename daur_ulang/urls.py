from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('waste/', include('waste_mgmt.urls')),
    path('', RedirectView.as_view(url='/waste/', permanent=False)),
]
