from django.contrib import admin

from apps.clasificacion.models import EstadisticasJugador


@admin.register(EstadisticasJugador)
class AdministradorEstadisticasJugador(admin.ModelAdmin):
    list_display = (
        "usuario",
        "partidas_jugadas",
        "victorias",
        "derrotas",
        "puntos",
        "racha_actual",
        "mejor_racha",
    )
    search_fields = ("usuario__username", "usuario__nombre_mostrado", "usuario__email")
