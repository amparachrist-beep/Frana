# finances/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Utilisateur, SourceRevenu, Categorie, Transaction,
    ObjectifEpargne, ContributionEpargne, Dette, RemboursementDette,
)


# =========================================================
# UTILISATEUR
# =========================================================
@admin.register(Utilisateur)
class UtilisateurAdmin(BaseUserAdmin):
    ordering = ("nom_complet",)
    list_display = (
        "nom_complet", "telephone", "email", "devise",
        "statut_abonnement", "date_fin_essai", "is_active",
    )
    list_filter = (
        "statut_abonnement", "frequence_revenu", "devise", "is_active", "is_staff",
    )
    search_fields = ("nom_complet", "telephone", "email")
    readonly_fields = ("cree_le", "modifie_le", "last_login")

    fieldsets = (
        (None, {"fields": ("telephone", "password")}),
        ("Informations personnelles", {
            "fields": ("nom_complet", "email")
        }),
        ("Paramètres financiers", {
            "fields": (
                "frequence_revenu", "date_paie_habituelle", "devise",
            )
        }),
        ("Abonnement", {
            "fields": ("statut_abonnement", "date_fin_essai")
        }),
        ("Permissions", {
            "fields": (
                "is_active", "is_staff", "is_superuser",
                "groups", "user_permissions",
            )
        }),
        ("Dates importantes", {
            "fields": ("last_login", "cree_le", "modifie_le")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "telephone", "nom_complet", "email",
                "frequence_revenu", "date_paie_habituelle", "devise",
                "password1", "password2",
            ),
        }),
    )


# =========================================================
# SOURCES DE REVENU
# =========================================================
@admin.register(SourceRevenu)
class SourceRevenuAdmin(admin.ModelAdmin):
    list_display = (
        "nom", "utilisateur", "montant_attendu", "frequence",
        "jour_habituel", "dernier_montant_recu", "dernier_date_recue", "actif",
    )
    list_filter = ("frequence", "actif")
    search_fields = ("nom", "utilisateur__nom_complet", "utilisateur__telephone")
    autocomplete_fields = ("utilisateur",)
    readonly_fields = ("cree_le", "modifie_le")
    list_select_related = ("utilisateur",)


# =========================================================
# CATÉGORIES
# =========================================================
@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "type", "utilisateur", "est_predefinie", "icone")
    list_filter = ("type", "est_predefinie")
    search_fields = ("nom", "utilisateur__nom_complet")
    autocomplete_fields = ("utilisateur",)
    list_select_related = ("utilisateur",)


# =========================================================
# TRANSACTIONS
# =========================================================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "date", "utilisateur", "type", "categorie",
        "montant", "canal_declaratif", "source_revenu",
    )
    list_filter = ("type", "canal_declaratif", "date")
    search_fields = (
        "utilisateur__nom_complet", "utilisateur__telephone",
        "categorie__nom", "note",
    )
    autocomplete_fields = ("utilisateur", "categorie", "source_revenu")
    date_hierarchy = "date"
    readonly_fields = ("cree_le",)
    list_select_related = ("utilisateur", "categorie", "source_revenu")


# =========================================================
# OBJECTIFS D'ÉPARGNE
# =========================================================
@admin.register(ObjectifEpargne)
class ObjectifEpargneAdmin(admin.ModelAdmin):
    list_display = (
        "nom", "utilisateur", "montant_cible", "montant_actuel",
        "progression_affichee", "date_cible", "statut",
    )
    list_filter = ("statut", "date_cible")
    search_fields = ("nom", "utilisateur__nom_complet")
    autocomplete_fields = ("utilisateur",)
    readonly_fields = ("cree_le", "modifie_le")
    list_select_related = ("utilisateur",)

    @admin.display(description="Progression")
    def progression_affichee(self, obj):
        return f"{obj.progression:.1f} %"


@admin.register(ContributionEpargne)
class ContributionEpargneAdmin(admin.ModelAdmin):
    list_display = ("date", "objectif_epargne", "montant")
    list_filter = ("date",)
    search_fields = ("objectif_epargne__nom", "objectif_epargne__utilisateur__nom_complet")
    autocomplete_fields = ("objectif_epargne",)
    date_hierarchy = "date"
    list_select_related = ("objectif_epargne",)


# =========================================================
# DETTES ET REMBOURSEMENTS
# =========================================================
@admin.register(Dette)
class DetteAdmin(admin.ModelAdmin):
    list_display = (
        "personne", "utilisateur", "sens", "montant_initial",
        "montant_restant", "date_creation", "date_echeance", "statut",
    )
    list_filter = ("sens", "statut", "date_creation", "date_echeance")
    search_fields = ("personne", "utilisateur__nom_complet", "note")
    autocomplete_fields = ("utilisateur",)
    date_hierarchy = "date_creation"
    list_select_related = ("utilisateur",)


@admin.register(RemboursementDette)
class RemboursementDetteAdmin(admin.ModelAdmin):
    list_display = ("date", "dette", "montant")
    list_filter = ("date",)
    search_fields = ("dette__personne", "dette__utilisateur__nom_complet")
    autocomplete_fields = ("dette",)
    date_hierarchy = "date"
    list_select_related = ("dette",)


# =========================================================
# PERSONNALISATION DE L'ADMIN
# =========================================================
admin.site.site_header = "Frana — Administration"
admin.site.site_title = "Frana Admin"
admin.site.index_title = "Gestion du portail Salarié / Revenu fixe"