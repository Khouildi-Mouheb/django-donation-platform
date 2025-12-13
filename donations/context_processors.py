# donations/context_processors.py
from .models import Don, DemandeDon, PropositionDon
from users.models import Transporteur

def home_stats(request):
    return {
        'total_donations': Don.objects.count(),
        'active_requests': DemandeDon.objects.filter(statut='en_attente').count(),
        'total_transporters': Transporteur.objects.filter(disponibilite=True).count(),
        'completed_missions': PropositionDon.objects.filter(statut='terminee').count()
    }