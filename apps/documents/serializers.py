from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    brevet_info = serializers.SerializerMethodField(read_only=True)
    fichier_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['id_document', 'id', 'date_ajout']

    def get_fichier_url(self, obj):
        if not obj.fichier:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.fichier.url)
        return obj.fichier.url

    def get_brevet_info(self, obj):
        if obj.id_brevet:
            return {
                "id_brevet":  obj.id_brevet.id_brevet,
                "titre":      obj.id_brevet.titre,
                "num_brevet": obj.id_brevet.num_brevet,
            }
        return None

    def validate(self, attrs):
        return attrs