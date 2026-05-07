from rest_framework import serializers
from .models import Brevet, DemandeBrevet, Deposant, Inventeur
from apps.documents.models import Document
import datetime


class DeposantSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Deposant
        fields = '__all__'


class InventeurSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Inventeur
        fields = '__all__'


class DemandeBrevetSerializer(serializers.ModelSerializer):
    createur_username = serializers.SerializerMethodField(read_only=True)
    createur_id       = serializers.SerializerMethodField(read_only=True)
    createur_groupe   = serializers.SerializerMethodField(read_only=True)
    documents         = serializers.SerializerMethodField(read_only=True)
    deposant          = serializers.SerializerMethodField(read_only=True)
    inventeur         = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = DemandeBrevet
        fields = [
            'id_demande', 'titre', 'nature', 'num_depo', 'date_depo',
            'pays_origine', 'numdemande_CA', 'date_CA', 'mandataire',
            'date_pouvoir', 'prepose_reception', 'lieu_reception',
            'date_reception', 'autre_info', 'statut', 'id',
            'piece_copie_int', 'piece_memoire_nat', 'piece_memoire_fr',
            'piece_memoire_fr_dup', 'piece_dessins_orig', 'piece_dessins_dup',
            'piece_abrege', 'piece_pouvoir', 'piece_priorite',
            'piece_cession', 'piece_titre',
            'createur_username', 'createur_id', 'createur_groupe',
            'documents', 'deposant', 'inventeur',
        ]
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

    def get_createur_groupe(self, obj):
        if obj.id:
            groups = list(obj.id.groups.values_list('name', flat=True))
            if 'responsable' in groups:
                return 'responsable'
            if 'agent' in groups:
                return 'agent'
        return 'inconnu'

    def get_deposant(self, obj):
        deps = Deposant.objects.filter(id_demande=obj)
        return DeposantSerializer(deps, many=True).data

    def get_inventeur(self, obj):
        invs = obj.inventeurs.all()
        return InventeurSerializer(invs, many=True).data

    def get_documents(self, obj):
        docs    = Document.objects.filter(id_demande=obj)
        request = self.context.get('request')
        result  = []
        for doc in docs:
            fichier_url = None
            if doc.fichier:
                fichier_url = (
                    request.build_absolute_uri(doc.fichier.url)
                    if request else doc.fichier.url
                )
            result.append({
                "id_document":   doc.id_document,
                "nom_document":  doc.nom_document,
                "type_document": doc.type_document,
                "date_ajout":    str(doc.date_ajout),
                "fichier_url":   fichier_url,
                "fichier_nom":   doc.fichier.name.split("/")[-1] if doc.fichier else None,
            })
        return result

    def validate(self, data):
        today = datetime.date.today()
        if not data.get('date_CA'):      data['date_CA']      = today
        if not data.get('date_pouvoir'): data['date_pouvoir'] = today
        if not data.get('date_depo'):    data['date_depo']    = today
        return data


class BrevetSerializer(serializers.ModelSerializer):
    id_inv     = serializers.SerializerMethodField()
    id_dep     = DeposantSerializer(read_only=True)
    id_demande = serializers.SerializerMethodField()

    inventeurs_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )
    deposant_data = serializers.DictField(
        write_only=True,
        required=False
    )
    id_demande_input = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model  = Brevet
        fields = '__all__'
        extra_kwargs = {
            'id_dep':     {'required': False},
            'user':       {'required': False},
            'id_demande': {'required': False},
        }

    def get_id_inv(self, obj):
        invs = obj.inventeurs.all()
        return InventeurSerializer(invs, many=True).data

    def get_id_demande(self, obj):
        if obj.id_demande:
            return {
                "id_demande": obj.id_demande.id_demande,
                "titre":      obj.id_demande.titre,
                "num_depo":   obj.id_demande.num_depo,
                "date_depo":  str(obj.id_demande.date_depo),
                "statut":     obj.id_demande.statut,
            }
        return None

    def create(self, validated_data):
        inventeurs_data  = validated_data.pop('inventeurs_data', [])
        deposant_data    = validated_data.pop('deposant_data', None)
        id_demande_input = validated_data.pop('id_demande_input', None)

        if deposant_data and (deposant_data.get('nom_dep') or deposant_data.get('prenom_dep')):
            deposant = Deposant.objects.create(
                nom_dep    = deposant_data.get('nom_dep', ''),
                prenom_dep = deposant_data.get('prenom_dep', ''),
            )
            validated_data['id_dep'] = deposant

        if id_demande_input:
            try:
                demande = DemandeBrevet.objects.get(pk=id_demande_input)
                validated_data['id_demande'] = demande
            except DemandeBrevet.DoesNotExist:
                pass

        brevet = Brevet.objects.create(**validated_data)

        for inv in inventeurs_data:
            if inv.get('nom_inv') or inv.get('prenom_inv'):
                Inventeur.objects.create(
                    nom_inv    = inv.get('nom_inv', ''),
                    prenom_inv = inv.get('prenom_inv', ''),
                    id_brevet  = brevet,
                )

        return brevet

    def update(self, instance, validated_data):
        inventeurs_data  = validated_data.pop('inventeurs_data', None)
        deposant_data    = validated_data.pop('deposant_data', None)
        id_demande_input = validated_data.pop('id_demande_input', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if id_demande_input is not None:
            try:
                demande = DemandeBrevet.objects.get(pk=id_demande_input)
                instance.id_demande = demande
            except DemandeBrevet.DoesNotExist:
                instance.id_demande = None

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
            existants = list(instance.inventeurs.all())
            for i, inv in enumerate(inventeurs_data):
                if i < len(existants):
                    existants[i].nom_inv    = inv.get('nom_inv', existants[i].nom_inv)
                    existants[i].prenom_inv = inv.get('prenom_inv', existants[i].prenom_inv)
                    existants[i].save()
                else:
                    Inventeur.objects.create(
                        nom_inv    = inv.get('nom_inv', ''),
                        prenom_inv = inv.get('prenom_inv', ''),
                        id_brevet  = instance,
                    )
            if len(inventeurs_data) < len(existants):
                for inv_a_suppr in existants[len(inventeurs_data):]:
                    inv_a_suppr.delete()

        return instance