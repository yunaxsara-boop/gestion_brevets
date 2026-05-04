from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Paiement
from .serializers import PaiementSerializer
from apps.notifications.models import Notifications
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

User = get_user_model()


def notifier_groupe(groupe_name, message):
    users = User.objects.filter(groups__name=groupe_name)
    for u in users:
        Notifications.objects.create(id=u, message=message)


def verifier_echeance_brevet(brevet):
    """
    Vérifie si le brevet approche ou a dépassé 1 an.
    Envoie une notification si c'est le cas.
    """
    aujourd_hui = timezone.now().date()
    if not brevet.date_depo:
        return

    try:
        echeance = brevet.date_depo.replace(year=brevet.date_depo.year + 1)
    except ValueError:
        echeance = brevet.date_depo.replace(year=brevet.date_depo.year + 1, day=28)

    jours_restants = (echeance - aujourd_hui).days

    if jours_restants <= 30:
        msg = (
            f"Le brevet '{brevet.titre}' (n°{brevet.num_brevet}) "
            f"arrive à échéance de paiement dans {jours_restants} jours ({echeance}). "
            f"Veuillez renouveler le paiement."
        )
        # Notifier l'agent propriétaire du brevet
        Notifications.objects.create(id=brevet.user, message=msg)
        # Notifier responsables et directeurs
        notifier_groupe("responsable", msg)
        notifier_groupe("directeur", msg)


class PaiementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Paiement.objects.all()
        if user.groups.filter(name="responsable").exists():
            return Paiement.objects.all()
        if user.groups.filter(name="directeur").exists():
            return Paiement.objects.all()
        return Paiement.objects.filter(id=user)

    def create(self, request, *args, **kwargs):
        id_brevet = request.data.get("id_brevet_id")
        if id_brevet and Paiement.objects.filter(id_brevet=id_brevet).exists():
            return Response(
                {"error": "Un paiement existe déjà pour ce brevet."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        paiement = serializer.save(id=self.request.user)

        # ✅ Vérifier l'échéance du brevet lié et notifier si besoin
        if paiement.id_brevet:
            verifier_echeance_brevet(paiement.id_brevet)

    def perform_update(self, serializer):
        paiement = serializer.save()

        # ✅ Si le paiement passe à "payer" → notifier l'agent
        if paiement.statut == "payer":
            Notifications.objects.create(
                id=paiement.id,
                message=f"Votre paiement pour le brevet '{paiement.id_brevet.titre}' a été confirmé."
            )