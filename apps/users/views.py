from django.contrib.auth import authenticate
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import Utilisateur
from .serializers import UtilisateurSerializer


# ✅ Permission personnalisée
class IsAdminOrSuperuser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_staff
                or request.user.is_superuser
                or request.user.groups.filter(name__iexact="admin").exists()  # ✅ ajouté
            )
        )


class UtilisateurViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrSuperuser]
    queryset = Utilisateur.objects.all().order_by('id')
    serializer_class = UtilisateurSerializer

    def create(self, request, *args, **kwargs):
        password1 = request.data.get("password")
        password2 = request.data.get("password_confirm")

        # ✅ Vérification confirmation mot de passe
        if not password1:
            return Response(
                {"password": ["Le mot de passe est obligatoire."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        if password1 != password2:
            return Response(
                {"password_confirm": ["Les mots de passe ne correspondent pas."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        password1 = request.data.get("password")
        password2 = request.data.get("password_confirm")

        # ✅ Si un mot de passe est fourni, vérifier la confirmation
        if password1 or password2:
            if password1 != password2:
                return Response(
                    {"password_confirm": ["Les mots de passe ne correspondent pas."]},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return super().update(request, *args, **kwargs)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user     = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'error': "Nom d'utilisateur ou mot de passe incorrect."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'token':        token.key,
        'user_id':      user.id,
        'username':     user.username,
        'email':        user.email,
        'is_superuser': user.is_superuser,
        'is_staff':     user.is_staff,
        'groups':       list(user.groups.values_list('name', flat=True)),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    serializer = UtilisateurSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    Token.objects.filter(user=request.user).delete()
    return Response({'message': 'Deconnexion reussie.'})