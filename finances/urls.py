from django.urls import path
from . import views

urlpatterns = [
    # ---------- AUTHENTIFICATION ----------
    path("", views.accueil, name="accueil"),
    path("connexion/", views.connexion, name="connexion"),
    path("inscription/", views.inscription, name="inscription"),
    path("deconnexion/", views.deconnexion, name="deconnexion"),

    # ---------- DASHBOARD ----------
    path("dashboard/", views.dashboard, name="dashboard"),

    # ---------- TRANSACTIONS ----------
    path("transactions/", views.transactions, name="transactions"),
    path("transactions/nouvelle/", views.transaction_create, name="transaction_create"),

    # ---------- SOURCES DE REVENU ----------
    path("revenus/", views.sources, name="sources"),
    path("revenus/nouveau/", views.source_create, name="source_create"),
    path("revenus/<uuid:pk>/supprimer/", views.source_delete, name="source_delete"),

    # ---------- CATÉGORIES ----------
    path("categories/", views.categories, name="categories"),
    path("categories/nouvelle/", views.categorie_create, name="categorie_create"),
    path("categories/<uuid:pk>/supprimer/", views.categorie_delete, name="categorie_delete"),

    # ---------- OBJECTIFS D'ÉPARGNE ----------
    path("objectifs/", views.objectifs, name="objectifs"),
    path("objectifs/nouveau/", views.objectif_create, name="objectif_create"),
    path("objectifs/<uuid:pk>/contribuer/", views.objectif_contribuer, name="objectif_contribuer"),
    path("objectifs/<uuid:pk>/abandonner/", views.objectif_abandonner, name="objectif_abandonner"),

    # ---------- DETTES ----------
    path("dettes/", views.dettes, name="dettes"),
    path("dettes/nouvelle/", views.dette_create, name="dette_create"),
    path("dettes/<uuid:pk>/rembourser/", views.dette_remboursement, name="dette_remboursement"),

    # ---------- PROFIL ----------
    path("profil/", views.profil, name="profil"),
    path("a-propos/", views.about, name="about"),
    path("fonctionnalites/", views.fonctionnalites, name="fonctionnalites"),
]