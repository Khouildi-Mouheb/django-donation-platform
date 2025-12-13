from django.urls import path
from .views import (create_proposition , valider_demande,
                    traiter_proposition, proposition_detail,
                    participant_donations, confirmer_remise_donateur,
                    ajouter_au_stock,
                    stock_list,
                    create_demande,
                    demande_detail,
                    traiter_demande,
                    getDemandeRelatedItems,
                    assign_transporteur_demande,
                    transporteur_confirme_demande   )

urlpatterns = [
    path('demande/<int:demande_id>/traiter_demande/', traiter_demande, name='traiter_demande'),
    path('demande/<int:demande_id>/assign_transporteur', assign_transporteur_demande, name='assign_transporteur_demande'),
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
    path('demandes/create/',create_demande,name="create_demande"),
    path("demande/<int:demande_id>/",demande_detail,name="demande_detail"),
    path("demande/<int:demande_id>/related_items/",getDemandeRelatedItems,name="related_items"),
    path('demande/<int:demande_id>/confirmer/', 
         transporteur_confirme_demande, 
         name='transporteur_confirme_demande'),
    
]
