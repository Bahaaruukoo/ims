from django.shortcuts import get_object_or_404, redirect, render
from inventory.models import ItemVariant, Location
from projects.models import Project
from utils.models import Membership

from .forms import ProjectForm, ProjectStageForm, SiteForm, StageMaterialForm
from .models import Project, ProjectStage, Site, StageMaterial


# ---------------- PROJECT LIST ----------------
def project_list(request):
    projects = Project.objects.filter(tenant=request.tenant)

    name_query = request.GET.get("name", "").strip()
    status_query = request.GET.get("status", "").strip()

    # Default behavior: show ACTIVE if no filters at all
    if not name_query and not status_query:
        status_query = "ACTIVE"

    if name_query:
        projects = projects.filter(name__icontains=name_query)

    if status_query:
        projects = projects.filter(status=status_query)

    projects = projects.order_by("-start_date")[:25]

    context = {
        "projects": projects,
        "name_query": name_query,
        "status_query": status_query,
        "status_choices": Project.STATUS_CHOICES,
    }
    return render(request, "projects/project_list.html", context)


def project_detail(request, pk):
    project = Project.objects.filter(
        
        pk=pk,
        tenant=request.tenant
    ).first()

    # Reverse relations
    sites = project.sites.all()
    stages = project.stages.all()
    locations = Location.objects.filter(
        tenant=request.tenant,
        project=project
    )

    materials = ItemVariant.objects.all()
    members = Membership.objects.filter(
        project=project
    ).select_related("member")
    context = {
        "project": project,
        "sites": sites,
        "stages": stages,
        "locations": locations,
        "materials": materials,
        "members": members
    }

    return render(request, "projects/project_detail.html", context)


# ---------------- PROJECT CREATE ----------------
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.tenant
            obj.created_by = request.user
            obj.save()
            return redirect("project_list")
    else:
        form = ProjectForm()

    return render(request, "projects/project_form.html", {"form": form, "title": "Add Project"})


# ---------------- PROJECT UPDATE ----------------
def project_update(request, pk):
    popup = request.GET.get("popup")

    project = get_object_or_404(Project, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
            if popup:
                return render(request, "projects/project_form.html", {"form": form, "close":True})
            return redirect("project_list")
    else:
        form = ProjectForm(instance=project)

    return render(request, "projects/project_form.html", {"form": form, "title": "Edit Project", "popup":popup})


# ---------------- PROJECT DELETE ----------------
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        project.delete()
        return redirect("project_list")

    return render(request, "projects/project_delete.html", {"project": project})

# ---------------- SITE LIST ----------------
def site_list(request):
    sites = Site.objects.filter(tenant=request.tenant).select_related("project")
    return render(request, "projects/site_list.html", {"sites": sites})


# ---------------- SITE CREATE ----------------
'''def site_create(request):
    if request.method == "POST":
        form = SiteForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.tenant
            obj.created_by = request.user
            obj.save()
            return redirect("site_list")
    else:
        form = SiteForm()

    form.fields["project"].queryset = Project.objects.filter(tenant=request.tenant)

    return render(request, "projects/site_form.html", {"form": form, "title": "Add Site"})'''

def site_create(request):
    project = request.GET.get("project")
    popup = request.GET.get("popup")
    if request.method == "POST":
        form = SiteForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.tenant
            obj.created_by = request.user

            # If project was forced, override POST value
            if project:
                obj.project_id = project

            obj.save()
            if project:
                return render(request, "projects/site_form.html", {"form": form, "close":True})
            return redirect("site_list")

    else:
        form = SiteForm()

        # If project is provided → preselect + disable
        if project:
            form.fields["project"].initial = Project.objects.filter(pk=project, tenant=request.tenant).first()
            form.fields["project"].disabled = True

        else:
            # Limit queryset
            form.fields["project"].queryset = Project.objects.filter(tenant=request.tenant)

    return render(request, "projects/site_form.html", {
        "form": form,
        "title": "Add Site",
        "project": project,
        "popup": popup
    })


# ---------------- SITE UPDATE ----------------
def site_update(request, pk):
    site = get_object_or_404(Site, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
            return redirect("site_list")
    else:
        form = SiteForm(instance=site)

    form.fields["project"].queryset = Project.objects.filter(tenant=request.tenant)

    return render(request, "projects/site_form.html", {"form": form, "title": "Edit Site"})


# ---------------- SITE DELETE ----------------
def site_delete(request, pk):
    site = get_object_or_404(Site, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        site.delete()
        return redirect("site_list")

    return render(request, "projects/site_delete.html", {"site": site})


# ---------------- STAGE LIST ----------------
def stage_list(request):
    stages = ProjectStage.objects.all()
    projects = Project.objects.all()

    project_id = request.GET.get("project")
    status = request.GET.get("status")

    if project_id:
        stages = stages.filter(project_id=project_id)

    if status:
        stages = stages.filter(status=status)

    return render(request, "projects/stage_list.html", {
        "stages": stages if project_id else None,
        "projects": projects,
    })


# ---------------- STAGE CREATE ----------------
def stage_create(request):
    project = request.GET.get("project")
    popup = request.GET.get("popup")
    if request.method == "POST":
        form = ProjectStageForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.tenant
            obj.save()
            if project:
                return render(request, "projects/site_form.html", {"form": form, "close":True})
            return redirect("stage_list")
    else:
        form = ProjectStageForm()

        # If project is provided → preselect + disable
        if project:
            pro = Project.objects.filter(pk=project, tenant=request.tenant).first()
            form.fields["project"].initial = pro
            form.fields["project"].disabled = True
            form.fields["site"].queryset = Site.objects.filter(tenant=request.tenant, project=pro)


        else:
            # Limit queryset
            form.fields["project"].queryset = Project.objects.filter(tenant=request.tenant)

            #form.fields["project"].queryset = Project.objects.filter(tenant=request.tenant)
            form.fields["site"].queryset = Site.objects.filter(tenant=request.tenant)

    return render(request, "projects/stage_form.html", {"form": form, "title": "Add Stage", "project": project, "popup":popup })


# ---------------- STAGE UPDATE ----------------
def stage_update(request, pk):
    stage = get_object_or_404(ProjectStage, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        form = ProjectStageForm(request.POST, instance=stage)
        if form.is_valid():
            form.save()
            return redirect("stage_list")
    else:
        form = ProjectStageForm(instance=stage)

    form.fields["project"].queryset = Project.objects.filter(tenant=request.tenant)
    form.fields["site"].queryset = Site.objects.filter(tenant=request.tenant)

    return render(request, "projects/stage_form.html", {"form": form, "title": "Edit Stage"})

# ---------------- STAGE DELETE ----------------
def stage_delete(request, pk):
    stage = get_object_or_404(ProjectStage, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        stage.delete()
        return redirect("stage_list")

    return render(request, "projects/stage_delete.html", {"stage": stage})

def stage_material_list(request):
    materials = StageMaterial.objects.filter(
        tenant=request.tenant
    ).select_related("stage", "stage__project", "item_variant")

    return render(request, "projects/stage_material_list.html", {
        "materials": materials
    })

def stage_material_create(request):
    stage = request.GET.get("stage")
    popup = request.GET.get("popup")
    if request.method == "POST":
        form = StageMaterialForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.tenant
            materials = obj.save()
            if popup:
                return render(request, "projects/stage_material_form.html", {"form": form, "close":True, "materials": materials})
            return redirect("stage_material_list")
    else:
        form = StageMaterialForm()
        if stage:
            form.fields["stage"].initial = ProjectStage.objects.filter(pk=stage, tenant=request.tenant).first()
            form.fields["stage"].disabled = True
        else:
            # Tenant filtering
            form.fields["stage"].queryset = ProjectStage.objects.filter(tenant=request.tenant)

    form.fields["item_variant"].queryset = ItemVariant.objects.filter(tenant=request.tenant)

    return render(request, "projects/stage_material_form.html", {
        "form": form,
        "title": "Add Stage Material",
        "stage": stage,
        "popup":popup
    })

def stage_material_update(request, pk):
    material = get_object_or_404(StageMaterial, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        form = StageMaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            return redirect("stage_material_list")
    else:
        form = StageMaterialForm(instance=material)

    form.fields["stage"].queryset = ProjectStage.objects.filter(tenant=request.tenant)
    form.fields["item_variant"].queryset = ItemVariant.objects.filter(tenant=request.tenant)

    return render(request, "projects/stage_material_form.html", {
        "form": form,
        "title": "Edit Stage Material"
    })


def stage_material_delete(request, pk):
    material = get_object_or_404(StageMaterial, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        material.delete()
        return redirect("stage_material_list")

    return render(request, "projects/stage_material_delete.html", {
        "material": material
    })


