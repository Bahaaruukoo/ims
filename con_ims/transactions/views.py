from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q, Sum
from django.forms import ModelForm
from django.http import JsonResponse
# Create your views here.
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views import View
from inventory.models import ItemVariant, Location, Stock
from projects.models import Project, ProjectStage, Site, StageMaterial
from utils.models import Membership, Settings

from .forms import IncomingStockForm
from .models import IncomingStock, InventoryTransaction, MaterialRequest


def request_list(request):
    requests = None
    if request.user.is_staff:
        requests = MaterialRequest.objects.filter(
            tenant=request.tenant,
            status__in=["PENDING", "APPROVED"]
        ).distinct().order_by("-created_at")

    else:
        requests = MaterialRequest.objects.filter(
            tenant=request.tenant,
            status__in=["PENDING", "APPROVED"]
        ).filter(
            Q(requested_by=request.user) |
            Q(
                project__membership__member=request.user,
                project__membership__location=models.F("warehouse")
            )
        ).distinct().order_by("-created_at")

    return render(request, "transactions/material_request_list.html", {"requests": requests })


def request_detail(request, pk):
    mr = get_object_or_404(MaterialRequest, pk=pk, tenant=request.tenant)
    avails = Stock.objects.filter(tenant=request.tenant, location=mr.warehouse, item_variant=mr.item_variant).first()
    available = avails.quantity if avails != None else 0

    planed_quantity = StageMaterial.objects.filter(tenant=request.tenant, stage=mr.stage, item_variant=mr.item_variant).first()
    planed_qtty = planed_quantity.planned_quantity if planed_quantity != None else 0

    so_far_dispatched = InventoryTransaction.objects.filter(
        tenant=request.tenant,
        stage=mr.stage,
        item_variant=mr.item_variant,
        type="OUT"
    ).aggregate(total=Sum("quantity"))["total"] or 0

    return render(request, "transactions/material_request_detail.html", 
        {
            "request_obj": mr,
            "available": available,
            "planed_qtty":planed_qtty,
            "so_far_dispatched": so_far_dispatched
         })


def request_create(request):
    if request.method == "POST":

        project_id = request.POST.get("project")
        site_id = request.POST.get("site")
        stage_id = request.POST.get("stage")
        warehouse_id = request.POST.get("warehouse")

        # -----------------------------
        # BASIC VALIDATION
        # -----------------------------
        if not project_id or not site_id:
            messages.error(request, "Project and Site are required")
            return redirect("request_create")

        # Validate project
        try:
            project = Project.objects.get(id=project_id, tenant=request.tenant)
        except Project.DoesNotExist:
            messages.error(request, "Invalid project")
            return redirect("request_create")

        # Validate site belongs to project
        try:
            site = Site.objects.get(id=site_id, project=project, tenant=request.tenant)
        except Site.DoesNotExist:
            messages.error(request, "Invalid site for selected project")
            return redirect("request_create")

        # Validate stage belongs to site (optional)
        stage = None
        if stage_id:
            try:
                stage = ProjectStage.objects.get(
                    id=stage_id,
                    site=site,
                    tenant=request.tenant
                )
            except ProjectStage.DoesNotExist:
                messages.error(request, "Invalid stage for selected site")
                return redirect("request_create")

            if stage.status=="COMPLETED":
                messages.error(request, "You cannot send material request for a completed stage")
                return redirect("request_create")

       # Validate warehouse belongs to project
        try:
            warehouse = Location.objects.get(id=warehouse_id, project=project, tenant=request.tenant)
        except Location.DoesNotExist:
            messages.error(request, "Invalid warehouse for selected project")
            return redirect("request_create")

        # -----------------------------
        # HANDLE ITEMS
        # -----------------------------
        items = request.POST.get("item_variant")
        quantities = request.POST.get("quantity")

        valid_item_found = False

        if not items or not quantities:
            messages.error(request, "Error in request")
            return redirect("request_create")

        try:
            qty = float(quantities)
            if qty <= 0:
                messages.error(request, "Add valid quantity")
                return redirect("request_create")
                
        except ValueError:
            messages.error(request, "Add valid quantity")
            return redirect("request_create")

        item_variant = ItemVariant.objects.filter(id=items).first()

        mr = MaterialRequest.objects.create(
            tenant=request.tenant,
            project=project,
            site=site,
            stage=stage,
            warehouse=warehouse,
            item_variant=item_variant,
            requested_quantity=quantities,
            requested_by=request.user,
        )

        valid_item_found = True
        
        if not valid_item_found:
            mr.delete()
            messages.error(request, "Add at least one valid item")
            return redirect("request_create")

        # -----------------------------
        # SUCCESS
        # -----------------------------
        messages.success(request, "Material request created successfully")
        return redirect("request_detail", pk=mr.pk)
    # -----------------------------
    # GET REQUEST
    # -----------------------------
    projects = Project.objects.filter(status='ACTIVE', membership__member=request.user).distinct().order_by("-start_date")
    item_variants = ItemVariant.objects.filter(tenant=request.tenant).distinct().order_by("item__name")

    return render(request, "transactions/material_request_create.html", {
        "projects": projects, "item_variants": item_variants
    })

def pending_request_count_partial(request):
    count = 0
    if request.user.is_staff:
        count = MaterialRequest.objects.filter(
            tenant=request.tenant,
            status="PENDING"
        ).count()
    else:
        count = MaterialRequest.objects.filter(
            tenant=request.tenant,
            status__in=["PENDING", "APPROVED"]
        ).filter(
            Q(requested_by=request.user) |
            Q(
                project__membership__member=request.user,
                project__membership__location=models.F("warehouse")
            )
        ).distinct().count()
        
    return render(request, "partials/pending_count.html", {"count": count})

def request_approve(request, pk):
    mr = get_object_or_404(MaterialRequest, pk=pk, tenant=request.tenant)

    if request.method == "POST":

        approved_qty = request.POST.get("approved_quantity")

        # Convert to decimal
        try:
            approved_qty = Decimal(approved_qty)
        except:
            messages.error(request, "Invalid quantity")
            return redirect("request_detail", pk=pk)
        
        avails = Stock.objects.filter(tenant=request.tenant, location=mr.warehouse, item_variant=mr.item_variant).first()
        available = avails.quantity if avails != None else 0

        # Backend validation
        if approved_qty > available:
            messages.error(request, f"Cannot approve more than available ({available}).")
            return redirect("request_detail", pk=pk)
        
        if approved_qty > mr.requested_quantity:
            messages.error(request, f"Cannot approve more than requested quantity ({mr.requested_quantity}).")
            return redirect("request_detail", pk=pk)
        
        mr.status = "APPROVED"
        mr.approved_by = request.user
        mr.approved_quantity = approved_qty
        mr.save()

        messages.success(request, "Request approved")
        return redirect("request_detail", pk=pk)

    return render(request, "transactions/material_request_approve.html", {"request_obj": mr})


def get_sites(request):
    project_id = request.GET.get("project_id")

    sites = Site.objects.filter(
        project_id=project_id,
        membership__member=request.user,
        tenant=request.tenant
    ).values("id", "name")

    return JsonResponse(list(sites), safe=False)


def get_stages(request):
    site_id = request.GET.get("site_id")

    stages = ProjectStage.objects.filter(
        site_id=site_id,
        tenant=request.tenant
    ).exclude(
        status="COMPLETED"
    ).values("id", "name", "status").order_by("-order")

    return JsonResponse(list(stages), safe=False)

def get_warehouses(request):
    project_id = request.GET.get("project_id")

    warehouses = Location.objects.filter(
        project_id=project_id,
        tenant=request.tenant
    ).values("id", "name")

    return JsonResponse(list(warehouses), safe=False)

def store_request_list(request):
    requests = MaterialRequest.objects.filter(
        tenant=request.tenant
    ).order_by("-created_at")

    return render(request, "requests/list.html", {
        "requests": requests
    })


def store_request_detail(request, pk):
    mr = get_object_or_404(
        MaterialRequest,
        pk=pk,
        tenant=request.tenant
    )

    return render(request, "requests/detail.html", {
        "request_obj": mr
    })


def store_request_approve(request, pk):
    mr = get_object_or_404(MaterialRequest, pk=pk, tenant=request.tenant)

    if mr.status != "PENDING":
        messages.error(request, "Only pending requests can be approved")
        return redirect("store_request_detail", pk=pk)

    if request.method == "POST":
        for item in mr.items.all():
            approved_qty = request.POST.get(f"approved_{item.id}")

            if approved_qty:
                try:
                    approved_qty = float(approved_qty)
                except:
                    approved_qty = 0

                item.approved_quantity = approved_qty
                item.save()

        mr.status = "APPROVED"
        mr.save()

        messages.success(request, "Request approved")
        return redirect("store_request_detail", pk=pk)

    return render(request, "requests/approve.html", {
        "request_obj": mr
    })

def store_request_reject(request, pk):
    mr = get_object_or_404(MaterialRequest, pk=pk, tenant=request.tenant)

    if mr.status != "PENDING":
        messages.error(request, "Only pending requests can be rejected")
        return redirect("store_request_detail", pk=pk)

    mr.status = "REJECTED"
    mr.save()

    messages.warning(request, "Request rejected")
    return redirect("store_request_list")


def store_request_dispatch(request, pk):
    mr = get_object_or_404(MaterialRequest, pk=pk, tenant=request.tenant)

    if mr.status != "APPROVED":
        messages.error(request, "Request must be approved first")
        return redirect("store_request_detail", pk=pk)


    if not mr.approved_quantity or mr.approved_quantity <= 0:
        messages.error(request, "Approved request has no quantity")
        return redirect("store_request_detail", pk=pk)
    #find available amount in stock

    # Create OUT transaction
    InventoryTransaction.objects.create(
        tenant=request.tenant,
        item_variant=mr.item_variant,
        request_item = mr,
        quantity=mr.approved_quantity,
        rate=mr.item_variant.unit_cost * mr.approved_quantity,  
        type="OUT",
        project=mr.project,
        site=mr.site,
        stage=mr.stage,
        from_location=mr.warehouse,  # 🔥 replace with actual warehouse
    )

    mr.status = "DISPATCHED"
    mr.save()

    messages.success(request, "Materials dispatched successfully")
    return redirect("store_request_detail", pk=pk)


# -------------------- LIST --------------------
def incoming_stock_list(request):
    
    projects = Project.objects.filter(
        membership__member=request.user,
        membership__location__isnull=False
    ).distinct()

    project_id = request.GET.get("project")
    item_id = request.GET.get("item")
    location_id = request.GET.get("location")
    driver = request.GET.get("driver")

    qs = IncomingStock.objects.filter(tenant=request.tenant)
    
    if projects:
        qs = qs.filter(project__in=projects)

    if project_id:
        qs = qs.filter(project_id=project_id)

    if item_id:
        qs = qs.filter(item_variant_id=item_id)

    if location_id:
        qs = qs.filter(location_id=location_id)

    if driver:
        qs = qs.filter(driver__icontains=driver)

    return render(request, "transactions/incoming_stock_list.html", {
        "stocks": qs,
        "projects": projects or  Project.objects.filter(tenant=request.tenant),
        "items": ItemVariant.objects.filter(tenant=request.tenant).order_by("item__name"),
        "locations": Location.objects.filter(tenant=request.tenant, project__in=projects) if projects else Location.objects.filter(tenant=request.tenant),
        "filters": request.GET,
    })


# -------------------- CREATE --------------------
def incoming_stock_create(request):
    if request.method == "POST":
        form = IncomingStockForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                incoming = form.save(commit=False)
                incoming.tenant = request.tenant
                incoming.created_by = request.user
                incoming.save()
                return redirect("incoming_stock_list")
    else:
        form = IncomingStockForm()

    # Filter dropdowns by tenant
    form.fields["item_variant"].queryset = ItemVariant.objects.filter(tenant=request.tenant)
    form.fields["location"].queryset = Location.objects.filter(tenant=request.tenant)
    form.fields["project"].queryset = Project.objects.filter(tenant=request.tenant)

    return render(request, "transactions/incoming_stock_form.html", {
        "form": form,
        "title": "Add Incoming Stock"
    })


# -------------------- UPDATE --------------------
def incoming_stock_update(request, pk):
    incoming = get_object_or_404(IncomingStock, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        form = IncomingStockForm(request.POST, instance=incoming)

        if form.is_valid():
            updated = form.save(commit=False)
            updated.updated_by = request.user
            updated.save()
            return redirect("incoming_stock_list")
    else:
        form = IncomingStockForm(instance=incoming)

    form.fields["item_variant"].queryset = ItemVariant.objects.filter(tenant=request.tenant)
    form.fields["location"].queryset = Location.objects.filter(tenant=request.tenant)
    form.fields["project"].queryset = Project.objects.filter(tenant=request.tenant)

    return render(request, "transactions/incoming_stock_form.html", {
        "form": form,
        "title": "Edit Incoming Stock"
    })


# -------------------- DELETE --------------------
def incoming_stock_delete(request, pk):
    incoming = get_object_or_404(IncomingStock, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        incoming.delete()
        return redirect("incoming_stock_list")

    return render(request, "transactions/incoming_stock_delete.html", {
        "incoming": incoming
    })


# =========================
# FORM
# =========================
class InventoryTransactionForm(ModelForm):
    class Meta:
        model = InventoryTransaction
        fields = [
            "item_variant",
            "type",
            "quantity",
            "rate",
            "from_location",
            "project",
            "stage",
            "site",
        ]

def transaction_list_view(request):
    tenant = request.tenant

    projects = Project.objects.filter(
        membership__member=request.user,
        membership__location__isnull=False
    ).distinct()

    # Base queryset
    qs = InventoryTransaction.objects.filter(tenant=tenant).select_related(
        "item_variant",
        "from_location",
        "project",
        "stage",
        "site"
    ).order_by("-date")

    # GET filters
    project_id = request.GET.get("project")
    location_id = request.GET.get("location")
    item_id = request.GET.get("item")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    stage_id = request.GET.get("stage")
    site_id = request.GET.get("site")

    # Apply filters
    if project_id:
        qs = qs.filter(project_id=project_id)

        

    if location_id:
        qs = qs.filter(from_location_id=location_id)  # or to_location_id

    if item_id:
        qs = qs.filter(item_variant_id=item_id)

    if site_id:
        qs = qs.filter(site_id=site_id)

    if start_date:
        qs = qs.filter(date__date__gte=parse_date(start_date))

    if end_date:
        qs = qs.filter(date__date__lte=parse_date(end_date))


    if stage_id:
        qs = qs.filter(stage_id=stage_id)

    return render(request, "transactions/list.html", {
        "transactions": qs,
        "projects": projects or Project.objects.filter(tenant=request.tenant),
        "locations": Location.objects.filter(tenant=tenant, project__in=projects) or Location.objects.filter(tenant=tenant),
        "sites": Site.objects.filter(tenant=tenant, project__in=projects) or Site.objects.filter(tenant=tenant),
        "stages": ProjectStage.objects.filter(tenant=tenant, project__in=projects) or ProjectStage.objects.filter(tenant=tenant),
        "items": ItemVariant.objects.filter(tenant=tenant).order_by("item__name"),
        "filters": request.GET,
    })


# =========================
# CREATE VIEW
# =========================
class TransactionCreateView(View):
    def get(self, request):
        form = InventoryTransactionForm()
        return render(request, "transactions/form.html", {"form": form})

    def post(self, request):
        form = InventoryTransactionForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.tenant
            obj.created_by = request.user
            obj.save()

            messages.success(request, "Transaction created successfully")
            return redirect("transaction_list")

        return render(request, "transactions/form.html", {"form": form})


# =========================
# UPDATE VIEW
# =========================
class TransactionUpdateView(View):
    def get(self, request, pk):
        obj = get_object_or_404(
            InventoryTransaction,
            pk=pk,
            tenant=request.tenant
        )

        form = InventoryTransactionForm(instance=obj)
        return render(request, "transactions/form.html", {
            "form": form,
            "edit": True
        })

    def post(self, request, pk):
        obj = get_object_or_404(
            InventoryTransaction,
            pk=pk,
            tenant=request.tenant
        )

        form = InventoryTransactionForm(request.POST, instance=obj)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()

            messages.success(request, "Transaction updated successfully")
            return redirect("transaction_list")

        return render(request, "transactions/form.html", {
            "form": form,
            "edit": True
        })


# =========================
# DELETE VIEW
# =========================
class TransactionDeleteView(View):
    def post(self, request, pk):
        obj = get_object_or_404(
            InventoryTransaction,
            pk=pk,
            tenant=request.tenant
        )

        obj.delete()
        messages.success(request, "Transaction deleted successfully")

        return redirect("transaction_list")

