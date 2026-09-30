from django.db import models
from django.contrib.auth.models import User
from django.core.files import File


# models.py
class GeneratedXML(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="generated_files")
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    excel_file = models.FileField(upload_to="excel_files/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    purpose_code = models.CharField(max_length=50, blank=True, null=True)  # Ajout
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)  # Ajout
    transaction_count = models.IntegerField(blank=True, null=True)  # Ajout

    def __str__(self):
        return f"{self.file_name} by {self.user.username}"

# Nouveau modèle pour les emails
class EmailRecord(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    generated_xml = models.ForeignKey(GeneratedXML, on_delete=models.CASCADE, null=True, blank=True)
    from_email = models.EmailField()
    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='sent')  # sent, failed
    error_message = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Email to {self.to_email} - {self.sent_at}"

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Profil utilisateur pour stocker les permissions et informations"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('comptable', 'Comptable'),
        ('user', 'Utilisateur'),
        ('user_xml_verifier', 'Vérificateur XML'),  
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    
    # Champs existants
    is_valid = models.BooleanField(default=False)
    can_view_files = models.BooleanField(default=False)
    
    # Nouveaux champs
    role = models.CharField(
        max_length=40,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name="Rôle"
    )
    fullname = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nom complet"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    # Permissions spécifiques
    can_view_all_files = models.BooleanField(default=False, verbose_name="Peut voir tous les fichiers")
    can_manage_users = models.BooleanField(default=False, verbose_name="Peut gérer les utilisateurs")
    
    # Relation ManyToMany pour les utilisateurs que le comptable peut voir
    can_view_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='viewed_by_comptables',
        verbose_name="Utilisateurs dont il peut voir les fichiers"
    )
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"



from django.db.models.signals import post_save
from django.dispatch import receiver

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.userprofile.save()