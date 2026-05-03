import os
import traceback
from groq import Groq
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

SYSTEM_PROMPT = """Tu es un assistant intelligent intégré dans un système de gestion de brevets (INAPI - Institut National Algérien de la Propriété Industrielle).

Tu aides les utilisateurs avec :
- Les demandes de brevets (création, suivi, validation)
- Les brevets (dépôt, numéros, titulaires, statuts)
- Les paiements de taxes et redevances
- Les recours administratifs
- Les documents officiels
- Les procédures et délais réglementaires

Rôles dans le système :
- Agent : crée et suit les demandes, brevets, documents et paiements
- Responsable : valide ou refuse les demandes et recours
- Directeur : consulte les statistiques et rapports
- Admin : gère les utilisateurs et leurs rôles

Réponds toujours en français, de façon claire, concise et professionnelle.
Si une question dépasse ton périmètre, indique poliment que l'utilisateur doit contacter le support."""

client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    messages = request.data.get('messages', [])

    if not messages:
        return Response(
            {'error': 'Aucun message fourni.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages[-20:],
            max_tokens=1024,
        )
        return Response({'reply': response.choices[0].message.content})

    except Exception as e:
        traceback.print_exc()  # ← affiche l'erreur complète dans le terminal
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )