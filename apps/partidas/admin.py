from django.contrib import admin

from apps.partidas.models import CartaPrivada, ManoPoker, ParticipacionPartida, PartidaPoker


class ParticipacionPartidaEnLinea(admin.TabularInline):
    model = ParticipacionPartida
    extra = 0


class ManoPokerEnLinea(admin.TabularInline):
    model = ManoPoker
    extra = 0


@admin.register(PartidaPoker)
class AdministradorPartidaPoker(admin.ModelAdmin):
    list_display = (
        "nombre",
        "estado",
        "maximo_jugadores",
        "ciega_pequena",
        "ciega_grande",
        "creada_en",
    )
    list_filter = ("estado",)
    search_fields = ("nombre",)
    inlines = [ParticipacionPartidaEnLinea, ManoPokerEnLinea]


@admin.register(ParticipacionPartida)
class AdministradorParticipacionPartida(admin.ModelAdmin):
    list_display = ("partida", "usuario", "numero_asiento", "fichas", "estado", "es_ganador")
    list_filter = ("estado", "es_ganador")
    search_fields = ("partida__nombre", "usuario__username", "usuario__nombre_mostrado")


@admin.register(ManoPoker)
class AdministradorManoPoker(admin.ModelAdmin):
    list_display = ("partida", "numero_mano", "estado", "creada_en")
    list_filter = ("estado",)
    search_fields = ("partida__nombre",)


@admin.register(CartaPrivada)
class AdministradorCartaPrivada(admin.ModelAdmin):
    list_display = ("mano", "participacion", "orden", "codigo")
    search_fields = ("mano__partida__nombre", "participacion__usuario__username", "codigo")
