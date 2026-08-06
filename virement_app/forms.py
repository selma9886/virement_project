# forms.py
from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class EmailForm(forms.Form):
    """
    Formulaire d'envoi d'email - Version simplifiée
    """
    
    # ===== CHAMPS OBLIGATOIRES POUR L'UTILISATEUR =====
    from_email = forms.EmailField(
        label="📧 Votre email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre.email@gmail.com',
            'required': 'required'
        })
    )
    
    email_password = forms.CharField(
        label="🔐 Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '********',
            'required': 'required'
        })
    )
    
    to_emails = forms.CharField(
        label="📨 Destinataires",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'destinataire1@exemple.com\ndestinataire2@exemple.com',
            'rows': 4,
            'required': 'required'
        }),
        help_text="Un email par ligne"
    )
    
    # ===== CHAMPS CACHÉS AVEC VALEURS PAR DÉFAUT =====
    subject = forms.CharField(
        required=True,
        widget=forms.HiddenInput()
    )
    
    body = forms.CharField(
        required=True,
        widget=forms.HiddenInput()
    )
    
    smtp_host = forms.CharField(
        required=True,
        widget=forms.HiddenInput()
    )
    
    smtp_port = forms.IntegerField(
        required=True,
        widget=forms.HiddenInput()
    )
    
    def clean_to_emails(self):
        """Valide chaque email"""
        emails_text = self.cleaned_data.get('to_emails', '')
        emails = [email.strip() for email in emails_text.split('\n') if email.strip()]
        
        if not emails:
            raise forms.ValidationError("Veuillez entrer au moins un destinataire.")
        
        invalid_emails = []
        for email in emails:
            try:
                validate_email(email)
            except ValidationError:
                invalid_emails.append(email)
        
        if invalid_emails:
            raise forms.ValidationError(
                f"Emails invalides : {', '.join(invalid_emails)}"
            )
        
        # Supprimer les doublons
        return list(dict.fromkeys(emails))