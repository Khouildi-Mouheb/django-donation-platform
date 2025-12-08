from django.contrib import admin
from . import models

admin.site.register(models.CategorieObjet)
admin.site.register(models.DemandeDon)
admin.site.register(models.PropositionDon)
admin.site.register(models.Don)

