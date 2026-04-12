from django.contrib import admin

from apps.auditoria.models import EventoAuditoria


@admin.register(EventoAuditoria)
class AdministradorEventoAuditoria(admin.ModelAdmin):
    list_display = ("categoria", "accion", "usuario", "referencia_partida", "creada_en")
    list_filter = ("categoria", "accion")
    search_fields = ("categoria", "accion", "usuario__username", "referencia_partida")
