"""ferreteria_ml URL Configuration"""
from django.contrib import admin
from django.urls import path, include

# --- ESTOS SON LOS DOS IMPORTS QUE FALTABAN ---
from django.conf import settings
from django.conf.urls.static import static
# ----------------------------------------------

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tienda.urls')),
]

# AGREGA ESTO AL FINAL:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)