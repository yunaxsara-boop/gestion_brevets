from .models import Notifications
from .serializers import NotificationsSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response


class NotificationsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Notifications.objects.all()
    serializer_class = NotificationsSerializer

    def get_queryset(self):
        # Chaque user voit uniquement ses propres notifications
        return Notifications.objects.filter(id=self.request.user)

    def perform_create(self, serializer):
        serializer.save(id=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.etat = True
        notification.save()
        return Response({'message': 'Notification marquée comme lue.'})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        Notifications.objects.filter(id=request.user, etat=False).update(etat=True)
        return Response({'message': 'Toutes les notifications marquées comme lues.'})