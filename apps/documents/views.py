from django.http import FileResponse, Http404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

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

        if user.groups.filter(name__in=["Responsable", "Directeur"]).exists():
            return Document.objects.all()

        return Document.objects.filter(id=user)

    def perform_create(self, serializer):
        serializer.save(id=self.request.user)

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