from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from projects.models import Project

from .forms import ItemForm, ItemVariantForm, LocationForm, StockForm
from .models import Item, ItemVariant, Location, Stock


def location_list(request):
    locations = Location.objects.filter(tenant=request.tenant)

    name_query = request.GET.get("name", "").strip()

    if name_query:
        locations = locations.filter(name__icontains=name_query)
    else:
        locations = locations[0:25]
    return render(request, "inventory/location_list.html", {"locations": locations, 
        "name_query": name_query })


def location_detail(request, pk):
    location = get_object_or_404(Location, pk=pk)
    return render(request, "inventory/location_detail.html", {"location": location})


def location_create(request):
    project = request.GET.get("project")
    popup = request.GET.get("popup")

    if request.method == "POST":
        form = LocationForm(request.POST)
        location = form.save(commit=False)
        location.tenant = request.tenant   # ← set tenant here
        location.save()
        if popup:
            return render(request, "projects/location_form.html", {"form": form, "close":True, "location": location})

        return redirect("location_list")
    else:
        form = LocationForm()
        # If project is provided → preselect + disable
        if project:
            form.fields["project"].initial = Project.objects.filter(pk=project, tenant=request.tenant).first()
            form.fields["project"].disabled = True

        else:
            # Limit queryset
            form.fields["project"].queryset = Project.objects.filter(tenant=request.tenant)

    return render(request, "inventory/location_form.html", 
                  {"form": form, 
                   "title": "Create Warehouse", 
                   "project": project,
                   "popup":popup })


def location_update(request, pk):
    location = get_object_or_404(Location, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.tenant = request.tenant
            updated.save()
            return redirect("location_list")
    else:
        form = LocationForm(instance=location)

    return render(request, "inventory/location_form.html", {"form": form, "title": "Edit Location"})


def location_delete(request, pk):
    location = get_object_or_404(Location, pk=pk)

    if request.method == "POST":
        location.delete()
        return redirect("location_list")

    return render(request, "inventory/location_delete.html", {"location": location})


# -------------------- ITEM LIST --------------------
def item_list(request):
    items = Item.objects.filter(tenant=request.tenant).order_by("name")
    return render(request, "inventory/item_list.html", {"items": items})


# -------------------- ITEM CREATE --------------------
def item_create(request):
    modal = request.GET.get("modal") == "true"
    popup = request.GET.get("popup")

    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.tenant = request.tenant
            item.save()

            if modal:
                return JsonResponse({
                    "success": True,
                    "id": item.id,
                    "name": item.name
                })

            return redirect("item_list")

    else:
        form = ItemForm()

    if modal:
        return render(request, "inventory/item_popup_form.html", {"form": form})

    return render(request, "inventory/item_form.html", {
        "form": form,
        "title": "Add Item",
        "popup":popup
    })


# -------------------- ITEM UPDATE --------------------
def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.tenant = request.tenant
            updated.save()
            return redirect("item_list")
    else:
        form = ItemForm(instance=item)

    return render(request, "inventory/item_form.html", {"form": form, "title": "Edit Item"})


# -------------------- ITEM DELETE --------------------
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        item.delete()
        return redirect("item_list")

    return render(request, "inventory/item_delete.html", {"item": item})


# -------------------- VARIANT LIST --------------------
def variant_list(request):
    variants = ItemVariant.objects.filter(tenant=request.tenant).order_by("item__name", "name")
    return render(request, "inventory/variant_list.html", {"variants": variants})


# -------------------- VARIANT CREATE --------------------
def variant_create(request):
    popup = request.GET.get("popup")
    if request.method == "POST":
        form = ItemVariantForm(request.POST)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.tenant = request.tenant
            variant.save()
            return redirect("variant_list")
    else:
        form = ItemVariantForm()

    # Filter items by tenant
    form.fields["item"].queryset = Item.objects.filter(tenant=request.tenant)

    return render(request, "inventory/variant_form.html", {"form": form, "title": "Create Item Variant",
                                                           "popup":popup })


# -------------------- VARIANT UPDATE --------------------
def variant_update(request, pk):
    variant = get_object_or_404(ItemVariant, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        form = ItemVariantForm(request.POST, instance=variant)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.tenant = request.tenant
            updated.save()
            return redirect("variant_list")
    else:
        form = ItemVariantForm(instance=variant)

    form.fields["item"].queryset = Item.objects.filter(tenant=request.tenant)

    return render(request, "inventory/variant_form.html", {"form": form, "title": "Edit Item Variant"})


# -------------------- VARIANT DELETE --------------------
def variant_delete(request, pk):
    variant = get_object_or_404(ItemVariant, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        variant.delete()
        return redirect("variant_list")

    return render(request, "inventory/variant_delete.html", {"variant": variant})


# -------------------- LIST --------------------

def stock_list(request):
    project_id = request.GET.get("project")
    stocks = None
    if project_id:
        stocks = Stock.objects.select_related(
            "item_variant__item",
            "location__project"
        )

        stocks = stocks.filter(location__project_id=project_id)
    
    projects = Project.objects.all()

    context = {
        "stocks": stocks,
        "projects": projects,
        "selected_project": project_id,
    }
    return render(request, "inventory/stock_list.html", context)

# -------------------- CREATE --------------------
def stock_create(request):
    if request.method == "POST":
        form = StockForm(request.POST)

        if form.is_valid():
            item_variant = form.cleaned_data["item_variant"]
            location = form.cleaned_data["location"]
            quantity = form.cleaned_data["quantity"]

            # Check for existing stock BEFORE saving
            existing = Stock.objects.filter(
                tenant=request.tenant,
                item_variant=item_variant,
                location=location
            ).first()

            if existing:
                # Merge quantities
                existing.quantity = existing.quantity + quantity
                existing.save()
                return redirect("stock_list")

            # Create new stock manually (DO NOT USE form.save())
            stock = Stock(
                tenant=request.tenant,
                item_variant=item_variant,
                location=location,
                quantity=quantity
            )
            stock.save()

            return redirect("stock_list")
        else:
            print("Form is not valid:", form.errors)
    else:
        form = StockForm()

    # Filter dropdowns by tenant
    form.fields["item_variant"].queryset = ItemVariant.objects.filter(tenant=request.tenant)
    form.fields["location"].queryset = Location.objects.filter(tenant=request.tenant)

    return render(request, "inventory/stock_form.html", {"form": form, "title": "Add Stock"})


# -------------------- UPDATE --------------------
def stock_update(request, pk):
    stock = get_object_or_404(Stock, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.tenant = request.tenant
            updated.save()
            return redirect("stock_list")
    else:
        form = StockForm(instance=stock)

    form.fields["item_variant"].queryset = ItemVariant.objects.filter(tenant=request.tenant)
    form.fields["location"].queryset = Location.objects.filter(tenant=request.tenant)

    return render(request, "inventory/stock_form.html", {"form": form, "title": "Edit Stock"})


# -------------------- DELETE --------------------
def stock_delete(request, pk):
    stock = get_object_or_404(Stock, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        stock.delete()
        return redirect("stock_list")

    return render(request, "inventory/stock_delete.html", {"stock": stock})
