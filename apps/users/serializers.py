from django.contrib.auth.models import Group
from rest_framework import serializers
from .models import Utilisateur


class UtilisateurSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Group.objects.all(),
        required=False,
    )

    class Meta:
        model = Utilisateur
        fields = (
            'id', 'username', 'email', 'password',
            'date_ajout', 'groups',
            'is_superuser', 'is_staff',
        )
        read_only_fields = ('date_ajout', 'is_superuser')
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
        groups   = validated_data.pop('groups', [])
        password = validated_data.pop('password', None)
        user     = Utilisateur(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        if groups:
            user.groups.set(groups)
        return user

    def update(self, instance, validated_data):
        groups   = validated_data.pop('groups', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if groups is not None:
            instance.groups.set(groups)
        return instance

    def validate_username(self, value):
        qs = Utilisateur.objects.filter(username=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ce nom d'utilisateur existe déjà.")
        return value
