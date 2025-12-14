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

    # Check if donor confirmed giving items to transporter
    if not proposition.donator_gives:
        messages.warning(request, "Le donateur n'a pas encore confirmé la remise au transporteur.")
        return redirect('proposition_detail', proposition_id=proposition_id)

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
            messages.success(request, "Votre proposition de don a été créée avec succès. Elle sera validée par un membre.")
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
            messages.success(request, "Votre demande de don a été créée avec succès. Elle sera validée par un membre.")
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
        # Redirect to assign transporteur after validation
        return redirect('assign_transporteur_demande', demande_id=demande.id)
    elif action == "refuser":
        raison = request.POST.get('raison_refus', '')
        demande.statut = "refusee"
        demande.date_validation = timezone.now()
        demande.membre_validateur = request.user.membre
        demande.raison_refus = raison
        demande.save()
        messages.warning(request, f"Demande #{demande.id} refusée.")
        return redirect('liste_demandes')
    else:
        messages.error(request, "Action non reconnue.")
        return redirect('liste_demandes')


# donations/views.py
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
            # Fix: Changed from 'assign_transporteur_view' to 'assign_transporteur'
            return redirect('assign_transporteur', proposition_id=proposition.id)
        elif action == "refuser":
            proposition.statut = "refusee"
            proposition.date_validation = timezone.now()
            proposition.membre_validateur = request.user.membre
            proposition.raison_refus = request.POST.get('raison_refus', '')
            proposition.save()
            messages.warning(request, f"Proposition #{proposition.id} refusée.")
            return redirect('membre_dashboard')
        else:
            messages.error(request, "Action non reconnue.")
            return redirect('membre_dashboard')
    return redirect('membre_dashboard')



# donations/views.py

# TRANSPORTER CONFIRMS RECEIVING FROM DONOR (for propositions)
@login_required
def transporteur_confirme_reception_proposition(request, proposition_id):
    """Transporter confirms they received items from donor"""
    proposition = get_object_or_404(PropositionDon, id=proposition_id)
    
    # Security check - only assigned transporter can confirm
    if not hasattr(request.user, 'transporteur') or proposition.transporteur_assignee != request.user.transporteur:
        messages.error(request, "Accès non autorisé.")
        return redirect('transporteur_dashboard')
    
    # Can only confirm if donor said they gave the items
    if not proposition.donator_gives:
        messages.error(request, "Le donateur n'a pas encore confirmé la remise.")
        return redirect('transporteur_dashboard')
    
    if request.method == 'POST':
        proposition.transporteur_recoit = True
        proposition.save()
        
        messages.success(request, f"✅ Réception confirmée de la proposition #{proposition.id}!")
        return redirect('transporteur_dashboard')
    
    return render(request, 'donations/propositions/transporteur_confirme_reception.html', {
        'proposition': proposition
    })

# TRANSPORTER CONFIRMS DELIVERY TO RECEIVER (for demandes)
@login_required
def transporteur_confirme_livraison_demande(request, demande_id):
    """Transporter confirms they delivered items to receiver"""
    demande = get_object_or_404(DemandeDon, id=demande_id)
    
    # Security check - only assigned transporter can confirm
    if not hasattr(request.user, 'transporteur') or demande.transporteur_livraison != request.user.transporteur:
        messages.error(request, "Accès non autorisé.")
        return redirect('transporteur_dashboard')
    
    if request.method == 'POST':
        demande.statut = 'terminee'
        demande.date_livraison = timezone.now().date()
        demande.save()
        
        messages.success(request, f"✅ Livraison confirmée pour la demande #{demande.id}!")
        return redirect('transporteur_dashboard')
    
    return render(request, 'donations/demandes/transporteur_confirme_livraison.html', {
        'demande': demande
    })

# donations/views.py - Add this function
@login_required
def assign_transporteur_proposition(request, proposition_id):
    """Assign a transporter to a donation proposition (member only)."""
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    # Ensure only Membre role can assign
    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('membre_dashboard')

    if request.method == "POST":
        transporteur_id = request.POST.get("transporteur_id")
        if transporteur_id:
            transporteur = get_object_or_404(Transporteur, id=transporteur_id)
            proposition.transporteur_assignee = transporteur
            proposition.statut = "validee"
            proposition.date_validation = timezone.now()
            proposition.membre_validateur = request.user.membre
            proposition.save()

            # Create notification for transporteur
            Notification.objects.create(
                receiver=transporteur,
                proposition=proposition,
                titre=f"Nouvelle mission: Proposition #{proposition.id}",
                message="Vous avez été assigné pour ramasser ce don. Veuillez accepter ou refuser la mission.",
                demande=None,
            )

            messages.success(request, f"Transporteur {transporteur} assigné à la proposition #{proposition.id}.")
            return redirect('membre_dashboard')

    # If GET request, show a form to choose transporteur
    available_transporteurs = getAvailableTransporteurs()
    return render(request, "donations/propositions/assign_transporteur.html", {
        "proposition": proposition,
        "transporteurs": available_transporteurs
    })


# donations/views.py - Add this function
@login_required
def transporteur_confirme_proposition(request, proposition_id):
    """Transporter accepts/refuses/completes proposition mission."""
    proposition = get_object_or_404(PropositionDon, id=proposition_id)
    
    # Security check
    if not hasattr(request.user, 'transporteur') or proposition.transporteur_assignee != request.user.transporteur:
        messages.error(request, "Accès non autorisé.")
        return redirect('transporteur_dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accepter':
            proposition.transporteur_statut = 'acceptee'
            proposition.save()
            messages.success(request, f"✅ Mission #{proposition.id} acceptée!")
            return redirect('transporteur_dashboard')
            
        elif action == 'refuser':
            raison_refus = request.POST.get('raison_refus', '')
            proposition.transporteur_statut = 'refusee'
            proposition.raison_refus_transporteur = raison_refus
            proposition.save()
            messages.warning(request, f"❌ Mission #{proposition.id} refusée.")
            return redirect('transporteur_dashboard')
            
        elif action == 'marquer comme terminer':
            proposition.statut = 'terminee'
            proposition.save()
            messages.success(request, f"✅ Mission #{proposition.id} terminée!")
            return redirect('transporteur_dashboard')
    
    # GET request - display the confirmation page
    return render(request, 'donations/propositions/transporteur_confirme_proposition.html', {
        'proposition': proposition
    })

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
            messages.success(request, f"Demande #{demande.id} validée.")
            # Redirect to assign transporteur after validation
            return redirect('assign_transporteur_demande', demande_id=demande.id)
        elif action == "refuser":
            demande.statut = "refusee"
            demande.date_validation = timezone.now()
            demande.membre_validateur = request.user.membre
            demande.raison_refus = request.POST.get('raison_refus', '')
            demande.save()
            messages.warning(request, f"Demande #{demande.id} refusée.")
            return redirect('membre_dashboard')
        else:
            messages.error(request, "Action non reconnue.")
            return redirect('membre_dashboard')
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


@login_required
def demande_detail(request, demande_id):
    """Display details of a specific demande."""
    demande = get_object_or_404(DemandeDon, id=demande_id)

    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('home')

    return render(request, 'donations/demandes/demande_detail.html', {
        'demande': demande
    })


@login_required
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
                message="Vous avez été assigné pour transporter ce don. Veuillez accepter ou refuser la mission."
            )

            messages.success(request, f"Transporteur {transporteur} assigné à la demande #{demande.id}.")
            return redirect('membre_dashboard')

    available_transporteurs = getAvailableTransporteurs()
    return render(request, "donations/demandes/assign_transporteur.html", {
        "demande": demande,
        "transporteurs": available_transporteurs
    })


@login_required
def assign_transporteur_view(request, proposition_id):
    """Assign a transporter to a donation proposition (member only)."""
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    # Ensure only Membre role can assign
    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('membre_dashboard')

    if request.method == "POST":
        transporteur_id = request.POST.get("transporteur_id")
        if transporteur_id:
            transporteur = get_object_or_404(Transporteur, id=transporteur_id)
            proposition.transporteur_assignee = transporteur
            proposition.statut = "validee"
            proposition.date_validation = timezone.now()
            proposition.membre_validateur = request.user.membre
            proposition.save()

            # Create notification for transporteur
            Notification.objects.create(
                receiver=transporteur,
                proposition=proposition,
                titre=f"Nouvelle mission: Proposition #{proposition.id}",
                message="Vous avez été assigné pour ramasser ce don. Veuillez accepter ou refuser la mission.",
                demande=None,
            )

            messages.success(request, f"Transporteur {transporteur} assigné à la proposition #{proposition.id}.")
            return redirect('membre_dashboard')

    # If GET request, show a form to choose transporteur
    available_transporteurs = getAvailableTransporteurs()
    return render(request, "donations/propositions/assign_transporteur.html", {
        "proposition": proposition,
        "transporteurs": available_transporteurs
    })


# ============ TRANSPORTER CONFIRMATION VIEWS ============
@login_required
def transporteur_confirme_demande(request, demande_id):
    """Transporter accepts/refuses demande mission."""
    demande = get_object_or_404(DemandeDon, id=demande_id)
    
    # Security check
    if not hasattr(request.user, 'transporteur') or demande.transporteur_livraison != request.user.transporteur:
        messages.error(request, "Accès non autorisé.")
        return redirect('transporteur_dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accepter':
            demande.transporteur_confirme = True
            demande.statut = 'en_cours'
            demande.transporteur_date_reponse = timezone.now()
            demande.save()
            messages.success(request, f"✅ Mission #{demande.id} acceptée!")
            return redirect('transporteur_dashboard')
            
        elif action == 'refuser':
            raison_refus = request.POST.get('raison_refus', '')
            demande.transporteur_confirme = False
            demande.transporteur_raison_refus = raison_refus
            demande.transporteur_livraison = None
            demande.statut = 'validee'
            demande.transporteur_date_reponse = timezone.now()
            demande.save()
            messages.warning(request, f"❌ Mission #{demande.id} refusée.")
            return redirect('transporteur_dashboard')
            
        elif action == 'demarrer':
            demande.statut = 'en_livraison'
            demande.save()
            messages.success(request, f"🚚 Livraison #{demande.id} démarrée!")
            return redirect('transporteur_dashboard')
            
        elif action == 'marquer comme terminer':
            demande.statut = 'terminee'
            demande.date_livraison = timezone.now().date()
            demande.save()
            messages.success(request, f"✅ Mission #{demande.id} terminée!")
            return redirect('transporteur_dashboard')
    
    # GET request - display the page
    return render(request, 'donations/demandes/transporteur_confirme_demande.html', {
        'demande': demande
    })


@login_required
def transporteur_reponse(request, proposition_id):
    """Handle transporter response to an assigned proposition mission."""
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    # Ensure only the assigned transporteur can respond
    if not hasattr(request.user, 'transporteur') or proposition.transporteur_assignee != request.user.transporteur:
        messages.error(request, "Vous n'êtes pas autorisé à répondre à cette mission.")
        return redirect('transporteur_notifications')

    if request.method == "POST":
        action = request.POST.get('action')
        if action == "accepter":
            proposition.transporteur_statut = "acceptee"
            proposition.save()
            messages.success(request, f"Vous avez accepté la mission pour Proposition #{proposition.id}.")
        elif action == "refuser":
            proposition.transporteur_statut = "refusee"
            proposition.raison_refus_transporteur = request.POST.get('raison_refus', '')
            proposition.save()
            messages.warning(request, f"Vous avez refusé la mission pour Proposition #{proposition.id}.")
        else:
            messages.error(request, "Action non reconnue.")

    return redirect('transporteur_notifications')


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


@login_required
def marquer_demande_terminee_transporteur(request, demande_id):
    """Mark a demande as completed by the assigned transporter."""
    demande = get_object_or_404(DemandeDon, id=demande_id)

    if not hasattr(request.user, 'transporteur') or demande.transporteur_livraison != request.user.transporteur:
        messages.error(request, "Vous n'êtes pas autorisé à terminer cette mission.")
        return redirect('transporteur_dashboard')

    if demande.statut != 'terminee':
        demande.statut = 'terminee'
        demande.date_livraison = timezone.now().date()
        demande.save()
        messages.success(request, f"Demande #{demande.id} marquée comme terminée.")

    return redirect('transporteur_dashboard')


# ============ PARTICIPANT CONFIRMATION VIEWS ============
@login_required
def confirmer_remise_donateur(request, proposition_id):
    """Donor confirms they gave the items to the transporter"""
    proposition = get_object_or_404(PropositionDon, id=proposition_id)
    
    # Security check - only the donor can confirm
    if not hasattr(request.user, 'participant') or proposition.participant_donateur != request.user.participant:
        messages.error(request, "Accès non autorisé.")
        return redirect('participant_dashboard')
    
    # Can only confirm if the proposition is validated and has a transporter
    if proposition.statut != 'validee' or not proposition.transporteur_assignee:
        messages.error(request, "Cette proposition n'est pas prête pour la remise.")
        return redirect('mes_propositions')
    
    if request.method == 'POST':
        proposition.donator_gives = True
        proposition.save()
        
        # Notify member that items are ready to be added to stock
        if proposition.membre_validateur:
            Notification.objects.create(
                receiver=proposition.membre_validateur,
                proposition=proposition,
                titre=f"Remise confirmée: Proposition #{proposition.id}",
                message=f"Le donateur a confirmé la remise au transporteur. Vous pouvez ajouter ce don au stock."
            )
        
        messages.success(request, f"✅ Remise confirmée pour la proposition #{proposition.id}!")
        return redirect('mes_propositions')
    
    return redirect('mes_propositions')


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import DemandeDon

@login_required
def confirmer_reception_demande(request, demande_id):
    """Allow demandeur to confirm they received their demand"""
    if not hasattr(request.user, 'participant'):
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard')
    
    demande = get_object_or_404(DemandeDon, id=demande_id)
    
    # Check permissions
    if demande.participant_requerant != request.user.participant:
        messages.error(request, "Vous n'êtes pas autorisé à confirmer cette réception.")
        return redirect('mes_demandes')
    
    # Check if demande is ready for confirmation
    if demande.statut != 'terminee':
        messages.error(request, "Cette demande n'est pas encore prête pour confirmation de réception.")
        return redirect('mes_demandes')
    
    if demande.demandeur_confirme_reception:
        messages.info(request, "Vous avez déjà confirmé la réception de cette demande.")
        return redirect('mes_demandes')
    
    # Confirm reception
    demande.demandeur_confirme_reception = True
    demande.save()
    
    messages.success(request, "Réception confirmée avec succès !")
    return redirect('mes_demandes')

# ============ PARTICIPANT VIEWS ============
@login_required
def mes_demandes(request):
    """View all demands by the current participant"""
    if not hasattr(request.user, 'participant'):
        messages.error(request, "Accès non autorisé.")
        return redirect('home')
    
    # Get all demands by this participant
    demandes = DemandeDon.objects.filter(
        participant_requerant=request.user.participant
    ).order_by('-date_demande')
    
    # Handle POST request to terminate a demand
    if request.method == 'POST':
        demande_id = request.POST.get('demande_id')
        action = request.POST.get('action')
        
        if demande_id and action == 'terminer':
            demande = get_object_or_404(DemandeDon, id=demande_id)
            
            # Check if this participant owns the demand
            if demande.participant_requerant == request.user.participant:
                # Terminate the demand
                demande.statut = 'terminee'
                demande.demandeur_confirme_reception = True
                demande.save()
                
                messages.success(request, f"Demande #{demande.id} terminée avec succès !")
                return redirect('mes_demandes')
            else:
                messages.error(request, "Vous n'êtes pas autorisé à terminer cette demande.")
    
    context = {
        'demandes': demandes
    }
    
    return render(request, 'donations/demandes/mes_demandes.html', context)

@login_required
def mes_propositions(request):
    """View all propositions by the current participant"""
    if not hasattr(request.user, 'participant'):
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard')
    
    # Get all propositions by this participant
    propositions = PropositionDon.objects.filter(
        participant_donateur=request.user.participant
    ).order_by('-date_proposition')
    
    # Get associated demands for completed propositions
    for proposition in propositions:
        # Find if there's a demande associated with this proposition
        try:
            proposition.demande_associee = DemandeDon.objects.filter(
                don_attribue__proposition=proposition
            ).first()
        except:
            proposition.demande_associee = None
    
    context = {
        'propositions': propositions
    }
    
    return render(request, 'donations/propositions/mes_propositions.html', context)


@login_required
def proposition_details(request, proposition_id):
    """Detailed view of a specific proposition"""
    proposition = get_object_or_404(PropositionDon, id=proposition_id)
    
    # Security check
    if not hasattr(request.user, 'participant') or proposition.participant_donateur != request.user.participant:
        messages.error(request, "Accès non autorisé.")
        return redirect('mes_propositions')
    
    # Get associated demande if exists
    demande_associee = None
    try:
        demande_associee = DemandeDon.objects.filter(don_attribue__proposition=proposition).first()
    except:
        pass
    
    context = {
        'proposition': proposition,
        'demande_associee': demande_associee
    }
    
    return render(request, 'donations/propositions/proposition_details.html', context)


@login_required
def mes_missions_acceptees(request):
    
    # Check if user is a participant
   
    
    # Get propositions where the participant is the donor
    propositions = PropositionDon.objects.filter(
        participant_donateur=request.user
    ).exclude(statut='en_attente').order_by('-date_proposition')
    
    # Get demands assigned to this participant (if they're also a transporter)
    demandes = DemandeDon.objects.none()
    if hasattr(request.user, 'transporteur'):
        demandes = DemandeDon.objects.filter(
            transporteur_livraison=request.user
        ).exclude(statut='en_attente').order_by('-date_demande')
    
    context = {
        'propositions': propositions,
        'demandes': demandes
    }
    
    return render(request, 'donations/propositions/mes_missions_acceptees.html', context)


@login_required
def demandes_de_recuperateur(request, user_id):
    """Show all donation requests for a specific participant."""
    participant_recurant = get_object_or_404(Participant, id=user_id)
    demandes = participant_recurant.demandes_dons.all()
    return render(
        request,
        "donations/demandes/demandes_requperateur.html",
        {"demandes": demandes}
    )


# ============ STOCK REMOVAL ============
@login_required
def retirer_du_stock(request, don_id):
    """Remove a don from stock after reception confirmation."""
    don = get_object_or_404(Don, id=don_id)
    
    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('home')
    
    # Check if associated demande has confirmed reception
    demande = DemandeDon.objects.filter(don_attribue=don, demandeur_confirme_reception=True).first()
    
    if not demande:
        messages.warning(request, "Le bénéficiaire n'a pas encore confirmé la réception.")
        return redirect('membre_dashboard')
    
    # Remove from stock (mark as donné)
    don.statut = 'donne'
    don.date_don = timezone.now().date()
    don.save()
    
    messages.success(request, f"Don #{don.reference} retiré du stock et marqué comme donné.")
    return redirect('membre_dashboard')