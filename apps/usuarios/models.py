from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """Modelo base de usuario del proyecto."""

    saldo_total = models.PositiveIntegerField(default=2000)

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self) -> str:
        return self.username
