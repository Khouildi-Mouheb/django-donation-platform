"""
views.py - Main views for the donation management system
Organized by functionality with consistent structure
"""

# ============ IMPORTS ============
# Django core
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse

# Decorators
from functools import wraps

# Local models and forms
from .forms import RegisterForm, TransporteurCreateForm, MembreCreateForm, AdminCreateForm
from .models import User, Participant, Admin, Membre, Transporteur
from donations.models import DemandeDon, PropositionDon, Don
from notifications.models import Notification


# ============ CONSTANTS & UTILITIES ============
User = get_user_model()


# ============ DECORATORS ============
def admin_required(view_func):
    """Custom decorator to restrict access to admin users only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.user_type != "admin":
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return wrapper


# ============ HELPER FUNCTIONS ============
def getAvailableTransporteurs():
    """Get all available transporters."""
    return Transporteur.objects.filter(disponibilite=True)


# ============ AUTHENTICATION VIEWS ============
def home(request):
    """Home page view."""
    return render(request, "base/home.html")


def logout_view(request):
    """Logout user and redirect to login page."""
    logout(request)
    return redirect("login")


def register_view(request):
    """Handle participant registration."""
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.set_password(form.cleaned_data["password"])
            participant.user_type = "participant"
            participant.save()
            login(request, participant)
            return redirect("home")
    else:
        form = RegisterForm()
    return render(request, "users/auth/register.html", {"form": form})


def login_view(request):
    """Handle user login."""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = AuthenticationForm()
    return render(request, "users/auth/login.html", {"form": form})


# ============ ADMIN MANAGEMENT VIEWS ============
@admin_required
def create_admin(request):
    """Create a new admin user (admin only)."""
    if request.method == "POST":
        form = AdminCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.user_type = "admin"
            user.save()
            Admin.objects.create(
                id=user.id,
                username=user.username,
                email=user.email,
                user_type="admin",
                password=user.password
            )
            return redirect("home")
    else:
        form = AdminCreateForm()
    return render(request, "users/admin/create_admin.html", {"form": form})


@admin_required
def create_membre(request):
    """Create a new member user (admin only)."""
    if request.method == "POST":
        form = MembreCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.user_type = "membre"
            user.save()
            Membre.objects.create(
                id=user.id,
                username=user.username,
                email=user.email,
                user_type="membre",
                password=user.password
            )
            return redirect("home")
    else:
        form = MembreCreateForm()
    return render(request, "users/admin/create_membre.html", {"form": form})


@admin_required
def create_transporteur(request):
    """Create a new transporter user (admin only)."""
    if request.method == "POST":
        form = TransporteurCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.user_type = "transporteur"
            user.save()
            Transporteur.objects.create(
                id=user.id,
                username=user.username,
                email=user.email,
                user_type="transporteur",
                password=user.password
            )
            return redirect("home")
    else:
        form = TransporteurCreateForm()
    return render(request, "users/admin/create_transporteur.html", {"form": form})


# ============ DASHBOARD VIEWS ============
@login_required
def membre_dashboard(request):
    """Member dashboard showing donations, requests, and transporters."""
    demandes = DemandeDon.objects.all()
    propositions = PropositionDon.objects.all()
    transporteurs = Transporteur.objects.all()
    dons = Don.objects.all()

    return render(request, "dashboards/membre.html", {
        "demandes": demandes,
        "propositions": propositions,
        "transporteurs": transporteurs,
        "dons": dons,
    })


@login_required
def transporteur_dashboard(request):
    """Transporter dashboard showing assigned missions."""
    if not hasattr(request.user, 'transporteur'):
        messages.error(request, "Accès réservé aux transporteurs.")
        return redirect('home')

    # Get propositions where transporteur is assigned and accepted
    propositions = PropositionDon.objects.filter(
        transporteur_assignee=request.user.transporteur,
        transporteur_statut='acceptee'
    ).order_by('-date_proposition')

    # Get demandes where transporteur is assigned
    demandes = DemandeDon.objects.filter(
        transporteur_livraison=request.user.transporteur
    ).exclude(statut='annulee').order_by('-date_demande')

    return render(request, "dashboards/transporteur.html", {
        "propositions": propositions,
        "demandes": demandes
    })


# ============ NOTIFICATION VIEWS ============
@login_required
def transporteur_notifications(request):
    """Display notifications for the current transporter."""
    if not hasattr(request.user, 'transporteur'):
        messages.error(request, "Accès réservé aux transporteurs.")
        return redirect('home')

    notifications = request.user.transporteur.notifications.order_by('-date_creation')
    return render(request, 'notifications/transporteur/notifications.html', 
                 {'notifications': notifications})


@login_required
def notification_detail(request, notif_id):
    """Display details of a specific notification."""
    notif = get_object_or_404(Notification, id=notif_id)
    proposition = notif.proposition
    demande = notif.demande

    # Ensure the notification belongs to the current user
    if notif.receiver != request.user:
        messages.error(request, "Accès non autorisé.")
        return redirect('transporteur_notifications')

    # Handle demande notifications
    if demande:
        if request.method == "POST":
            action = request.POST.get("action")
            if action == "marquer comme terminer":
                demande.statut = "terminee"
                demande.transporteur_confirme = True
                demande.save()
                messages.success(request, f"Demande #{demande.id} marquée comme terminée.")
                return redirect('transporteur_dashboard')
            elif action == "accepter":
                demande.transporteur_confirme = True
                demande.statut = "en_livraison"
                demande.save()
                messages.success(request, f"Vous avez accepté la mission pour demande #{demande.id}.")
                return redirect('transporteur_dashboard')
            elif action == "refuser":
                demande.transporteur_confirme = False
                demande.transporteur_livraison = None
                demande.statut = "validee"
                demande.save()
                messages.warning(request, f"Vous avez refusé la mission pour demande #{demande.id}.")
                return redirect('transporteur_dashboard')

        notif.lu = True
        notif.save()

        return render(request, 'notifications/transporteur/notification_detail.html', {
            'notif': notif,
            'demande': demande,
        })

    # Handle proposition notifications
    else:
        if request.method == "POST":
            action = request.POST.get("action")
            action2 = request.POST.get('marquer comme terminer')
            if action == "accepter":
                proposition.transporteur_statut = 'acceptee'
                proposition.save()
                messages.success(request, f"Proposition #{proposition.id} marquée comme acceptee.")
                return redirect('transporteur_dashboard')
            if action2 == "marquer comme terminer":
                proposition.statut = 'terminee'
                proposition.save()
                return redirect('transporteur_dashboard')
        notif.lu = True
        notif.save()

        return render(request, 'notifications/transporteur/notification_detail.html', {
            'notif': notif,
            'proposition': proposition,
        })


# ============ ASSIGNMENT & MISSION VIEWS ============
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
                message="Vous avez été assigné pour ramasser ce don.",
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


@login_required
def transporteur_reponse(request, proposition_id):
    """Handle transporter response to an assigned mission."""
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
            proposition.save()
            messages.warning(request, f"Vous avez refusé la mission pour Proposition #{proposition.id}.")
        else:
            messages.error(request, "Action non reconnue.")

    return redirect('transporteur_notifications')


# ============ COMPLETION ACTIONS ============
@login_required
def terminer_proposition(request, proposition_id):
    """Mark a proposition as completed by the assigned transporter."""
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    # Ensure only the assigned transporteur can mark it as finished
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
        demande.save()
        messages.success(request, f"Demande #{demande.id} marquée comme terminée.")

    return redirect('transporteur_dashboard')


# ============ PARTICIPANT VIEWS ============
def demandes_de_recuperateur(request, user_id):
    """Show all donation requests for a specific participant."""
    participant_recurant = Participant.objects.get(id=user_id)
    demandes = participant_recurant.demandes_dons.all()
    return render(
        request,
        "donations/demandes/demandes_requperateur.html",
        {"demandes": demandes}
    )


def demandeur_confirme_reception(request):
    """Placeholder for donor confirmation of receipt."""
    pass


# ============ API VIEWS ============
def get_user(request, user_id):
    """API endpoint to get user information."""
    try:
        u = User.objects.get(id=user_id)
        return JsonResponse({
            "id": u.id,
            "username": u.username,
            "type": u.user_type,
        })
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)