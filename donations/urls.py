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
                    transporteur_confirme_demande ,
                    assign_transporteur_proposition,
                    transporteur_confirme_proposition,
                    )


from . import views

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

     path('demande/<int:demande_id>/confirmer-reception/', 
         views.confirmer_reception_demande, 
         name='confirmer_reception_demande'),
    
    # View all demands (we'll create this next)
    path('mes-demandes/', views.mes_demandes, name='mes_demandes'),
    path('mes-propositions/', views.mes_propositions, name='mes_propositions'),
    path('proposition/<int:proposition_id>/', views.proposition_details, name='proposition_details'),
    path('proposition/<int:proposition_id>/confirmer-remise/', 
         views.confirmer_remise_donateur, 
         name='confirmer_remise_donateur'),
    
    # Participant missions (for transporter role)
    path('mes-missions/', views.mes_missions_acceptees, name='mes_missions_acceptees'),
    
    # Participant demands (from previous code)
    path('mes-demandes/', views.mes_demandes, name='mes_demandes'),
    path('demande/<int:demande_id>/confirmer-reception/', 
         views.confirmer_reception_demande, 
         name='confirmer_reception_demande'),

     path('dashboard/membre/proposition/<int:proposition_id>/assign/', 
         assign_transporteur_proposition, 
         name='assign_transporteur'),

     path("dashboard/transporteur/proposition/confirme/<int:proposition_id>/",
         transporteur_confirme_proposition,
         name="transporteur_confirme_proposition"),


     path('proposition/<int:proposition_id>/confirmer-reception-transporteur/', 
         views.transporteur_confirme_reception_proposition, 
         name='transporteur_confirme_reception_proposition'),
    
    # Transporteur confirms delivery to receiver (for demandes)
    path('demande/<int:demande_id>/confirmer-livraison-transporteur/', 
         views.transporteur_confirme_livraison_demande, 
         name='transporteur_confirme_livraison_demande'),

    
]
