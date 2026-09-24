# models.py
import uuid
from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone


# =========================================================
# UTILISATEUR
# =========================================================
class UtilisateurManager(BaseUserManager):
    def create_user(self, telephone, password=None, **extra_fields):
        if not telephone:
            raise ValueError("Le numéro de téléphone est obligatoire.")
        user = self.model(telephone=telephone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, telephone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(telephone, password, **extra_fields)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    class Frequence(models.TextChoices):
        MENSUELLE = "mensuelle", "Mensuelle"
        QUINZAINE = "quinzaine", "Quinzaine"
        HEBDOMADAIRE = "hebdomadaire", "Hebdomadaire"

    class Devise(models.TextChoices):
        XAF = "XAF", "XAF"
        XOF = "XOF", "XOF"
        USD = "USD", "USD"

    class Abonnement(models.TextChoices):
        ESSAI = "essai", "Essai"
        GRATUIT = "gratuit", "Gratuit"
        PAYANT = "payant", "Payant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom_complet = models.CharField(max_length=150)
    telephone = models.CharField(max_length=30, unique=True)
    email = models.EmailField(blank=True, null=True)
    frequence_revenu = models.CharField(
        max_length=20, choices=Frequence.choices, default=Frequence.MENSUELLE
    )
    # Jour du mois (1-31) si mensuelle/quinzaine, jour de semaine (0-6) si hebdomadaire
    date_paie_habituelle = models.PositiveSmallIntegerField(default=25)
    devise = models.CharField(max_length=5, choices=Devise.choices, default=Devise.XAF)
    statut_abonnement = models.CharField(
        max_length=15, choices=Abonnement.choices, default=Abonnement.ESSAI
    )
    date_fin_essai = models.DateField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "telephone"
    REQUIRED_FIELDS = ["nom_complet"]

    objects = UtilisateurManager()

    def __str__(self):
        return self.nom_complet

    # ---------- Solde calculé à la volée (décision actée §6) ----------
    @property
    def solde(self):
        revenus = self.transactions.filter(type=Transaction.Type.REVENU).aggregate(
            total=Sum("montant")
        )["total"] or Decimal("0")
        depenses = self.transactions.filter(type=Transaction.Type.DEPENSE).aggregate(
            total=Sum("montant")
        )["total"] or Decimal("0")
        return revenus - depenses

    # ---------- Gestion de l'essai (point à trancher §9) ----------
    def verifier_fin_essai(self):
        """Bascule automatiquement essai -> gratuit à la fin de l'essai."""
        if (
            self.statut_abonnement == self.Abonnement.ESSAI
            and self.date_fin_essai
            and self.date_fin_essai < timezone.now().date()
        ):
            self.statut_abonnement = self.Abonnement.GRATUIT
            self.save(update_fields=["statut_abonnement"])


# =========================================================
# SOURCES DE REVENU
# =========================================================
class SourceRevenu(models.Model):
    class Frequence(models.TextChoices):
        MENSUELLE = "mensuelle", "Mensuelle"
        QUINZAINE = "quinzaine", "Quinzaine"
        HEBDOMADAIRE = "hebdomadaire", "Hebdomadaire"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name="sources_revenu"
    )
    nom = models.CharField(max_length=150)
    montant_attendu = models.DecimalField(max_digits=14, decimal_places=2)
    frequence = models.CharField(
        max_length=20, choices=Frequence.choices, default=Frequence.MENSUELLE
    )
    jour_habituel = models.PositiveSmallIntegerField(default=25)
    # Choix V1 : pas de table d'historique des versements (décision actée §6)
    dernier_montant_recu = models.DecimalField(
        max_digits=14, decimal_places=2, blank=True, null=True
    )
    dernier_date_recue = models.DateField(blank=True, null=True)
    actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom


# =========================================================
# CATÉGORIES
# =========================================================
class Categorie(models.Model):
    class Type(models.TextChoices):
        REVENU = "revenu", "Revenu"
        DEPENSE = "depense", "Dépense"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="categories_personnelles",
        blank=True,
        null=True,
    )
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=Type.choices)
    icone = models.CharField(max_length=40, blank=True)
    est_predefinie = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Catégories"
        ordering = ["type", "nom"]
        constraints = [
            models.UniqueConstraint(
                fields=["utilisateur", "nom", "type"],
                name="unique_categorie_par_utilisateur_et_type",
            )
        ]

    def __str__(self):
        return self.nom


# =========================================================
# TRANSACTIONS
# =========================================================
class Transaction(models.Model):
    class Type(models.TextChoices):
        REVENU = "revenu", "Revenu"
        DEPENSE = "depense", "Dépense"

    class Canal(models.TextChoices):
        CASH = "cash", "Cash"
        MOBILE_MONEY = "mobile_money", "Mobile Money"
        BANQUE = "banque", "Banque"
        AUTRE = "autre", "Autre"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name="transactions"
    )
    categorie = models.ForeignKey(
        Categorie, on_delete=models.PROTECT, related_name="transactions"
    )
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    type = models.CharField(max_length=10, choices=Type.choices)
    date = models.DateField(default=timezone.now)
    canal_declaratif = models.CharField(
        max_length=20, choices=Canal.choices, default=Canal.CASH
    )
    note = models.CharField(max_length=255, blank=True)
    source_revenu = models.ForeignKey(
        SourceRevenu,
        on_delete=models.SET_NULL,
        related_name="transactions",
        blank=True,
        null=True,
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-cree_le"]

    def __str__(self):
        return f"{self.type} — {self.montant}"

    def clean(self):
        # Cohérence type / catégorie
        if self.categorie_id and self.type and self.categorie.type != self.type:
            raise ValidationError(
                "Le type de la transaction doit correspondre au type de la catégorie."
            )
        # source_revenu uniquement si type = revenu
        if self.source_revenu_id and self.type != self.Type.REVENU:
            raise ValidationError(
                "Une source de revenu ne peut être liée qu'à une transaction de type revenu."
            )
        # source_revenu doit appartenir au même utilisateur
        if (
            self.source_revenu_id
            and self.utilisateur_id
            and self.source_revenu.utilisateur_id != self.utilisateur_id
        ):
            raise ValidationError(
                "La source de revenu doit appartenir au même utilisateur."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        # Mise à jour du dernier versement reçu sur la source liée
        if self.source_revenu_id and self.type == self.Type.REVENU:
            SourceRevenu.objects.filter(pk=self.source_revenu_id).update(
                dernier_montant_recu=self.montant,
                dernier_date_recue=self.date,
            )


# =========================================================
# OBJECTIFS D'ÉPARGNE
# =========================================================
class ObjectifEpargne(models.Model):
    class Statut(models.TextChoices):
        EN_COURS = "en_cours", "En cours"
        ATTEINT = "atteint", "Atteint"
        ABANDONNE = "abandonne", "Abandonné"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name="objectifs_epargne"
    )
    nom = models.CharField(max_length=150)
    montant_cible = models.DecimalField(max_digits=14, decimal_places=2)
    montant_actuel = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0")
    )
    date_cible = models.DateField(blank=True, null=True)
    statut = models.CharField(
        max_length=15, choices=Statut.choices, default=Statut.EN_COURS
    )
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    @property
    def progression(self):
        if not self.montant_cible:
            return 0
        return min(100, float((self.montant_actuel / self.montant_cible) * 100))

    def recalculer_montant_actuel(self):
        """Recalcule montant_actuel à partir des contributions (source de vérité)."""
        total = self.contributions.aggregate(total=Sum("montant"))["total"] or Decimal("0")
        self.montant_actuel = total
        if total >= self.montant_cible and self.statut == self.Statut.EN_COURS:
            self.statut = self.Statut.ATTEINT
        self.save(update_fields=["montant_actuel", "statut", "modifie_le"])

    def __str__(self):
        return self.nom


class ContributionEpargne(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objectif_epargne = models.ForeignKey(
        ObjectifEpargne, on_delete=models.CASCADE, related_name="contributions"
    )
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.montant} — {self.objectif_epargne.nom}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mise à jour automatique du montant_actuel de l'objectif
        self.objectif_epargne.recalculer_montant_actuel()

    def delete(self, *args, **kwargs):
        objectif = self.objectif_epargne
        super().delete(*args, **kwargs)
        objectif.recalculer_montant_actuel()


# =========================================================
# DETTES ET CRÉDITS INFORMELS
# =========================================================
class Dette(models.Model):
    class Sens(models.TextChoices):
        JE_DOIS = "je_dois", "Je dois"
        ON_ME_DOIT = "on_me_doit", "On me doit"

    class Statut(models.TextChoices):
        EN_COURS = "en_cours", "En cours"
        SOLDE = "solde", "Soldé"
        EN_RETARD = "en_retard", "En retard"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name="dettes"
    )
    sens = models.CharField(max_length=15, choices=Sens.choices)
    personne = models.CharField(max_length=150)
    montant_initial = models.DecimalField(max_digits=14, decimal_places=2)
    montant_restant = models.DecimalField(max_digits=14, decimal_places=2)
    date_creation = models.DateField(default=timezone.now)
    date_echeance = models.DateField(blank=True, null=True)
    statut = models.CharField(
        max_length=15, choices=Statut.choices, default=Statut.EN_COURS
    )
    note = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.personne} — {self.montant_restant}"

    def recalculer_montant_restant(self):
        """Recalcule le montant restant et met à jour le statut."""
        total_rembourse = self.remboursements.aggregate(total=Sum("montant"))["total"] or Decimal("0")
        self.montant_restant = max(Decimal("0"), self.montant_initial - total_rembourse)

        if self.montant_restant <= 0:
            self.statut = self.Statut.SOLDE
        elif self.date_echeance and self.date_echeance < timezone.now().date():
            self.statut = self.Statut.EN_RETARD
        else:
            self.statut = self.Statut.EN_COURS

        self.save(update_fields=["montant_restant", "statut"])


class RemboursementDette(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dette = models.ForeignKey(
        Dette, on_delete=models.CASCADE, related_name="remboursements"
    )
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.montant} — {self.dette.personne}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.dette.recalculer_montant_restant()

    def delete(self, *args, **kwargs):
        dette = self.dette
        super().delete(*args, **kwargs)
        dette.recalculer_montant_restant()