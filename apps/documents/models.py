from django.db import models
from django.conf import settings


class Document(models.Model):
    TYPE_CHOICES = [
        ("brevet",   "Brevet"),
        ("demande",  "Demande"),
        ("recours",  "Recours"),
        ("paiement", "Paiement"),
    ]

    id_document  = models.AutoField(primary_key=True)
    nom_document = models.CharField(max_length=255)
    fichier      = models.FileField(upload_to='documents/', null=True, blank=True)
    date_ajout   = models.DateField(auto_now_add=True)

    type_document = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default="brevet"
    )

    id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column='id'
    )
    id_brevet = models.ForeignKey(
        'brevets.Brevet',
        on_delete=models.CASCADE,
        null=True, blank=True,
        db_column='id_brevet'
    )
    id_demande = models.ForeignKey(
        'brevets.DemandeBrevet',
        on_delete=models.CASCADE,
        null=True, blank=True,
        db_column='id_demande'
    )
    id_paiement = models.OneToOneField(
        'paiements.Paiement',
        on_delete=models.CASCADE,
        null=True, blank=True,
        db_column='id_paiement'
    )

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return self.nom_document