from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.models import Notifications
from .models import Brevet, DemandeBrevet, Deposant, Inventeur
from .serializers import (
    BrevetSerializer,
    DemandeBrevetSerializer,
    DeposantSerializer,
    InventeurSerializer,
)


class DemandeBrevetViewSet(viewsets.ModelViewSet):
    queryset = DemandeBrevet.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = DemandeBrevetSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return DemandeBrevet.objects.all()
        if user.groups.filter(name="responsable").exists():
            return DemandeBrevet.objects.all()
        if user.groups.filter(name="directeur").exists():
            return DemandeBrevet.objects.all()
        return DemandeBrevet.objects.filter(id=user)

    def perform_create(self, serializer):
        demande = serializer.save(id=self.request.user)
        Notifications.objects.create(
            id=self.request.user,
            message=f"Votre demande '{demande.titre}' a ete creee."
        )

    @action(detail=True, methods=['post'])
    def valider_demande(self, request, pk=None):
        if not request.user.groups.filter(name="responsable").exists():
            return Response(
                {"error": "Vous n'avez pas la permission de valider une demande."},
                status=status.HTTP_403_FORBIDDEN
            )
        demande = self.get_object()
        demande.statut = "valider"
        demande.save()
        Notifications.objects.create(
            id=demande.id,
            message=f"Votre demande '{demande.titre}' a ete validee."
        )
        return Response({"message": "Demande validee avec succes."})

    @action(detail=True, methods=['post'])
    def refuser_demande(self, request, pk=None):
        if not request.user.groups.filter(name="responsable").exists():
            return Response(
                {"error": "Vous n'avez pas la permission de refuser une demande."},
                status=status.HTTP_403_FORBIDDEN
            )
        demande = self.get_object()
        demande.statut = "non_valider"
        demande.save()
        Notifications.objects.create(
            id=demande.id,
            message=f"Votre demande '{demande.titre}' a ete refusee."
        )
        return Response({"message": "Demande refusee avec succes."})


class DeposantViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Deposant.objects.all()
    serializer_class = DeposantSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Deposant.objects.all()
        if user.groups.filter(name="responsable").exists():
            return Deposant.objects.all()
        if user.groups.filter(name="directeur").exists():
            return Deposant.objects.all()
        return Deposant.objects.filter(id_demande__id=user)


class InventeurViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Inventeur.objects.all()
    serializer_class = InventeurSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Inventeur.objects.all()
        if user.groups.filter(name="responsable").exists():
            return Inventeur.objects.all()
        if user.groups.filter(name="directeur").exists():
            return Inventeur.objects.all()
        return Inventeur.objects.filter(id_demande__id=user).distinct()


class BrevetViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Brevet.objects.all()
    serializer_class = BrevetSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Brevet.objects.all()
        if user.groups.filter(name="responsable").exists():
            return Brevet.objects.all()
        if user.groups.filter(name="directeur").exists():
            return Brevet.objects.all()
        return Brevet.objects.filter(user=user)

    def _can_manage_brevet(self, user):
        return (
            user.is_staff
            or user.is_superuser
            or user.groups.filter(name="agent").exists()
            or user.groups.filter(name="responsable").exists()
        )

    def create(self, request, *args, **kwargs):
        if not self._can_manage_brevet(request.user):
            return Response(
                {"error": "Seul un agent peut ajouter un brevet."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not self._can_manage_brevet(request.user):
            return Response(
                {"error": "Seul un agent peut modifier un brevet."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._can_manage_brevet(request.user):
            return Response(
                {"error": "Seul un agent peut supprimer un brevet."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        # ✅ user injecté ici — ne pas l'envoyer depuis le frontend
        brevet = serializer.save(user=self.request.user)
        if brevet.id_demande:
            Notifications.objects.create(
                id=brevet.id_demande.id,
                message=f"Brevet créé pour la demande '{brevet.id_demande.titre}'"
            )