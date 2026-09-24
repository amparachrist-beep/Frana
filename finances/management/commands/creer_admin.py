from django.core.management.base import BaseCommand
import os

from finances.models import Utilisateur


class Command(BaseCommand):
    help = "Crée un superutilisateur à partir des variables d'environnement, si absent."

    def handle(self, *args, **options):
        telephone = os.environ.get("DJANGO_SUPERUSER_TELEPHONE")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        nom_complet = os.environ.get("DJANGO_SUPERUSER_NOM_COMPLET", "Administrateur")

        if not telephone or not password:
            self.stdout.write(self.style.WARNING(
                "DJANGO_SUPERUSER_TELEPHONE ou DJANGO_SUPERUSER_PASSWORD manquant — étape ignorée."
            ))
            return

        if Utilisateur.objects.filter(telephone=telephone).exists():
            self.stdout.write(self.style.SUCCESS(f"Superutilisateur {telephone} déjà existant."))
            return

        Utilisateur.objects.create_superuser(
            telephone=telephone,
            password=password,
            nom_complet=nom_complet,
        )
        self.stdout.write(self.style.SUCCESS(f"Superutilisateur {telephone} créé."))