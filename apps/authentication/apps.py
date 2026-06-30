from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Keep the base name clean so Django maps it to 'authentication.User' flawlessly
    name = 'authentication'