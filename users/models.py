from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER_TYPES = (
        ("participant", "Participant"),
        ("membre", "Membre"),
        ("transporteur", "Transporteur"),
        ("admin", "Admin"),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default="participant")

    def __str__(self):
        return self.username


class Participant(User):
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Participant"

    def __str__(self):
        return f"Participant {self.username}"


class Membre(User):
    role = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Membre"

    def __str__(self):
        return f"Membre {self.username}"


class Transporteur(User):
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    vehicule = models.CharField(max_length=100)
    disponibilite = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Transporteur"

    def __str__(self):
        return f"Transporteur {self.username}"


class Admin(User):
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Admin"

    def __str__(self):
        return f"Admin {self.username}"
