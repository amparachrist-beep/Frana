from django.conf import settings
from django.utils import timezone

from .models import FeatureUsage, FeedbackAffichage, FeedbackQuestion, FeedbackResponse


class FeedbackService:
    """
    Point d'entrée unique utilisé depuis les vues de Frana :

        question = FeedbackService.should_show(request.user, "compte_a_rebours")

    Le service ne sait rien de Django views/templates : il ne fait que décider
    et enregistrer, ce qui le rend facile à tester unitairement.
    """

    @staticmethod
    def should_show(utilisateur, fonctionnalite):
        """
        Renvoie la FeedbackQuestion de niveau 1 à proposer à cet utilisateur pour
        cette fonctionnalité, ou None si rien ne doit être affiché maintenant.
        """
        aujourd_hui = timezone.now().date()

        candidats = (
            FeedbackQuestion.objects.filter(
                fonctionnalite=fonctionnalite,
                active=True,
                niveau=FeedbackQuestion.Niveau.RAPIDE,
            )
            .exclude(affichages__utilisateur=utilisateur)
            .order_by("-priorite")
        )

        for question in candidats:
            if not question.est_dans_periode():
                continue

            if question.delai_jours_inscription:
                inscription = getattr(utilisateur, "cree_le", None)
                if inscription and (aujourd_hui - inscription.date()).days < question.delai_jours_inscription:
                    continue

            if question.seuil_utilisations > 1:
                usage = FeatureUsage.objects.filter(
                    utilisateur=utilisateur, fonctionnalite=fonctionnalite
                ).first()
                if not usage or usage.compteur < question.seuil_utilisations:
                    continue

            return question

        return None

    @staticmethod
    def question_suivante(question_parent, reponse):
        """Renvoie la question de niveau 2/3 déclenchée par une réponse donnée, ou None."""
        return FeedbackQuestion.objects.filter(
            question_parent=question_parent,
            declenchee_par_reponse=reponse,
            active=True,
        ).first()

    @staticmethod
    def record_response(utilisateur, question, reponse, commentaire="", version_application=""):
        FeedbackAffichage.objects.get_or_create(utilisateur=utilisateur, question=question)
        return FeedbackResponse.objects.create(
            utilisateur=utilisateur,
            question=question,
            reponse=reponse,
            commentaire=commentaire,
            version_application=version_application or getattr(settings, "APP_VERSION", ""),
        )

    @staticmethod
    def marquer_affichee(utilisateur, question):
        FeedbackAffichage.objects.get_or_create(utilisateur=utilisateur, question=question)