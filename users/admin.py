from django.contrib import admin
from . import models

admin.site.register(models.User)
admin.site.register(models.Participant)
admin.site.register(models.Membre)
admin.site.register(models.Transporteur)
admin.site.register(models.Admin)
  
