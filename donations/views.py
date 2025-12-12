from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import PropositionDonForm , DemandeDonForm
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from .models import DemandeDon
from .models import PropositionDon , Don
from users.views import getAvailableTransporteurs
from users.models import Transporteur


@login_required
def stock_list(request):
    # Tous les dons en stock
    dons = Don.objects.all()
    return render(request, "donations/stock/stock_list.html", {"dons": dons})


@login_required
def participant_donations(request):
    # Vérifier que l'utilisateur est bien un participant
    if not hasattr(request.user, 'participant'):
        messages.error(request, "Accès réservé aux participants.")
        return redirect('home')

    propositions = PropositionDon.objects.filter(participant_donateur=request.user.participant)
    return render(request, "dashboards/participant.html", {"propositions": propositions})


@login_required
def confirmer_remise_donateur(request, proposition_id):
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    if not hasattr(request.user, 'participant') or proposition.participant_donateur != request.user.participant:
        messages.error(request, "Vous n'êtes pas autorisé à confirmer cette remise.")
        return redirect('home')

    proposition.donator_gives = True
    proposition.save()
    messages.success(request, f"Vous avez confirmé la remise du don #{proposition.id}.")
    return redirect('participant_donations')

def participant_required(view_func):
    """Decorator to ensure only participants can access"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.user_type != "participant":
            messages.error(request, "Seuls les participants peuvent proposer un don.")
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return wrapper


@participant_required
def create_proposition(request):
    if request.method == "POST":
        form = PropositionDonForm(request.POST, request.FILES)
        if form.is_valid():
            proposition = form.save(commit=False)
            proposition.statut = "en_attente"
            # Link the logged-in participant to the proposition
            proposition.participant_donateur = request.user.participant
            proposition.save()
            messages.success(request, "Votre proposition de don a été créée avec succès.")
            return redirect("home")  # you can define a list view later
    else:
        form = PropositionDonForm()
    return render(request, "donations/propositions/create_proposition.html", {"form": form})






@login_required
def valider_demande(request, demande_id):
    demande = get_object_or_404(DemandeDon, id=demande_id)

    # Ensure only Membre role can validate/refuse
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
def proposition_detail(request, proposition_id):
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('home')

    return render(request, 'donations/propositions/proposition_detail.html', {
        'proposition': proposition
    })


@login_required
def terminer_proposition(request, proposition_id):
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    if not hasattr(request.user, 'transporteur') or proposition.transporteur_assignee != request.user.transporteur:
        messages.error(request, "Vous n'êtes pas autorisé à terminer cette mission.")
        return redirect('transporteur_dashboard')

    proposition.statut = "terminee"
    proposition.save()
    messages.success(request, f"Proposition #{proposition.id} marquée comme terminée.")
    return redirect('transporteur_dashboard')


@login_required
def ajouter_au_stock(request, proposition_id):
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('home')

    # ✅ Prevent duplicate Don creation
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
    messages.success(request, f"Proposition #{proposition.id} ajoutée au stock comme Don #{don.reference}.")
    return redirect('membre_dashboard')


@participant_required
def create_demande(request):
    if request.method == "POST":
        form = DemandeDonForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.statut = "en_attente"
            # Link the logged-in participant to the proposition
            demande.participant_requerant = request.user.participant
            demande.save()
            messages.success(request, "Votre proposition de don a été créée avec succès.")
            return redirect("home")  # you can define a list view later
    else:
        form = DemandeDonForm()
    return render(request, "donations/demandes/create_demande.html", {"form": form})



def demande_detail(request , demande_id):
    demande=get_object_or_404(DemandeDon , id=demande_id)
    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('home')

    return render(request, 'donations/demandes/demande_detail.html', {
        'demande': demande
    })


@login_required
def traiter_demande(request,demande_id):
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



def getDemandeRelatedItems(request , demande_id):
    demande=get_object_or_404(DemandeDon, id=demande_id)
    categorie=demande.categorie_recherchee
    realted_items=Don.objects.filter(categorie=categorie)
    return render(request, "donations/demandes/related_items.html",{"related_items":realted_items})

from notifications.models import Notification

@login_required
def assign_transporteur_demande(request, demande_id):
    demande = get_object_or_404(DemandeDon, id=demande_id)

    # Ensure only Membre role can assign
    if not hasattr(request.user, 'membre'):
        messages.error(request, "Accès réservé aux membres.")
        return redirect('membre_dashboard')

    if request.method == "POST":
        transporteur_id = request.POST.get("transporteur_id")
        if transporteur_id:
            transporteur = get_object_or_404(Transporteur, id=transporteur_id)
            demande.transporteur_assignee = transporteur
            demande.statut = "validee"  # still valid until transporteur responds
            demande.date_validation = timezone.now()
            demande.membre_validateur = request.user.membre
            demande.save()

            # Create notification for transporteur
            Notification.objects.create(
                receiver=transporteur,
                demande=demande,
                titre=f"Nouvelle mission: Proposition #{demande.id}",
                message="Vous avez été assigné pour twasseel ce don."
            )

            messages.success(request, f"Transporteur {transporteur} assigné à la proposition #{demande.id}.")
            return redirect('membre_dashboard')  # ✅ always return something

    # If GET request, show a form to choose transporteur
    available_transporteurs = getAvailableTransporteurs()
    return render(request, "donations/demandes/assign_transporteur.html", {
        "proposidemandetion": demande,
        "transporteurs": available_transporteurs
    })

