from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.models import Notifications
from .models import Recours
from .serializers import RecoursSerializer


class RecoursViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Recours.objects.all()
    serializer_class = RecoursSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return Recours.objects.all()

        if user.groups.filter(name="Responsable").exists():
            return Recours.objects.all()

        if user.groups.filter(name="Directeur").exists():
            return Recours.objects.all()

        return Recours.objects.filter(id=user)

    def create(self, request, *args, **kwargs):
        user = request.user
        id_brevet = request.data.get("id_brevet")

        # ✅ agent ajouté — peut créer un recours sur n'importe quel brevet
        if not (
            user.is_staff
            or user.is_superuser
            or user.groups.filter(name="Responsable").exists()
            or user.groups.filter(name="Directeur").exists()
            or user.groups.filter(name="agent").exists()  # ✅ FIX
        ):
            if id_brevet:
                from apps.brevets.models import Brevet
                allowed_brevet = Brevet.objects.filter(
                    id_brevet=id_brevet,
                    user=user  # ✅ FIX : user direct au lieu de id_demande__id
                ).exists()

                if not allowed_brevet:
                    return Response(
                        {"error": "Vous ne pouvez pas créer un recours sur ce brevet."},
                        status=status.HTTP_403_FORBIDDEN
                    )

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        recours = serializer.save(id=self.request.user)
        Notifications.objects.create(
            id=self.request.user,
            message=f"Votre recours '{recours.motif}' a ete cree."
        )

    @action(detail=True, methods=['post'])
    def traiter_recours(self, request, pk=None):
        if not request.user.groups.filter(name="Responsable").exists():
            return Response(
                {"error": "Vous n'avez pas la permission de traiter un recours."},
                status=status.HTTP_403_FORBIDDEN
            )

        recours = self.get_object()
        nouveau_statut = request.data.get("statut")

        if nouveau_statut not in ["TRAITE", "REFUSE"]:
            return Response(
                {"error": "Le statut doit etre TRAITE ou REFUSE."},
                status=status.HTTP_400_BAD_REQUEST
            )

        recours.statut = nouveau_statut
        recours.date_traitement = timezone.now().date()
        recours.save()

        Notifications.objects.create(
            id=recours.id,
            message=f"Votre recours '{recours.motif}' a ete mis a jour: {nouveau_statut}."
        )

        return Response(
            {
                "message": "Recours traite avec succes.",
                "statut": recours.statut,
                "date_traitement": recours.date_traitement,
            }
        )