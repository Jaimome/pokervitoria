from django.urls import path

from apps.nucleo.views import VistaInicio


app_name = "nucleo"

urlpatterns = [
    path("", VistaInicio.as_view(), name="inicio"),
]
