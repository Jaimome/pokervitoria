from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("apps.nucleo.urls")),
    path("partidas/", include("apps.partidas.urls")),
    path("usuarios/", include("apps.usuarios.urls")),
    path("admin/", admin.site.urls),
]
