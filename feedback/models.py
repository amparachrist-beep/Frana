from django.db import models

# Create your models here.

import uuid

from django.conf import settings
from django.db import models
from django.db.models import F
from django.utils import timezone


class FeedbackQuestion(models.Model):
    class Fonctionnalite(models.TextChoices):
        GENERAL = "general", "Général"
        TRANSACTIONS = "transactions", "Suivi des transactions"
        COMPTE_A_REBOURS = "compte_a_rebours", "Compte à rebours"
        EPARGNE = "epargne", "Épargne / Objectifs"
        DETTES = "dettes", "Dettes et crédits"

    class TypeReponse(models.TextChoices):
        SATISFACTION = "satisfaction", "👍 / 😐 / 👎"
        CHOIX = "choix", "Choix multiple"
        TEXTE = "texte", "Texte libre"

    class Niveau(models.IntegerChoices):
        RAPIDE = 1, "Niveau 1 — ultra rapide"
        PRECISION = 2, "Niveau 2 — précision"
        COMMENTAIRE = 3, "Niveau 3 — commentaire libre"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(max_length=150)
    question = models.CharField(max_length=255)
    fonctionnalite = models.CharField(max_length=30, choices=Fonctionnalite.choices)
    type_reponse = models.CharField(
        max_length=15, choices=TypeReponse.choices, default=TypeReponse.SATISFACTION
    )
    niveau = models.PositiveSmallIntegerField(choices=Niveau.choices, default=Niveau.RAPIDE)

    # Chaînage niveau 1 -> niveau 2 -> niveau 3 (ex: après un 👎, on affine)
    question_parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="questions_enfants",
        blank=True,
        null=True,
        help_text="Question de niveau supérieur qui déclenche celle-ci (ex: niveau 2 après un 👎 au niveau 1).",
    )
    declenchee_par_reponse = models.CharField(
        max_length=30,
        blank=True,
        help_text="Valeur de réponse du parent qui déclenche cette question (ex: 'non').",
    )
    options_choix = models.JSONField(
        blank=True,
        default=list,
        help_text="Options pour type_reponse='choix', ex: ['Je ne comprends pas', 'C'est compliqué'].",
    )

    # Moteur de déclenchement
    seuil_utilisations = models.PositiveSmallIntegerField(
        default=1,
        help_text="Nombre d'utilisations de la fonctionnalité avant de proposer cette question.",
    )
    delai_jours_inscription = models.PositiveSmallIntegerField(
        default=0,
        help_text="Jours après l'inscription avant de proposer cette question (0 = pas de contrainte).",
    )

    active = models.BooleanField(default=True)
    priorite = models.PositiveSmallIntegerField(default=0, help_text="Plus élevé = affiché en priorité.")
    date_debut = models.DateField(blank=True, null=True)
    date_fin = models.DateField(blank=True, null=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-priorite", "titre"]

    def __str__(self):
        return self.titre

    def est_dans_periode(self):
        aujourd_hui = timezone.now().date()
        if self.date_debut and aujourd_hui < self.date_debut:
            return False
        if self.date_fin and aujourd_hui > self.date_fin:
            return False
        return True


class FeedbackResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks"
    )
    question = models.ForeignKey(FeedbackQuestion, on_delete=models.CASCADE, related_name="reponses")
    reponse = models.CharField(max_length=100)
    commentaire = models.TextField(blank=True)
    version_application = models.CharField(max_length=20, blank=True)
    date_reponse = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_reponse"]

    def __str__(self):
        return f"{self.utilisateur} — {self.question.titre} — {self.reponse}"


class FeatureUsage(models.Model):
    """Compteur d'utilisation par fonctionnalité, alimenté depuis les vues existantes de Frana."""

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usages_fonctionnalites"
    )
    fonctionnalite = models.CharField(max_length=30, choices=FeedbackQuestion.Fonctionnalite.choices)
    compteur = models.PositiveIntegerField(default=0)
    derniere_utilisation = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["utilisateur", "fonctionnalite"],
                name="unique_usage_par_utilisateur_et_fonctionnalite",
            )
        ]

    def __str__(self):
        return f"{self.utilisateur} — {self.fonctionnalite} ({self.compteur})"

    @classmethod
    def incrementer(cls, utilisateur, fonctionnalite):
        usage, _ = cls.objects.get_or_create(utilisateur=utilisateur, fonctionnalite=fonctionnalite)
        usage.compteur = F("compteur") + 1
        usage.save(update_fields=["compteur", "derniere_utilisation"])
        usage.refresh_from_db()
        return usage


class FeedbackAffichage(models.Model):
    """Empêche de reproposer la même question plusieurs fois au même utilisateur."""

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks_affiches"
    )
    question = models.ForeignKey(FeedbackQuestion, on_delete=models.CASCADE, related_name="affichages")
    date_affichage = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["utilisateur", "question"],
                name="unique_affichage_par_utilisateur_et_question",
            )
        ]

    def __str__(self):
        return f"{self.utilisateur} — {self.question.titre}"
