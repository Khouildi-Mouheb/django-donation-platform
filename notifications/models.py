from django.db import models
from django.utils import timezone
from users.models import User, Membre  # adjust import paths
from donations.models import PropositionDon  # adjust import paths

class Notification(models.Model):
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    proposition = models.ForeignKey(PropositionDon, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    titre = models.CharField(max_length=200)
    message = models.TextField()
    date_creation = models.DateTimeField(default=timezone.now)
    lu = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification pour {self.receiver} - {self.titre}"
