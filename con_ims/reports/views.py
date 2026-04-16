from decimal import Decimal

from django.db.models import DecimalField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render
from projects.models import Project, StageMaterial
from transactions.models import InventoryTransaction

DECIMAL_FIELD = DecimalField(max_digits=12, decimal_places=2)


def project_dashboard(request):

    project_id = request.GET.get("project")
    projects = Project.objects.all()

    charts = []

    if project_id:

        consumed_subquery = InventoryTransaction.objects.filter(
            type="OUT",
            project_id=project_id,
            site=OuterRef("stage__site"),
            stage=OuterRef("stage"),
            item_variant=OuterRef("item_variant"),
        ).values(
            "stage", "item_variant"
        ).annotate(
            total=Sum("quantity")
        ).values("total")[:1]

        queryset = (
            StageMaterial.objects.filter(stage__project_id=project_id)
            .values(
                "stage__id",
                "stage__name",
                "stage__order",              # ✅ ADD THIS
                "stage__site__id",
                "stage__site__name",
                "item_variant__name"
            )
            .annotate(
                planned=Coalesce(
                    Sum("planned_quantity"),
                    Value(0),
                    output_field=DECIMAL_FIELD
                ),
                consumed=Coalesce(
                    Subquery(consumed_subquery),
                    Value(0),
                    output_field=DECIMAL_FIELD
                )
            )
            .order_by(                      # ✅ IMPORTANT
                "stage__site__id",
                "stage__order",
                "item_variant__name"
            )
        )
        # Group per site
        site_map = {}

        for row in queryset:
            site_id = row["stage__site__id"]
            site_name = row["stage__site__name"] or "No Site"

            stage = row["stage__name"]
            item = row["item_variant__name"]

            label = f"{stage} - {item}"

            planned = float(row["planned"] or Decimal("0"))
            consumed = float(row["consumed"] or Decimal("0"))

            site = site_map.setdefault(site_id, {
                "site_name": site_name,
                "labels": [],
                "planned": [],
                "consumed": []
            })

            site["labels"].append(label)
            site["planned"].append(planned)
            site["consumed"].append(consumed)

        charts = list(site_map.values())

    return render(request, "reports/project_dashboard.html", {
        "projects": projects,
        "charts": charts,
        "selected_project": project_id
    })
