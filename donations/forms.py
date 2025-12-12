from django import forms
from .models import PropositionDon , DemandeDon

class PropositionDonForm(forms.ModelForm):
    class Meta:
        model = PropositionDon
        fields = [
            "categorie",
            "type_materiel",
            "quantite",
            "description",
            "etat",
            "photos",
            "adresse_ramassage",
            "ville",
            "code_postal",
            "disponibilite_ramassage",
        ]



class DemandeDonForm(forms.ModelForm):
    class Meta:
        model = DemandeDon
        fields = [
            'type_materiel',
            'categorie_recherchee',
            'description_besoin',
            'quantite_desiree',
            'urgence',

            

                  ]
