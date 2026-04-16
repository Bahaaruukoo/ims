from django.db import models

from con_ims.settings import AUTH_USER_MODEL


class Membership(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE)
    member = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    location = models.ForeignKey('inventory.Location', on_delete=models.CASCADE, null=True, blank=True)
    site = models.ForeignKey('projects.Site', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'member', 'site'],
                name='unique_project_member_site'
            ),
            models.UniqueConstraint(
                fields=['project', 'member', 'location'],
                name='unique_project_member_location'
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}

        # Must have at least one
        if not self.site and not self.location:
            errors['site'] = "Provide at least a site or a location."
            errors['location'] = "Provide at least a site or a location."

        # Site must belong to project
        if self.site and self.site.project != self.project:
            errors['site'] = "Selected site does not belong to this project."

        # Location must belong to project
        if self.location and self.location.project != self.project:
            errors['location'] = "Selected location does not belong to this project."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.member} @ {self.project}"


class Settings(models.Model):
    StoreManagerCanApproveMaterialRequests = models.BooleanField(default=True)