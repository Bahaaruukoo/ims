from django.db import connection, models, transaction
from django_tenants.models import DomainMixin, TenantMixin
from django_tenants.utils import schema_context


class Tenant(TenantMixin):
    
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    paid_until = models.DateField(auto_now_add=True)

    org_name = models.CharField(max_length=255)
    #tin_number = models.CharField(max_length=255, blank=True, null=True)

    contact = models.CharField(max_length=255)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20)
    second_phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
   
    on_trial = models.BooleanField(default=False)

    auto_create_schema = True
    auto_drop_schema = True  # Automatically drop schema on tenant deletion


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # create schema manually outside transaction
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}"')

        self.create_schema(check_if_exists=True)


    def delete(self, *args, **kwargs):
        schema = self.schema_name

        # Drop tenant schema first
        with connection.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')

        # Delete tenant row without triggering collector
        type(self).objects.filter(pk=self.pk).delete()

class Domain(DomainMixin):
    pass
