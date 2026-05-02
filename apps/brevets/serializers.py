from rest_framework import serializers
from .models import Brevet, DemandeBrevet, Deposant, Inventeur
from apps.documents.models import Document
import datetime


class DeposantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposant
        fields = '__all__'


class InventeurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventeur
        fields = ['id_inv', 'nom_inv', 'prenom_inv', 'adress_inv']


class DemandeBrevetSerializer(serializers.ModelSerializer):
    createur_username = serializers.SerializerMethodField(read_only=True)
    createur_id       = serializers.SerializerMethodField(read_only=True)
    documents         = serializers.SerializerMethodField(read_only=True)  # ✅ nouveau

    class Meta:
        model  = DemandeBrevet
        fields = '__all__'
        extra_kwargs = {
            'id':            {'read_only': True},
            'pays_origine':  {'required': False, 'default': ''},
            'numdemande_CA': {'required': False, 'default': 0},
            'date_CA':       {'required': False},
            'date_pouvoir':  {'required': False},
            'mandataire':    {'required': False, 'default': ''},
            'num_depo':      {'required': False, 'default': 0},
            'date_depo':     {'required': False},
        }

    def get_createur_username(self, obj):
        return obj.id.username if obj.id else "—"

    def get_createur_id(self, obj):
        return obj.id.id if obj.id else None

    # ✅ Retourne les documents liés à cette demande avec URL absolue
    def get_documents(self, obj):
        docs = Document.objects.filter(id_demande=obj)
        request = self.context.get('request')
        result = []
        for doc in docs:
            fichier_url = None
            if doc.fichier:
                fichier_url = (
                    request.build_absolute_uri(doc.fichier.url)
                    if request else doc.fichier.url
                )
            result.append({
                "id_document":    doc.id_document,
                "nom_document":   doc.nom_document,
                "type_document":  doc.type_document,
                "date_ajout":     str(doc.date_ajout),
                "fichier_url":    fichier_url,
                "fichier_nom":    doc.fichier.name.split("/")[-1] if doc.fichier else None,
            })
        return result

    def validate(self, data):
        today = datetime.date.today()
        if not data.get('date_CA'):
            data['date_CA'] = today
        if not data.get('date_pouvoir'):
            data['date_pouvoir'] = today
        if not data.get('date_depo'):
            data['date_depo'] = today
        return data


class BrevetSerializer(serializers.ModelSerializer):
    id_inv = InventeurSerializer(many=True, read_only=True)
    id_dep = DeposantSerializer(read_only=True)

    inventeurs_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )
    deposant_data = serializers.DictField(
        write_only=True,
        required=False
    )

    class Meta:
        model = Brevet
        fields = '__all__'
        extra_kwargs = {
            'id_dep': {'required': False},
            'id_inv': {'required': False},
            'user':   {'required': False},
        }

    def create(self, validated_data):
        inventeurs_data = validated_data.pop('inventeurs_data', [])
        deposant_data   = validated_data.pop('deposant_data', None)

        if deposant_data and (deposant_data.get('nom_dep') or deposant_data.get('prenom_dep')):
            deposant = Deposant.objects.create(
                nom_dep    = deposant_data.get('nom_dep', ''),
                prenom_dep = deposant_data.get('prenom_dep', ''),
            )
            validated_data['id_dep'] = deposant

        brevet = Brevet.objects.create(**validated_data)

        for inv in inventeurs_data:
            if inv.get('nom_inv') or inv.get('prenom_inv'):
                inventeur = Inventeur.objects.create(
                    nom_inv    = inv.get('nom_inv', ''),
                    prenom_inv = inv.get('prenom_inv', ''),
                )
                brevet.id_inv.add(inventeur)

        return brevet

    def update(self, instance, validated_data):
        inventeurs_data = validated_data.pop('inventeurs_data', None)
        deposant_data   = validated_data.pop('deposant_data', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if deposant_data:
            if instance.id_dep:
                instance.id_dep.nom_dep    = deposant_data.get('nom_dep', instance.id_dep.nom_dep)
                instance.id_dep.prenom_dep = deposant_data.get('prenom_dep', instance.id_dep.prenom_dep)
                instance.id_dep.save()
            else:
                deposant = Deposant.objects.create(
                    nom_dep    = deposant_data.get('nom_dep', ''),
                    prenom_dep = deposant_data.get('prenom_dep', ''),
                )
                instance.id_dep = deposant
                instance.save()

        if inventeurs_data is not None:
            existants = list(instance.id_inv.all())
            for i, inv in enumerate(inventeurs_data):
                if i < len(existants):
                    existants[i].nom_inv    = inv.get('nom_inv', existants[i].nom_inv)
                    existants[i].prenom_inv = inv.get('prenom_inv', existants[i].prenom_inv)
                    existants[i].save()
                else:
                    nouvel_inv = Inventeur.objects.create(
                        nom_inv    = inv.get('nom_inv', ''),
                        prenom_inv = inv.get('prenom_inv', ''),
                    )
                    instance.id_inv.add(nouvel_inv)

        return instance