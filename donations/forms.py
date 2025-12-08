from django import forms
from .models import PropositionDon

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
