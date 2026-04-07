# setup_admin.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "virement_project.settings")
django.setup()

from django.contrib.auth.models import User
from virement_app.models import UserProfile

# Créer ou récupérer admin
if not User.objects.filter(username="admin").exists():
    admin = User.objects.create_superuser(
        username="admin@bnm.mr",
        email="admin@bnm.mr",  # ton vrai email
        password="123456789"
    )
else:
    admin = User.objects.get(username="admin")

# Créer ou mettre à jour UserProfile
profile, created = UserProfile.objects.get_or_create(user=admin)
profile.is_valid = True
profile.can_view_files = True
profile.save()
