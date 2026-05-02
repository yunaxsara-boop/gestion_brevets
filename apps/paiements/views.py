from .models import Paiement
from .serializers import PaiementSerializer
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class PaiementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return Paiement.objects.all()

        if user.groups.filter(name="Responsable").exists():
            return Paiement.objects.all()

        if user.groups.filter(name="Directeur").exists():
            return Paiement.objects.all()

        return Paiement.objects.filter(id=user)

    def create(self, request, *args, **kwargs):
        # ✅ Vérifier qu'un paiement n'existe pas déjà pour ce brevet (OneToOne)
        id_brevet = request.data.get("id_brevet_id")
        if id_brevet and Paiement.objects.filter(id_brevet=id_brevet).exists():
            return Response(
                {"error": "Un paiement existe déjà pour ce brevet."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(id=self.request.user)