from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
import traceback


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.recours.models import Recours
            from apps.paiements.models import Paiement
            from apps.brevets.models import Brevet, DemandeBrevet

            user     = request.user
            is_admin = user.is_staff or user.is_superuser or \
                       user.groups.filter(name__in=["responsable", "directeur"]).exists()

            mode     = request.query_params.get("mode", "")
            selected = request.query_params.get("selected", "")

            brevets   = Brevet.objects.all()        if is_admin else Brevet.objects.filter(user=user)
            demandes  = DemandeBrevet.objects.all() if is_admin else DemandeBrevet.objects.filter(id=user)
            recours   = Recours.objects.all()       if is_admin else Recours.objects.filter(id=user)
            paiements = Paiement.objects.all()      if is_admin else Paiement.objects.filter(id=user)

            # ✅ date_depo (pas date_depot)
            brevets_f   = self._filter_date(brevets,   "date_depo",     mode, selected)
            paiements_f = self._filter_date(paiements, "date_paiement", mode, selected)
            recours_f   = self._filter_date(recours,   "date_depot",    mode, selected)
            demandes_f  = demandes  # ← on filtre pas les demandes pour l'instant

            stats = {
                "total_brevets":    brevets_f.count(),
                "brevets_acceptes": brevets_f.filter(statut="ACCEPTER").count(),
                "total_demandes":   demandes_f.count(),
                "total_recours":    recours_f.count(),
            }

            donut = {
                "acceptes":   brevets_f.filter(statut="ACCEPTER").count(),
                "refuses":    brevets_f.filter(statut="REFUSER").count(),
                "en_attente": brevets_f.filter(statut="EN_ATTENTE").count(),
            }

            bar_data = self._get_bar_data(paiements_f)

            # ✅ date_depo (pas date_depot)
            derniers_brevets = []
            for b in brevets_f.order_by("-date_depo")[:5]:
                derniers_brevets.append({
                    "num_brevet": str(getattr(b, "num_brevet", "") or ""),
                    "titre":      str(getattr(b, "titre", "")      or ""),
                    "date_depot": str(b.date_depo) if getattr(b, "date_depo", None) else "",
                    "statut":     str(getattr(b, "statut", "")     or ""),
                })

            derniers_paiements = []
            for p in paiements_f.order_by("-date_paiement")[:5]:
                titre = ""
                try:
                    if p.id_brevet:
                        titre = str(getattr(p.id_brevet, "titre", "") or "")
                except Exception:
                    pass
                derniers_paiements.append({
                    "titre_brevet":  titre,
                    "montant_total": str(getattr(p, "montant_total", "") or ""),
                    "date_paiement": str(p.date_paiement) if getattr(p, "date_paiement", None) else "",
                    "statut":        str(getattr(p, "statut", "") or ""),
                })

            return Response({
                "stats":              stats,
                "donut":              donut,
                "bar_data":           bar_data,
                "derniers_brevets":   derniers_brevets,
                "derniers_paiements": derniers_paiements,
            })

        except Exception as e:
            traceback.print_exc()
            return Response({
                "error":  str(e),
                "detail": traceback.format_exc()
            }, status=500)

    def _filter_date(self, qs, date_field, mode, selected):
        if not selected:
            return qs
        try:
            if mode == "Jour":
                y, m, d = selected.split("-")
                return qs.filter(**{
                    f"{date_field}__year":  int(y),
                    f"{date_field}__month": int(m),
                    f"{date_field}__day":   int(d),
                })
            elif mode == "Mois":
                y, m = selected.split("-")
                return qs.filter(**{
                    f"{date_field}__year":  int(y),
                    f"{date_field}__month": int(m),
                })
            elif mode == "Année":
                return qs.filter(**{f"{date_field}__year": int(selected)})
        except (ValueError, AttributeError):
            pass
        return qs

    def _get_bar_data(self, paiements_qs):
        MOIS_LABELS = {
            1: "Jan", 2: "Fév",  3: "Mar",  4: "Avr",
            5: "Mai", 6: "Juin", 7: "Juil", 8: "Août",
            9: "Sep", 10: "Oct", 11: "Nov", 12: "Déc",
        }
        try:
            monthly = (
                paiements_qs
                .annotate(mois=TruncMonth("date_paiement"))
                .values("mois")
                .annotate(
                    total=Sum("montant_total"),
                    payes=Sum("montant_total", filter=Q(statut="Payé")),
                )
                .order_by("mois")
            )
            labels, revenus, paiments = [], [], []
            for row in monthly:
                if row["mois"]:
                    labels.append(MOIS_LABELS.get(row["mois"].month, "?"))
                    revenus.append(float(row["total"]  or 0))
                    paiments.append(float(row["payes"] or 0))
            return {"labels": labels, "revenus": revenus, "paiements": paiments}
        except Exception:
            return {"labels": [], "revenus": [], "paiements": []}