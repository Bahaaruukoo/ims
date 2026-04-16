from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_default_tenant(sender, **kwargs):
    # Import locally to avoid AppRegistryNotReady errors
    from .models import Domain, Tenant
    
    tenant = Tenant.objects.get_or_create(
        schema_name="public",
            name="public", 
                                 org_name="Public Tenant", 
                                 contact="admin", 
                                 contact_email="admin@example.com", 
                                 contact_phone="1234567890", 
                                 second_phone="0987654321", 
                                 address="123 Main St", 
                                 is_active=True, 
                                 on_trial=False
                        )
    domain = Domain.objects.get_or_create(domain="localhost", tenant=tenant[0])

class TenantManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenant_manager'

    def ready(self):

        # Connect the signal so it runs after every 'migrate' command
        post_migrate.connect(create_default_tenant, sender=self)