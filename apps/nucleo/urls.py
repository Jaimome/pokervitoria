from django.urls import path

from apps.nucleo.views import VistaInicio, VistaReglasPoker


app_name = "nucleo"

urlpatterns = [
    path("", VistaInicio.as_view(), name="inicio"),
    path("reglas/", VistaReglasPoker.as_view(), name="reglas"),
]
