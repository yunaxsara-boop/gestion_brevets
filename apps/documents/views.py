from django.http import FileResponse, Http404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Document
from .serializers import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Document.objects.all()
        if user.groups.filter(name__in=["responsable", "directeur"]).exists():
            return Document.objects.all()
        return Document.objects.filter(id=user)

    def perform_create(self, serializer):
        document = serializer.save(id=self.request.user)

        # ✅ Type "brevet" → brevet lié devient "valider"
        if document.type_document == "brevet" and document.id_brevet:
            brevet = document.id_brevet
            brevet.statut = "ACCEPTER"
            brevet.save()

        # ✅ Type "paiement" → paiement lié devient "paye"
        if document.type_document == "paiement" and document.id_paiement:
            paiement = document.id_paiement
            paiement.statut = "paye"
            paiement.save()

    def perform_destroy(self, instance):
        brevet    = instance.id_brevet
        paiement  = instance.id_paiement
        type_doc  = instance.type_document

        # Supprimer le document
        instance.delete()

        # ✅ Type "brevet" supprimé → si plus aucun doc brevet sur ce brevet → "non_valider"
        if type_doc == "brevet" and brevet:
            reste = Document.objects.filter(
                id_brevet=brevet,
                type_document="brevet"
            ).exists()
            if not reste:
                brevet.statut = "REFUSER"
                brevet.save()

        # ✅ Type "paiement" supprimé → si plus aucun doc paiement sur ce brevet → "non_paye"
        if type_doc == "paiement" and brevet:
            reste = Document.objects.filter(
                id_brevet=brevet,
                type_document="paiement"
            ).exists()
            if not reste and paiement:
                paiement.statut = "non_paye"
                paiement.save()

    @action(detail=False, methods=['get'], url_path='types')
    def get_types(self, request):
        """Retourne les types définis dans TYPE_CHOICES du modèle."""
        types = [
            {"value": value, "label": label}
            for value, label in Document.TYPE_CHOICES
        ]
        return Response(types)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        document = self.get_object()
        if not document.fichier:
            raise Http404("Fichier introuvable.")
        return FileResponse(
            document.fichier.open("rb"),
            as_attachment=True,
            filename=document.fichier.name.split("/")[-1]
        )