from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AdministradorUsuarioDjango

from apps.usuarios.models import Usuario


@admin.register(Usuario)
class AdministradorUsuario(AdministradorUsuarioDjango):
    list_display = ("username", "email", "nombre_mostrado", "is_staff", "is_active")
    search_fields = ("username", "email", "nombre_mostrado")
    fieldsets = AdministradorUsuarioDjango.fieldsets + (
        ("Pokervitoria", {"fields": ("nombre_mostrado",)}),
    )
