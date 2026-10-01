# forms.py
from datetime import timedelta

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import (
    Utilisateur, SourceRevenu, Categorie, Transaction,
    ObjectifEpargne, ContributionEpargne, Dette, RemboursementDette,
)
from django.db import models


# =========================================================
# AUTHENTIFICATION
# =========================================================
INDICATIFS = [
    ("+242", "Congo Brazzaville"),
    ("+226", "Burkina Faso"),
    ("+241", "Gabon"),
    ("+223", "Mali"),
    ("+221", "Sénégal"),
    ("+228", "Togo"),
]


class InscriptionForm(UserCreationForm):
    indicatif = forms.ChoiceField(
        choices=INDICATIFS,
        initial="+242",
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Utilisateur
        fields = [
            "nom_complet", "telephone", "email",
            "frequence_revenu", "date_paie_habituelle", "devise",
        ]
        widgets = {
            "nom_complet": forms.TextInput(attrs={
                "class": "login__input",
                "placeholder": " ",
                "autocomplete": "name",
            }),
            "telephone": forms.TextInput(attrs={
                "class": "login__input",
                "placeholder": " ",
                "autocomplete": "tel-national",
            }),
            "email": forms.EmailInput(attrs={
                "class": "login__input",
                "placeholder": " ",
                "autocomplete": "email",
            }),
            "frequence_revenu": forms.Select(attrs={
                "class": "login__input",
                "style": "background: transparent; color: #fffaf2;",
            }),
            "date_paie_habituelle": forms.NumberInput(attrs={
                "class": "login__input",
                "placeholder": " ",
                "min": 1,
                "max": 31,
            }),
            "devise": forms.Select(attrs={
                "class": "login__input",
                "style": "background: transparent; color: #fffaf2;",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter la classe aux champs de mot de passe (gérés par UserCreationForm)
        self.fields["password1"].widget.attrs.update({
            "class": "login__input",
            "placeholder": " ",
            "autocomplete": "new-password",
        })
        self.fields["password2"].widget.attrs.update({
            "class": "login__input",
            "placeholder": " ",
            "autocomplete": "new-password",
        })

    def clean(self):
        cleaned = super().clean()
        numero = (cleaned.get("telephone") or "").strip()
        indicatif = cleaned.get("indicatif") or "+242"
        if numero:
            # Retire espaces, points et tirets
            numero = "".join(c for c in numero if c.isdigit() or c == "+")
            if not numero.startswith("+"):
                chiffres_indicatif = indicatif.lstrip("+")  # "+242" -> "242"
                # Si la saisie commence déjà par l'indicatif (sans le "+"),
                # on le retire pour ne pas le doubler. La garde sur la longueur
                # évite d'amputer un vrai numéro local qui commencerait par les
                # mêmes chiffres.
                if (
                    numero.startswith(chiffres_indicatif)
                    and len(numero) - len(chiffres_indicatif) >= 8
                ):
                    numero = numero[len(chiffres_indicatif):]
                numero = f"{indicatif}{numero}"
            cleaned["telephone"] = numero
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.date_fin_essai = timezone.now().date() + timedelta(days=30)
        user.statut_abonnement = Utilisateur.Abonnement.ESSAI
        if commit:
            user.save()
        return user


class ConnexionForm(forms.Form):
    telephone = forms.CharField(
        label="Téléphone",
        widget=forms.TextInput(attrs={
            "class": "login__input",
            "placeholder": " ",
            "autocomplete": "tel",
        }),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            "class": "login__input",
            "placeholder": " ",
            "autocomplete": "current-password",
        }),
    )

    def clean(self):
        cleaned = super().clean()
        telephone = cleaned.get("telephone")
        password = cleaned.get("password")
        if telephone and password:
            saisie = telephone.strip()
            # Retire espaces, points et tirets
            numero = "".join(c for c in saisie if c.isdigit() or c == "+")

            # Numéros candidats : tel que saisi, avec "+", ou avec chaque indicatif
            candidats = {saisie, numero}
            if not numero.startswith("+"):
                candidats.add("+" + numero)
                candidats.update(f"{code}{numero}" for code, _ in INDICATIFS)

            # On ne teste le mot de passe que sur les comptes qui existent
            existants = Utilisateur.objects.filter(
                telephone__in=candidats
            ).values_list("telephone", flat=True)

            user = None
            for tel in existants:
                user = authenticate(telephone=tel, password=password)
                if user:
                    break

            if not user:
                raise forms.ValidationError("Téléphone ou mot de passe incorrect.")
            cleaned["user"] = user
        return cleaned


# =========================================================
# SOURCES DE REVENU
# =========================================================
class SourceRevenuForm(forms.ModelForm):
    class Meta:
        model = SourceRevenu
        exclude = ["utilisateur", "actif"]


# =========================================================
# CATÉGORIES
# =========================================================
class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ["nom", "type", "icone"]
        widgets = {"icone": forms.TextInput(attrs={"placeholder": "emoji ou code"})}

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.est_predefinie = False  # Catégorie personnelle
        if commit:
            instance.save()
        return instance


# =========================================================
# WIDGET : ajoute data-type="revenu|depense" sur chaque <option>
# (doit être défini AVANT TransactionForm)
# =========================================================
class CategorieSelect(forms.Select):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        # `value` est un ModelChoiceIteratorValue (Django >= 3.1) ;
        # l'option vide ("---------") est une simple chaîne, sans .instance
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"]["data-type"] = instance.type
        return option


# =========================================================
# TRANSACTIONS
# =========================================================
class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        exclude = ["utilisateur", "cree_le"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "categorie": CategorieSelect(),
        }

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.utilisateur = utilisateur
        if utilisateur:
            # Catégories système + celles de l'utilisateur
            self.fields["categorie"].queryset = Categorie.objects.filter(
                models.Q(utilisateur__isnull=True) | models.Q(utilisateur=utilisateur)
            )
            # Sources de revenu de l'utilisateur uniquement
            self.fields["source_revenu"].queryset = SourceRevenu.objects.filter(
                utilisateur=utilisateur, actif=True
            )
        # Rendre source_revenu optionnel
        self.fields["source_revenu"].required = False

    def clean(self):
        cleaned = super().clean()
        categorie = cleaned.get("categorie")
        type_ = cleaned.get("type")
        source = cleaned.get("source_revenu")

        if categorie and type_ and categorie.type != type_:
            raise forms.ValidationError(
                "Le type sélectionné ne correspond pas à la catégorie choisie."
            )
        if source and type_ and type_ != Transaction.Type.REVENU:
            raise forms.ValidationError(
                "Une source de revenu ne peut être liée qu'à un revenu."
            )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.utilisateur:
            instance.utilisateur = self.utilisateur
        if commit:
            instance.save()
        return instance


# =========================================================
# OBJECTIFS D'ÉPARGNE
# =========================================================
class ObjectifForm(forms.ModelForm):
    class Meta:
        model = ObjectifEpargne
        # montant_actuel exclu : mis à jour via les contributions (PDF §4.5)
        fields = ["nom", "montant_cible", "date_cible"]
        widgets = {"date_cible": forms.DateInput(attrs={"type": "date"})}

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance._state.adding:
            instance.montant_actuel = 0
        if commit:
            instance.save()
        return instance


class ContributionForm(forms.ModelForm):
    class Meta:
        model = ContributionEpargne
        fields = ["montant", "date"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


# =========================================================
# DETTES
# =========================================================
class DetteForm(forms.ModelForm):
    class Meta:
        model = Dette
        exclude = ["utilisateur", "montant_restant", "statut"]
        widgets = {
            "date_creation": forms.DateInput(attrs={"type": "date"}),
            "date_echeance": forms.DateInput(attrs={"type": "date"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Initialisation : montant_restant = montant_initial à la création
        if instance._state.adding:
            instance.montant_restant = instance.montant_initial
            instance.statut = Dette.Statut.EN_COURS
        if commit:
            instance.save()
        return instance


class RemboursementForm(forms.ModelForm):
    class Meta:
        model = RemboursementDette
        fields = ["montant", "date"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}