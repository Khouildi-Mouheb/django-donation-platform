from django.urls import path
from .views import (
    register_view, login_view, home, logout_view,
    create_admin, create_membre, create_transporteur,
    membre_dashboard, assign_transporteur_view,
    transporteur_notifications, notification_detail,
    transporteur_reponse, transporteur_dashboard,
    terminer_proposition,   # ✅ make sure this is imported
)

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('', home, name='home'),
    path("logout/", logout_view, name="logout"),

    # Admin-only account creation
    path("create-admin/", create_admin, name="create_admin"),
    path("create-membre/", create_membre, name="create_membre"),
    path("create-transporteur/", create_transporteur, name="create_transporteur"),

    # Membre dashboard
    path('dashboard/membre/', membre_dashboard, name='membre_dashboard'),
    path('dashboard/membre/proposition/<int:proposition_id>/assign/', assign_transporteur_view, name='assign_transporteur'),

    # Transporteur notifications
    path('dashboard/transporteur/notifications/', transporteur_notifications, name='transporteur_notifications'),
    path('dashboard/transporteur/notifications/<int:notif_id>/', notification_detail, name='notification_detail'),

    # Transporteur responds to a proposition (accept/refuse)
    path("dashboard/transporteur/proposition/<int:proposition_id>/reponse/", transporteur_reponse, name="transporteur_reponse"),

    # Transporteur dashboard: list of accepted propositions
    path("dashboard/transporteur/missions/", transporteur_dashboard, name="transporteur_dashboard"),

    # Transporteur marks a proposition as terminée
    path("dashboard/transporteur/proposition/<int:proposition_id>/terminer/", terminer_proposition, name="terminer_proposition"),
    

]


