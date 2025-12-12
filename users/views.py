from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm , TransporteurCreateForm,MembreCreateForm,AdminCreateForm
from .models import User, Participant , Admin , Membre , Transporteur
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.shortcuts import redirect
from functools import wraps
from django.contrib.auth.decorators import login_required
from donations.models import DemandeDon , PropositionDon
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from donations.models import PropositionDon,Don
from users.models import Transporteur
from notifications.models import Notification
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from donations.models import Don
from django.http import JsonResponse
from django.contrib.auth import get_user_model

User = get_user_model()

def get_user(request, user_id):
    try:
        u = User.objects.get(id=user_id)
        return JsonResponse({
            "id": u.id,
            "username": u.username,
            "type": u.user_type,
        })
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)








def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.user_type != "admin":
            return redirect("home")  # or raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def home(request):
    return render(request, "base/home.html")



def logout_view(request):
    logout(request)   # clears the session
    return redirect("login")   # redirect to login page after logout



def getAvailableTransporteurs():
    return Transporteur.objects.filter(disponibilite=True)


def register_view(request):
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
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = AuthenticationForm()
    return render(request, "users/auth/login.html", {"form": form})


@admin_required
def create_admin(request):
    if request.method == "POST":
        form = AdminCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.user_type = "admin"
            user.save()
            Admin.objects.create(id=user.id, username=user.username, email=user.email, user_type="admin", password=user.password)
            return redirect("home")
    else:
        form = AdminCreateForm()
    return render(request, "users/admin/create_admin.html", {"form": form})


@admin_required
def create_membre(request):
    if request.method == "POST":
        form = MembreCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.user_type = "membre"
            user.save()
            Membre.objects.create(id=user.id, username=user.username, email=user.email, user_type="membre", password=user.password)
            return redirect("home")
    else:
        form = MembreCreateForm()
    return render(request, "users/admin/create_membre.html", {"form": form})


@admin_required
def create_transporteur(request):
    if request.method == "POST":
        form = TransporteurCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.user_type = "transporteur"
            user.save()
            Transporteur.objects.create(id=user.id, username=user.username, email=user.email, user_type="transporteur", password=user.password)
            return redirect("home")
    else:
        form = TransporteurCreateForm()
    return render(request, "users/admin/create_transporteur.html", {"form": form})


from donations.models import Don

@login_required
def membre_dashboard(request):
    demandes = DemandeDon.objects.all()
    propositions = PropositionDon.objects.all()
    transporteurs = Transporteur.objects.all()
    dons = Don.objects.all()   # ✅ récupérer les dons

    return render(request, "dashboards/membre.html", {
        "demandes": demandes,
        "propositions": propositions,
        "transporteurs": transporteurs,
        "dons": dons,
    })




@login_required
def transporteur_notifications(request):
    if not hasattr(request.user, 'transporteur'):
        messages.error(request, "Accès réservé aux transporteurs.")
        return redirect('home')

    notifications = request.user.transporteur.notifications.order_by('-date_creation')
    return render(request, 'notifications/transporteur/notifications.html', {'notifications': notifications})




@login_required
def assign_transporteur_view(request, proposition_id):
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
            proposition.statut = "validee"  # still valid until transporteur responds
            proposition.date_validation = timezone.now()
            proposition.membre_validateur = request.user.membre
            proposition.save()

            # Create notification for transporteur
            Notification.objects.create(
                receiver=transporteur,
                proposition=proposition,
                titre=f"Nouvelle mission: Proposition #{proposition.id}",
                message="Vous avez été assigné pour ramasser ce don."
            )

            messages.success(request, f"Transporteur {transporteur} assigné à la proposition #{proposition.id}.")
            return redirect('membre_dashboard')  # ✅ always return something

    # If GET request, show a form to choose transporteur
    available_transporteurs = getAvailableTransporteurs()
    return render(request, "donations/propositions/assign_transporteur.html", {
        "proposition": proposition,
        "transporteurs": available_transporteurs
    })




@login_required
def transporteur_reponse(request, proposition_id):
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


@login_required
def notification_detail(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id)
    demande=notif.demande
    if request.method=="POST":
        action=request.POST.get("action")
        if action=="marquer comme terminer":
            demande.statut="terminee"
            demande.transporteur_confirme=True
            demande.save()
            messages.success(request,f"Demande #{demande.id} marquée comme terminée.")
            return redirect('transporteur_dashboard')

    notif.lu = True
    notif.save()

    return render(request, 'notifications/transporteur/notification_detail.html', {
        'notif': notif,
        'proposition': notif.proposition,
    })



@login_required
def transporteur_dashboard(request):
    if not hasattr(request.user, 'transporteur'):
        messages.error(request, "Accès réservé aux transporteurs.")
        return redirect('home')

    # Show only propositions accepted by this transporteur
    propositions = PropositionDon.objects.filter(
        transporteur_assignee=request.user.transporteur,
        transporteur_statut="acceptee"
    ).order_by('-date_proposition')

    return render(request, 'dashboards/transporteur.html', {
        'propositions': propositions
    })


@login_required
def terminer_proposition(request, proposition_id):
    proposition = get_object_or_404(PropositionDon, id=proposition_id)

    # Ensure only the assigned transporteur can mark it as finished
    if not hasattr(request.user, 'transporteur') or proposition.transporteur_assignee != request.user.transporteur:
        messages.error(request, "Vous n'êtes pas autorisé à terminer cette mission.")
        return redirect('transporteur_dashboard')

    proposition.statut = "terminee"   # make sure "terminee" exists in STATUT_CHOICES
    proposition.save()

    messages.success(request, f"Proposition #{proposition.id} marquée comme terminée.")
    return redirect('transporteur_dashboard')








