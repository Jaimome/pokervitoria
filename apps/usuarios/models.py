from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Modelo base de usuario del proyecto.

    Lo definimos desde el principio para evitar sustituir el modelo de usuario
    de Django a mitad del desarrollo.
    """

    saldo_total = models.PositiveIntegerField(default=2000)

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self) -> str:
        return self.username
