from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError, ProgrammingError

'''
class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.session.admin_sessions
'''
from django.db.models.signals import post_migrate


def create_default_roles(sender, **kwargs):
    # Import locally to avoid AppRegistryNotReady errors
    from .models import Role
    
    ROLE_NAMES = [
        'PLATFORM_ADMIN', 'ADMIN', 
        'STAFF', 'VIEWER', 'AUDITOR', 'MANAGER', 
        'STORE_MANAGER', 'SITE_ENGINEER', 'PROJECT_MANAGER', 'SUPERVISOR', 'WORKER'
    ]
    
    for name in ROLE_NAMES:
        Role.objects.get_or_create(name=name)

class CoreAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.auth_logging
        import core.session.admin_sessions

        # Connect the signal so it runs after every 'migrate' command
        post_migrate.connect(create_default_roles, sender=self)
