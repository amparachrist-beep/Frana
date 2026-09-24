from django.contrib import admin

# Register your models here.

from django.contrib import admin
from django.db.models import Count

from .models import FeatureUsage, FeedbackAffichage, FeedbackQuestion, FeedbackResponse


@admin.register(FeedbackQuestion)
class FeedbackQuestionAdmin(admin.ModelAdmin):
    list_display = ("titre", "fonctionnalite", "niveau", "type_reponse", "active", "priorite")
    list_filter = ("fonctionnalite", "niveau", "type_reponse", "active")
    search_fields = ("titre", "question")
    autocomplete_fields = ("question_parent",)


@admin.register(FeedbackResponse)
class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = ("date_reponse", "utilisateur", "question", "reponse", "version_application")
    list_filter = ("question__fonctionnalite", "reponse", "version_application", "date_reponse")
    search_fields = ("utilisateur__nom_complet", "commentaire")
    autocomplete_fields = ("utilisateur", "question")
    date_hierarchy = "date_reponse"
    change_list_template = "admin/feedback/feedbackresponse/change_list.html"

    def changelist_view(self, request, extra_context=None):
        stats = (
            FeedbackResponse.objects.values("question__fonctionnalite")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        repartition = {}
        for ligne in stats:
            fonctionnalite = ligne["question__fonctionnalite"]
            total = ligne["total"]
            par_reponse = (
                FeedbackResponse.objects.filter(question__fonctionnalite=fonctionnalite)
                .values("reponse")
                .annotate(nb=Count("id"))
            )
            repartition[fonctionnalite] = {
                "total": total,
                "reponses": [
                    {
                        "reponse": r["reponse"],
                        "nb": r["nb"],
                        "pourcentage": round(100 * r["nb"] / total, 1),
                    }
                    for r in par_reponse
                ],
            }
        extra_context = extra_context or {}
        extra_context["repartition_par_fonctionnalite"] = repartition
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(FeatureUsage)
class FeatureUsageAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "fonctionnalite", "compteur", "derniere_utilisation")
    list_filter = ("fonctionnalite",)
    search_fields = ("utilisateur__nom_complet",)
    autocomplete_fields = ("utilisateur",)


@admin.register(FeedbackAffichage)
class FeedbackAffichageAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "question", "date_affichage")
    autocomplete_fields = ("utilisateur", "question")
