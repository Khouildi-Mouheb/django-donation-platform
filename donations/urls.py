from django.urls import path
from .views import (create_proposition , valider_demande,
                    traiter_proposition, proposition_detail,
                    participant_donations, confirmer_remise_donateur,
                    ajouter_au_stock,
                    stock_list)

urlpatterns = [
    path('demande/<int:demande_id>/valider/', valider_demande, name='valider_demande'),
    path("propositions/create/", create_proposition, name="create_proposition"),
    path('dashboard/membre/proposition/<int:proposition_id>/traiter/',traiter_proposition, name='traiter_proposition'),
    path('dashboard/membre/proposition/<int:proposition_id>/',proposition_detail, name='proposition_detail'),
    path("dashboard/participant/donations/", participant_donations, name="participant_donations"),
    path("dashboard/participant/proposition/<int:proposition_id>/confirmer/",
         confirmer_remise_donateur, name="confirmer_remise_donateur"),
         path(
    "dashboard/membre/proposition/<int:proposition_id>/ajouter-stock/",
    ajouter_au_stock,
    name="ajouter_au_stock"
    ),
    path("dashboard/membre/stock/", stock_list, name="stock_list"), 
]
