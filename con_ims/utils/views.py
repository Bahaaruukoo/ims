from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import select_template
from inventory.models import Location
from projects.models import Project, Site

from .forms import MembershipForm
from .models import Membership

User = get_user_model()


def landing_page(request):
    if request.user and request.user.is_authenticated:
        #return redirect("home")
        if getattr(request.user, "is_platform_admin", False):
            return redirect("/admin/")
        if getattr(request.user, "is_admin", False): #tenant admin
            return redirect("/admin/")
        return redirect("/portal/")

    tenant_name = request.tenant.name

    if tenant_name != "public":
        template = select_template([
            f"utils/{tenant_name}/landing_page.html",
            "utils/default/landing_page.html"
        ])
        return render(request, template.template.name)
    return render(request, "utils/landing_page.html")


@login_required
def portal_page(request):
    return render(request, "utils/portal.html")


def membership_list(request):
    memberships = Membership.objects.filter(
        project__tenant=request.tenant
    ).select_related("project", "member", "site", "location")

    return render(request, "utils/membership_list.html", {
        "memberships": memberships
    })

def membership_create(request):
    project = request.GET.get("project")
    site = request.GET.get("site")
    location = request.GET.get("location")
    popup = request.GET.get("popup")

    if request.method == "POST":
        form = MembershipForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.full_clean()
            member=obj.save()
            if popup:
                return render(request, "utils/membership_form.html", {"form": form, "close":True, "member":member})
            return redirect("membership_list")
    else:
        form = MembershipForm()
        
        # If project is provided → preselect + disable
        if project:
            form.fields["project"].initial = Project.objects.filter(pk=project, tenant=request.tenant).first()
            form.fields["project"].disabled = True
            form.fields["location"].queryset = Location.objects.filter(tenant=request.tenant, project__id = project)
        if site:
            form.fields["site"].initial = Site.objects.filter( id=site).first()
            form.fields["site"].disabled = True
            form.fields["location"].disabled = True
        if location:
            form.fields["location"].initial = Location.objects.filter(id=location).first()
            form.fields["location"].disabled = True
            form.fields["site"].disabled = True

        else:
            # Limit queryset
            form.fields["project"].queryset = Project.objects.filter(tenant=request.tenant)

            #form.fields["project"].queryset = Project.objects.filter(tenant=request.tenant)
            form.fields["site"].queryset = Site.objects.filter(tenant=request.tenant)
            form.fields["location"].queryset = Location.objects.filter(tenant=request.tenant)
            
    form.fields["member"].queryset = User.objects.filter(tenant=request.tenant)

    return render(request, "utils/membership_form.html", {
        "form": form,
        "title": "Assign Member to Site" if site else "Add Manager",
        "project": project,
        "site": site,
        "location": location,
        "popup":popup
    })

def membership_update(request, pk):
    membership = get_object_or_404(Membership, pk=pk, project__tenant=request.tenant)

    if request.method == "POST":
        form = MembershipForm(request.POST, instance=membership)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.full_clean()
            obj.save()
            return redirect("membership_list")
    else:
        form = MembershipForm(instance=membership)

    form.fields["project"].queryset = Project.objects.filter(tenant=request.tenant)
    form.fields["member"].queryset = User.objects.filter(tenant=request.tenant)
    form.fields["site"].queryset = Site.objects.filter(tenant=request.tenant)
    form.fields["location"].queryset = Location.objects.filter(tenant=request.tenant)

    return render(request, "utils/membership_form.html", {
        "form": form,
        "title": "Edit Membership"
    })


def membership_delete(request, pk):
    
    project = request.GET.get("project")
    site = request.GET.get("site")
    popup = request.GET.get("popup")

    membership = get_object_or_404(Membership, pk=pk, project__tenant=request.tenant)

    if request.method == "POST":
        membership.delete()
        if project:
            return render(request, "utils/membership_delete.html", {"close":True})
        return redirect("membership_list")

    return render(request, "utils/membership_delete.html", {
        "membership": membership,
        "popup":popup
    })

