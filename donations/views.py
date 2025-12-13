"""
donations/views.py - Views for donation management (propositions, demandes, stock)
"""

# ============ IMPORTS ============
# Django core
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

# Local imports
from .forms import PropositionDonForm, DemandeDonForm
from .models import DemandeDon, PropositionDon, Don
from users.views import getAvailableTransporteurs
from users.models import Transporteur
from notifications.models import Notification


# ============ DECORATORS ============
def participant_required(view_func):
    """Decorator to ensure only participants can access."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.user_type != "participant":
            messages.error(request, "Seuls les participants peuvent proposer un don.")
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return wrapper


# ============ STOCK & INVENTORY VIEWS ============
@login_required
def stock_list(request):
    """Display all donations in stock."""
    dons = Don.objects.all()
    return render(request, "donations/stock/stock_list.html", {"dons": dons})


@login_required
def ajouter_au_stock(request, proposition_id):
    """Add a validated proposition to the stock."""
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('home')

    # Prevent duplicate Don creation
    if hasattr(proposition, 'don_realise'):
        messages.warning(request, "Ce don est déjà en stock.")
        return redirect('membre_dashboard')

    don = Don.objects.create(
        proposition=proposition,
        categorie=proposition.categorie,
        type_materiel=proposition.type_materiel,
        quantite=proposition.quantite,
        description=proposition.description,
        etat=proposition.etat,
        photos=proposition.photos,
        lieu_stockage="Entrepôt principal"
    )
    messages.success(request, 
                     f"Proposition #{proposition.id} ajoutée au stock comme Don #{don.reference}.")
    return redirect('membre_dashboard')


# ============ PARTICIPANT DASHBOARD VIEWS ============
@login_required
def participant_donations(request):
    """Display donations made by the current participant."""
    if not hasattr(request.user, 'participant'):
        messages.error(request, "Accès réservé aux participants.")
        return redirect('home')

    propositions = PropositionDon.objects.filter(
        participant_donateur=request.user.participant
    )
    return render(request, "dashboards/participant.html", 
                  {"propositions": propositions})


@login_required
def confirmer_remise_donateur(request, proposition_id):
    """Allow donor to confirm they have handed over the donation."""
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    if not hasattr(request.user, 'participant') or proposition.participant_donateur != request.user.participant:
        messages.error(request, "Vous n'êtes pas autorisé à confirmer cette remise.")
        return redirect('home')

    proposition.donator_gives = True
    proposition.save()
    messages.success(request, f"Vous avez confirmé la remise du don #{proposition.id}.")
    return redirect('participant_donations')


# ============ CREATE DONATION VIEWS ============
@participant_required
def create_proposition(request):
    """Create a new donation proposition."""
    if request.method == "POST":
        form = PropositionDonForm(request.POST, request.FILES)
        if form.is_valid():
            proposition = form.save(commit=False)
            proposition.statut = "en_attente"
            proposition.participant_donateur = request.user.participant
            proposition.save()
            messages.success(request, "Votre proposition de don a été créée avec succès.")
            return redirect("home")
    else:
        form = PropositionDonForm()
    return render(request, "donations/propositions/create_proposition.html", 
                  {"form": form})


@participant_required
def create_demande(request):
    """Create a new donation request."""
    if request.method == "POST":
        form = DemandeDonForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.statut = "en_attente"
            demande.participant_requerant = request.user.participant
            demande.save()
            messages.success(request, "Votre proposition de don a été créée avec succès.")
            return redirect("home")
    else:
        form = DemandeDonForm()
    return render(request, "donations/demandes/create_demande.html", 
                  {"form": form})


# ============ MEMBER VALIDATION VIEWS ============
@login_required
def valider_demande(request, demande_id):
    """Validate or refuse a donation request (member only)."""
    demande = get_object_or_404(DemandeDon, id=demande_id)

    if not hasattr(request.user, 'membre'):
        messages.error(request, "Vous n'avez pas les droits pour valider cette demande.")
        return redirect('liste_demandes')

    action = request.POST.get('action')  # "valider" or "refuser"
    if action == "valider":
        demande.statut = "validee"
        demande.date_validation = timezone.now()
        demande.membre_validateur = request.user.membre
        demande.save()
        messages.success(request, f"Demande #{demande.id} validée avec succès.")
    elif action == "refuser":
        raison = request.POST.get('raison_refus', '')
        demande.statut = "refusee"
        demande.date_validation = timezone.now()
        demande.membre_validateur = request.user.membre
        demande.raison_refus = raison
        demande.save()
        messages.warning(request, f"Demande #{demande.id} refusée.")
    else:
        messages.error(request, "Action non reconnue.")

    return redirect('liste_demandes')


@login_required
def traiter_proposition(request, proposition_id):
    """Process a donation proposition (validate/refuse)."""
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('membre_dashboard')

    if request.method == "POST":
        action = request.POST.get('action')
        if action == "valider":
            proposition.statut = "validee"
            proposition.date_validation = timezone.now()
            proposition.membre_validateur = request.user.membre
            proposition.save()
            messages.success(request, f"Proposition #{proposition.id} validée.")
        elif action == "refuser":
            proposition.statut = "refusee"
            proposition.date_validation = timezone.now()
            proposition.membre_validateur = request.user.membre
            proposition.raison_refus = request.POST.get('raison_refus', '')
            proposition.save()
            messages.warning(request, f"Proposition #{proposition.id} refusée.")
    return redirect('membre_dashboard')


@login_required
def traiter_demande(request, demande_id):
    """Process a donation demande (validate/refuse)."""
    demande = get_object_or_404(DemandeDon, id=demande_id)

    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('membre_dashboard')

    if request.method == "POST":
        action = request.POST.get('action')
        if action == "valider":
            demande.statut = "validee"
            demande.date_validation = timezone.now()
            demande.membre_validateur = request.user.membre
            demande.save()
            messages.success(request, f"Proposition #{demande.id} validée.")
        elif action == "refuser":
            demande.statut = "refusee"
            demande.date_validation = timezone.now()
            demande.membre_validateur = request.user.membre
            demande.raison_refus = request.POST.get('raison_refus', '')
            demande.save()
            messages.warning(request, f"Proposition #{demande.id} refusée.")
    return redirect('membre_dashboard')


# ============ DETAIL VIEWS ============
@login_required
def proposition_detail(request, proposition_id):
    """Display details of a specific proposition."""
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('home')

    return render(request, 'donations/propositions/proposition_detail.html', {
        'proposition': proposition
    })


def demande_detail(request, demande_id):
    """Display details of a specific demande."""
    demande = get_object_or_404(DemandeDon, id=demande_id)

    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('home')

    return render(request, 'donations/demandes/demande_detail.html', {
        'demande': demande
    })


def getDemandeRelatedItems(request, demande_id):
    """Get related items in stock for a specific demande."""
    demande = get_object_or_404(DemandeDon, id=demande_id)
    categorie = demande.categorie_recherchee
    related_items = Don.objects.filter(categorie=categorie)
    return render(request, "donations/demandes/related_items.html",
                  {"related_items": related_items})


# ============ TRANSPORTER ASSIGNMENT VIEWS ============
@login_required
def assign_transporteur_demande(request, demande_id):
    """Assign a transporter to a demande (member only)."""
    demande = get_object_or_404(DemandeDon, id=demande_id)

    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('membre_dashboard')

    if request.method == "POST":
        transporteur_id = request.POST.get("transporteur_id")
        if transporteur_id:
            transporteur = get_object_or_404(Transporteur, id=transporteur_id)
            demande.transporteur_livraison = transporteur
            demande.statut = "validee"
            demande.date_validation = timezone.now()
            demande.membre_validateur = request.user.membre
            demande.save()

            # Create notification for transporteur
            Notification.objects.create(
                receiver=transporteur,
                proposition=None,
                demande=demande,
                titre=f"Nouvelle mission: demande #{demande.id}",
                message="Vous avez été assigné pour twasseel ce don."
            )

            messages.success(request, f"Transporteur {transporteur} assigné à la proposition #{demande.id}.")
            return redirect('membre_dashboard')

    available_transporteurs = getAvailableTransporteurs()
    return render(request, "donations/demandes/assign_transporteur.html", {
        "demande": demande,
        "transporteurs": available_transporteurs
    })


# donations/views.py
@login_required
def transporteur_confirme_demande(request, demande_id):
    demande = get_object_or_404(DemandeDon, id=demande_id)
    
    # Security check
    if not hasattr(request.user, 'transporteur') or demande.transporteur_livraison != request.user.transporteur:
        messages.error(request, "Accès non autorisé.")
        return redirect('transporteur_dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accepter':
            demande.transporteur_confirme = True
            demande.statut = 'en_cours'  # Changed from 'validee' to 'en_cours'
            demande.save()
            messages.success(request, f"✅ Mission #{demande.id} acceptée!")
            
        elif action == 'refuser':
            raison_refus = request.POST.get('raison_refus', '')
            demande.transporteur_confirme = False
            demande.transporteur_raison_refus = raison_refus
            demande.transporteur_livraison = None
            demande.statut = 'validee'
            demande.save()
            messages.warning(request, f"❌ Mission #{demande.id} refusée.")
            
        elif action == 'demarrer':
            demande.statut = 'en_livraison'
            demande.save()
            messages.success(request, f"🚚 Livraison #{demande.id} démarrée!")
            
        elif action == 'marquer comme terminer':
            demande.statut = 'terminee'
            demande.save()
            messages.success(request, f"✅ Mission #{demande.id} terminée!")
        
        # Redirect back to the same page
        return redirect('transporteur_confirme_demande', demande_id=demande_id)
    
    # GET request - display the page
    return render(request, 'donations/demandes/transporteur_confirme_demande.html', {
        'demande': demande
    })
# ============ COMPLETION VIEWS ============
@login_required
def terminer_proposition(request, proposition_id):
    """Mark a proposition as completed (transporter only)."""
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    if not hasattr(request.user, 'transporteur') or proposition.transporteur_assignee != request.user.transporteur:
        messages.error(request, "Vous n'êtes pas autorisé à terminer cette mission.")
        return redirect('transporteur_dashboard')

    proposition.statut = "terminee"
    proposition.save()
    messages.success(request, f"Proposition #{proposition.id} marquée comme terminée.")
    return redirect('transporteur_dashboard')