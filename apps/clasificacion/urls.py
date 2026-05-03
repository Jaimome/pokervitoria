from django.urls import path

from apps.clasificacion.views import VistaRanking


app_name = "clasificacion"

urlpatterns = [
    path("", VistaRanking.as_view(), name="ranking"),
]
