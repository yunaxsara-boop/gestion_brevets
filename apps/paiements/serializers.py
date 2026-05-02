from rest_framework import serializers
from .models import Paiement
from apps.brevets.models import Brevet
from apps.brevets.serializers import BrevetSerializer


class PaiementSerializer(serializers.ModelSerializer):
    # ✅ Lecture : retourne l'objet brevet complet
    id_brevet = BrevetSerializer(read_only=True)

    # ✅ Écriture : accepte un ID entier en POST/PATCH
    id_brevet_id = serializers.PrimaryKeyRelatedField(
        queryset=Brevet.objects.all(),
        source='id_brevet',
        write_only=True
    )

    class Meta:
        model = Paiement
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
        }

    def validate_montant_total(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Le montant total doit être strictement positif."
            )
        return value