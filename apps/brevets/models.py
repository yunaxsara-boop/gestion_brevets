from django.db import models
from django.conf import settings


# models.py — ajouter dans DemandeBrevet
class DemandeBrevet(models.Model):
    STATUT_CHOICES = [('valider', 'valider'), ('non_valider', 'non_valider')]

    id_demande        = models.AutoField(primary_key=True)
    titre             = models.TextField()
    nature            = models.CharField(max_length=100)
    num_depo          = models.IntegerField()
    date_depo         = models.DateField()
    pays_origine      = models.CharField(max_length=100)
    numdemande_CA     = models.IntegerField()
    date_CA           = models.DateField()
    mandataire        = models.CharField(max_length=255)
    date_pouvoir      = models.DateField()
    prepose_reception = models.CharField(max_length=255, blank=True, default="")
    lieu_reception    = models.CharField(max_length=255, blank=True, default="")
    date_reception    = models.DateField(null=True, blank=True)
    autre_info        = models.TextField(blank=True)
    statut            = models.CharField(max_length=20, choices=STATUT_CHOICES, default='non_valider')
    id                = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column='id',
        related_name='demandes'
    )

    # ✅ Champs pièces déposées
    piece_copie_int      = models.BooleanField(default=False)
    piece_memoire_nat    = models.BooleanField(default=False)
    piece_memoire_fr     = models.BooleanField(default=False)
    piece_memoire_fr_dup = models.BooleanField(default=False)
    piece_dessins_orig   = models.BooleanField(default=False)
    piece_dessins_dup    = models.BooleanField(default=False)
    piece_abrege         = models.BooleanField(default=False)
    piece_pouvoir        = models.BooleanField(default=False)
    piece_priorite       = models.BooleanField(default=False)
    piece_cession        = models.BooleanField(default=False)
    piece_titre          = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id_demande} - {self.titre}"

class Deposant(models.Model):
    id_dep = models.AutoField(primary_key=True)
    nom_dep = models.CharField(max_length=100)
    prenom_dep = models.CharField(max_length=100)
    denomination = models.CharField(max_length=255, blank=True, default="")
    adresse_dep = models.CharField(max_length=255, blank=True, default="")
    nationalite = models.CharField(max_length=100, blank=True, default="")

    # ✅ null=True, blank=True — plus obligatoire d'avoir une demande
    id_demande = models.ForeignKey(
        DemandeBrevet,
        on_delete=models.CASCADE,
        db_column='id_demande',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.nom_dep} {self.prenom_dep}"


class Inventeur(models.Model):
    id_inv = models.AutoField(primary_key=True)
    nom_inv = models.CharField(max_length=100)
    prenom_inv = models.CharField(max_length=100)
    adress_inv = models.CharField(max_length=255, blank=True, default="")

    # ✅ blank=True — plus obligatoire d'avoir une demande
    id_demande = models.ManyToManyField(
        DemandeBrevet,
        related_name='inventeurs',
        blank=True
    )

    def __str__(self):
        return f"{self.nom_inv} {self.prenom_inv}"


class Brevet(models.Model):
    STATUT_CHOICES = [
        ('ACCEPTER', 'ACCEPTER'),
        ('REFUSER', 'REFUSER'),
        ('EN_ATTENTE', 'EN_ATTENTE'),
    ]

    id_brevet = models.AutoField(primary_key=True)
    num_brevet = models.IntegerField()
    titre = models.CharField(max_length=1000)
    num_depo = models.IntegerField()
    date_depo = models.DateField()
    date_sortie = models.DateField()
    titulaire = models.CharField(max_length=255)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="brevets"
    )
    id_demande = models.OneToOneField(
        'DemandeBrevet',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    id_inv = models.ManyToManyField('Inventeur', related_name='brevets', blank=True)
    id_dep = models.ForeignKey('Deposant', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.titre