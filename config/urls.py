from django.contrib import admin
from django.urls import path , include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("api-token-auth/", obtain_auth_token),
    path('admin/', admin.site.urls),
    path('users/', include('apps.users.urls')),
    path('', include('apps.documents.urls')),
    path('', include('apps.brevets.urls')),
    path('', include('apps.dashboards.urls')),
    path('', include('apps.recours.urls')),
    path('', include('apps.paiements.urls')),
    path('', include('apps.notifications.urls')),
    # Ajoute cette ligne dans urlpatterns :
path('api/chatbot/', include('apps.chatbot.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Gestion des Brevets"
admin.site.site_title = "Admin Panel"
admin.site.index_title = "Bienvenue"