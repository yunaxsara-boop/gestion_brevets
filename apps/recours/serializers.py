from rest_framework import serializers
from .models import Recours
from apps.brevets.serializers import BrevetSerializer


class RecoursSerializer(serializers.ModelSerializer):
    # ✅ Lecture : affiche les infos du brevet
    id_brevet_detail = BrevetSerializer(source='id_brevet', read_only=True)

    class Meta:
        model = Recours
        fields = '__all__'
        extra_kwargs = {
            'id':       {'read_only': True},
            'id_brevet': {'required': True},
        }
