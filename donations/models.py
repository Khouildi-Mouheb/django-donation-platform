from django.db import models
from django.utils import timezone
from users.models import Participant, Membre, Transporteur   # import roles from users app


class CategorieObjet(models.Model):
    """Categories for organizing items"""
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sous_categories'
    )

    class Meta:
        verbose_name = "Catégorie d'objet"
        verbose_name_plural = "Catégories d'objets"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class PropositionDon(models.Model):


    """Donor Participant suggests a donation"""
    ETAT_CHOICES = (
        ('neuf', 'Neuf'),
        ('bon_etat', 'Bon état'),
        ('etat_moyen', 'État moyen'),
        ('a_reparer', 'À réparer'),
    )

    STATUT_CHOICES = (
    ('en_attente', 'En attente de validation'),
    ('validee', 'Validée'),
    ('refusee', 'Refusée'),
    ('annulee', 'Annulée'),
    ('ramassee', 'Ramassée par transporteur'),
    ('terminee', 'Terminée'),
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    


    participant_donateur = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='propositions_dons'
    )
    date_proposition = models.DateTimeField(auto_now_add=True)

    categorie = models.ForeignKey(CategorieObjet, on_delete=models.SET_NULL, null=True, blank=True)
    type_materiel = models.CharField(max_length=200)
    quantite = models.IntegerField(default=1)
    description = models.TextField()
    etat = models.CharField(max_length=20, choices=ETAT_CHOICES, default='bon_etat')
    photos = models.ImageField(upload_to='propositions/dons/', blank=True, null=True)

    adresse_ramassage = models.TextField()
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=10)
    disponibilite_ramassage = models.TextField(help_text="Disponibilités pour le ramassage")

    TRANSPORTEUR_CHOICES = (
        ('en_attente', 'En attente de réponse'),
        ('acceptee', 'Acceptée par transporteur'),
        ('refusee', 'Refusée par transporteur'),
    )

    transporteur_statut = models.CharField(
        max_length=20,
        choices=TRANSPORTEUR_CHOICES,
        default='en_attente'
    )
    raison_refus_transporteur = models.TextField(blank=True)

    date_validation = models.DateTimeField(null=True, blank=True)
    membre_validateur = models.ForeignKey(Membre, on_delete=models.SET_NULL, null=True, blank=True)
    raison_refus = models.TextField(blank=True)

    transporteur_assignee = models.ForeignKey(Transporteur, on_delete=models.SET_NULL, null=True, blank=True)
    date_ramassage = models.DateField(null=True, blank=True)
    heure_ramassage = models.TimeField(null=True, blank=True)
    transporteur_recoit = models.BooleanField(default=False)  # ✅ Transporter confirms they received from donor
    transporteur_livre = models.BooleanField(default=False)  # ✅ Transporter confirms they delivered to receiver
    donator_gives = models.BooleanField(default=False)  # ✅


    class Meta:
        verbose_name = "Proposition de don"
        verbose_name_plural = "Propositions de dons"
        ordering = ['-date_proposition']

    def __str__(self):
        return f"Proposition #{self.id} - {self.type_materiel}"


class Don(models.Model):
    STATUT_CHOICES = (
        ('en_stock', 'En stock'),
        ('garde_meuble', 'Garde Meuble'),
        ('en_depot_vente', 'En dépôt-vente'),
        ('reserve', 'Réservé'),
        ('donne', 'Donné'),
        ('vendu', 'Vendu'),
        ('perime', 'Périmé/Détruit'),
    )

    proposition = models.OneToOneField(PropositionDon, on_delete=models.CASCADE, related_name='don_realise')

    reference = models.CharField(max_length=50, unique=True, blank=True)
    categorie = models.ForeignKey(CategorieObjet, on_delete=models.SET_NULL, null=True, blank=True)
    type_materiel = models.CharField(max_length=200)
    quantite = models.IntegerField(default=1)
    description = models.TextField()
    etat = models.CharField(max_length=20, choices=PropositionDon.ETAT_CHOICES, default='bon_etat')
    photos = models.ImageField(upload_to='dons/', blank=True, null=True)

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_stock')
    date_entree_stock = models.DateTimeField(auto_now_add=True)
    lieu_stockage = models.CharField(max_length=100, blank=True)

    valeur_estimee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    prix_vente = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    date_vente = models.DateField(null=True, blank=True)
    acheteur = models.CharField(max_length=255, blank=True)

    date_don = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Don"
        verbose_name_plural = "Dons"
        ordering = ['-date_entree_stock']

    def __str__(self):
        ref = self.reference if self.reference else f"Don-{self.id}"
        return f"{ref} - {self.type_materiel}"

    def save(self, *args, **kwargs):
        if not self.reference:
        # Generate reference before saving
            self.reference = f"DON-{timezone.now().year}-{self.id or 0:06d}"
        super().save(*args, **kwargs)

    # If reference was generated with id=0, update after first save
        if self.reference.endswith("000000"):
            self.reference = f"DON-{timezone.now().year}-{self.id:06d}"
            super().save(update_fields=["reference"])



class DemandeDon(models.Model):


    """Participant requests a donation"""
    URGENCE_CHOICES = (
        ('faible', 'Faible'),
        ('moyenne', 'Moyenne'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    )

    participant_requerant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='demandes_dons'
    )
    date_demande = models.DateTimeField(auto_now_add=True)

    categorie_recherchee = models.ForeignKey(CategorieObjet, on_delete=models.SET_NULL, null=True, blank=True)
    type_materiel = models.CharField(max_length=200)
    description_besoin = models.TextField()
    quantite_desiree = models.IntegerField(default=1)
    urgence = models.CharField(max_length=20, choices=URGENCE_CHOICES, default='moyenne')

    STATUT_CHOICES = (
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours de traitement'),
        ('validee', 'Validée'),
        ('refusee', 'Refusée'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    date_validation = models.DateTimeField(null=True, blank=True)
    membre_validateur = models.ForeignKey(Membre, on_delete=models.SET_NULL, null=True, blank=True)
    raison_refus = models.TextField(blank=True)

    adresse_livraison = models.TextField()
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=10)
    disponibilite_livraison = models.TextField(blank=True)
    don_attribue = models.ForeignKey(Don, on_delete=models.SET_NULL, null=True, blank=True, related_name='demandes_attribuees')
    date_attribution = models.DateTimeField(null=True, blank=True)
    transporteur_livraison = models.ForeignKey(Transporteur, on_delete=models.SET_NULL, null=True, blank=True)
    date_livraison = models.DateField(null=True, blank=True)
    transporteur_confirme = models.BooleanField(default=False)
    demandeur_confirme_reception=models.BooleanField(default=False,null=True,blank=True)

    transporteur_date_reponse = models.DateTimeField(null=True, blank=True)
    transporteur_raison_refus = models.TextField(blank=True) 


    class Meta:
        verbose_name = "Demande de don"
        verbose_name_plural = "Demandes de dons"
        ordering = ['urgence', '-date_demande']

    def __str__(self):
        return f"Demande #{self.id} - {self.type_materiel}"

    def setStatus(self):
        self.statut='validee'
