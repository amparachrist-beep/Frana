# views.py
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from feedback.models import FeatureUsage

from .forms import (
    ConnexionForm, InscriptionForm, SourceRevenuForm, TransactionForm,
    ObjectifForm, ContributionForm, DetteForm, RemboursementForm,
    CategorieForm,
)
from .models import (
    Categorie, Transaction, SourceRevenu, ObjectifEpargne,
    ContributionEpargne, Dette, RemboursementDette,
)


# =========================================================
# AUTHENTIFICATION
# =========================================================
def accueil(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "finances/landing.html")


def connexion(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = ConnexionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["user"]
        login(request, user)
        user.verifier_fin_essai()
        return redirect("dashboard")
    return render(request, "finances/connexion.html", {"form": form})


def inscription(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = InscriptionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Votre espace Frana est prêt.")
        return redirect("dashboard")
    return render(request, "finances/inscription.html", {"form": form})


@login_required
@require_POST
def deconnexion(request):
    logout(request)
    return redirect("accueil")


# =========================================================
# UTILITAIRES
# =========================================================
def _prochaine_paie(utilisateur):
    """
    Calcule la prochaine date de revenu selon la fréquence de l'utilisateur.
    - hebdomadaire : jour de semaine (0=lundi … 6=dimanche)
    - quinzaine   : 1er et 15 du mois
    - mensuelle   : jour du mois (1-28 pour éviter les erreurs)
    """
    aujourd_hui = date.today()
    freq = utilisateur.frequence_revenu

    if freq == "hebdomadaire":
        jour_cible = utilisateur.date_paie_habituelle % 7
        delta = (jour_cible - aujourd_hui.weekday()) % 7
        if delta == 0:
            delta = 7
        return aujourd_hui + timedelta(days=delta)

    if freq == "quinzaine":
        if aujourd_hui.day < 15:
            return aujourd_hui.replace(day=15)
        mois = aujourd_hui.month + 1
        annee = aujourd_hui.year
        if mois == 13:
            mois, annee = 1, annee + 1
        return date(annee, mois, 1)

    # Mensuelle par défaut
    jour = min(max(utilisateur.date_paie_habituelle, 1), 28)
    prochaine = aujourd_hui.replace(day=jour)
    if prochaine <= aujourd_hui:
        mois = aujourd_hui.month + 1
        annee = aujourd_hui.year
        if mois == 13:
            mois, annee = 1, annee + 1
        prochaine = date(annee, mois, jour)
    return prochaine


# =========================================================
# DASHBOARD — §2.1, §2.2 du PDF
# =========================================================
@login_required
def dashboard(request):
    user = request.user
    user.verifier_fin_essai()  # bascule essai -> gratuit si expiré

    FeatureUsage.incrementer(user, "compte_a_rebours")  # ligne ajoutée

    transactions = user.transactions.select_related("categorie")[:8]

    revenus = user.transactions.filter(type="revenu").aggregate(
        total=Sum("montant")
    )["total"] or Decimal("0")
    depenses = user.transactions.filter(type="depense").aggregate(
        total=Sum("montant")
    )["total"] or Decimal("0")
    solde = revenus - depenses  # calculé une seule fois

    objectifs = user.objectifs_epargne.filter(statut="en_cours")[:4]
    prochain = _prochaine_paie(user)
    jours_paie = (prochain - date.today()).days

    # Projection basée sur les 30 derniers jours
    debut = date.today() - timedelta(days=30)
    depenses_30j = user.transactions.filter(
        type="depense", date__gte=debut
    ).aggregate(total=Sum("montant"))["total"] or Decimal("0")
    nb_transactions_30j = user.transactions.filter(date__gte=debut).count()
    moyenne_jour = depenses_30j / Decimal("30")

    projection = None
    if moyenne_jour > 0 and nb_transactions_30j >= 5:
        projection = solde / moyenne_jour

    context = {
        "transactions": transactions,
        "revenus": revenus,
        "depenses": depenses,
        "solde": solde,
        "objectifs": objectifs,
        "jours_paie": jours_paie,
        "prochaine_paie": prochain,
        "projection_jours": round(float(projection), 1) if projection is not None else None,
        "page_active": "dashboard",
    }
    return render(request, "finances/dashboard.html", context)


# =========================================================
# TRANSACTIONS — §2.1 du PDF
# =========================================================
@login_required
def transactions(request):
    qs = request.user.transactions.select_related("categorie", "source_revenu")
    type_filter = request.GET.get("type")
    if type_filter in ("revenu", "depense"):
        qs = qs.filter(type=type_filter)
    return render(request, "finances/transactions.html", {
        "transactions": qs,
        "page_active": "transactions",
    })


@login_required
def transaction_create(request):
    # utilisateur passé au formulaire : filtrage auto des querysets + injection au save
    form = TransactionForm(request.POST or None, utilisateur=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        FeatureUsage.incrementer(request.user, "transactions")  # ligne ajoutée
        messages.success(request, "Transaction enregistrée.")
        return redirect("transactions")
    return render(request, "finances/transaction_form.html", {
        "form": form,
        "titre": "Nouvelle",
        "page_active": "transactions",
    })


# =========================================================
# SOURCES DE REVENU — §4.2 du PDF
# =========================================================
@login_required
def sources(request):
    return render(request, "finances/sources.html", {
        "sources": request.user.sources_revenu.filter(actif=True),
        "page_active": "sources",
    })


@login_required
def source_create(request):
    form = SourceRevenuForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.utilisateur = request.user
        obj.save()
        messages.success(request, "Source de revenu ajoutée.")
        return redirect("sources")
    return render(request, "finances/source_form.html", {
        "form": form,
        "titre": "Nouvelle",
        "page_active": "sources",
    })


@login_required
def source_delete(request, pk):
    source = get_object_or_404(SourceRevenu, pk=pk, utilisateur=request.user)

    if request.method == "POST":
        source.actif = False
        source.save(update_fields=["actif"])
        messages.success(request, "Source désactivée.")
        return redirect("sources")

    return render(request, "finances/source_confirm_delete.html", {
        "source": source,
        "page_active": "sources",
    })


# =========================================================
# CATÉGORIES — §4.3 du PDF (catégories personnelles)
# =========================================================
@login_required
def categories(request):
    return render(request, "finances/categories.html", {
        "categories_systeme": Categorie.objects.filter(
            utilisateur__isnull=True
        ).order_by("type", "nom"),
        "categories_perso": Categorie.objects.filter(
            utilisateur=request.user
        ).order_by("type", "nom"),
        "page_active": "profil",
    })


@login_required
def categorie_create(request):
    form = CategorieForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.utilisateur = request.user
        obj.est_predefinie = False
        obj.save()
        messages.success(request, "Catégorie ajoutée.")
        return redirect("categories")
    return render(request, "finances/categorie_form.html", {
        "form": form,
        "titre": "Nouvelle",
        "page_active": "profil",
    })


@login_required
def categorie_delete(request, pk):
    categorie = get_object_or_404(
        Categorie, pk=pk, utilisateur=request.user, est_predefinie=False
    )

    if request.method == "POST":
        categorie.delete()
        messages.success(request, "Catégorie supprimée.")
        return redirect("categories")

    return render(request, "finances/categorie_confirm_delete.html", {
        "categorie": categorie,
        "page_active": "profil",
    })

# =========================================================
# OBJECTIFS D'ÉPARGNE — §2.3, §4.5, §4.6 du PDF
# =========================================================
@login_required
def objectifs(request):
    return render(request, "finances/objectifs.html", {
        "objectifs": request.user.objectifs_epargne.all().order_by("-cree_le"),
        "page_active": "objectifs",
    })


@login_required
def objectif_create(request):
    form = ObjectifForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.utilisateur = request.user
        obj.save()
        messages.success(request, "Objectif créé.")
        return redirect("objectifs")
    return render(request, "finances/objectif_form.html", {
        "form": form,
        "titre": "Nouvel",
        "page_active": "objectifs",
    })


@login_required
def objectif_contribuer(request, pk):
    objectif = get_object_or_404(
        ObjectifEpargne, pk=pk, utilisateur=request.user
    )
    form = ContributionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        contribution = form.save(commit=False)
        contribution.objectif_epargne = objectif
        # Le modèle recalcule montant_actuel + statut automatiquement
        contribution.save()
        FeatureUsage.incrementer(request.user, "epargne")  # ligne ajoutée
        messages.success(request, "Épargne ajoutée à l’objectif.")
        return redirect("objectifs")
    return render(request, "finances/objectif_contribution.html", {
        "form": form,
        "objectif": objectif,
        "page_active": "objectifs",
    })


@login_required
def objectif_abandonner(request, pk):
    objectif = get_object_or_404(
        ObjectifEpargne, pk=pk, utilisateur=request.user
    )

    if request.method == "POST":
        objectif.statut = ObjectifEpargne.Statut.ABANDONNE
        objectif.save(update_fields=["statut", "modifie_le"])
        messages.success(request, "Objectif abandonné.")
        return redirect("objectifs")

    return render(request, "finances/objectif_confirm_abandon.html", {
        "objectif": objectif,
        "page_active": "objectifs",
    })


# =========================================================
# DETTES ET CRÉDITS INFORMELS — §2.4, §4.7, §4.8 du PDF
# =========================================================
@login_required
def dettes(request):
    return render(request, "finances/dettes.html", {
        "dettes": request.user.dettes.all().order_by("-date_creation"),
        "page_active": "dettes",
    })


@login_required
def dette_create(request):
    form = DetteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.utilisateur = request.user
        # Le formulaire initialise déjà montant_restant et statut
        obj.save()
        messages.success(request, "Dette enregistrée.")
        return redirect("dettes")
    return render(request, "finances/dette_form.html", {
        "form": form,
        "titre": "Nouvelle",
        "page_active": "dettes",
    })


@login_required
def dette_remboursement(request, pk):
    dette = get_object_or_404(Dette, pk=pk, utilisateur=request.user)
    form = RemboursementForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        remboursement = form.save(commit=False)
        remboursement.dette = dette
        if remboursement.montant > dette.montant_restant:
            form.add_error(
                "montant", "Le remboursement dépasse le montant restant."
            )
        else:
            # Le modèle recalcule montant_restant + statut automatiquement
            remboursement.save()
            FeatureUsage.incrementer(request.user, "dettes")  # ligne ajoutée
            messages.success(request, "Remboursement enregistré.")
            return redirect("dettes")
    return render(request, "finances/dette_remboursement.html", {
        "form": form,
        "dette": dette,
        "page_active": "dettes",
    })


# =========================================================
# PROFIL UTILISATEUR
# =========================================================
@login_required
def profil(request):
    user = request.user
    context = {
        "utilisateur": user,
        "solde": user.solde,
        "nb_transactions": user.transactions.count(),
        "nb_objectifs": user.objectifs_epargne.count(),
        "nb_dettes": user.dettes.filter(statut="en_cours").count(),
        "page_active": "profil",
    }
    return render(request, "finances/profil.html", context)


# =========================================================
# PAGES PUBLIQUES
# =========================================================
def about(request):
    """Page À propos de Frana — accessible à tous."""
    return render(request, "finances/about.html")


def fonctionnalites(request):
    """Page Fonctionnalités — accessible à tous."""
    return render(request, "finances/fonctionnalites.html")