# forms.py
from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class EmailForm(forms.Form):
    """
    Formulaire d'envoi d'email - Avec TO et CC
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
    
    # ===== DESTINATAIRES =====
    to_emails = forms.CharField(
        label="📨 Destinataires (TO)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'destinataire1@exemple.com\ndestinataire2@exemple.com',
            'rows': 3,
            'required': False
        }),
        help_text="Destinataires principaux - Un email par ligne",
        required=False
    )
    
    cc_emails = forms.CharField(
        label="📋 Copie (CC)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'cc1@exemple.com\ncc2@exemple.com',
            'rows': 2,
            'required': False
        }),
        help_text="Destinataires en copie - Un email par ligne (optionnel)",
        required=False
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
        """Valide chaque email des destinataires principaux"""
        emails_text = self.cleaned_data.get('to_emails', '')
        if not emails_text:
            return []
        return self._validate_emails_list(emails_text)
    
    def clean_cc_emails(self):
        """Valide chaque email des CC"""
        cc_data = self.cleaned_data.get('cc_emails', '')
        if not cc_data:
            return []
        return self._validate_emails_list(cc_data)
    
    def _validate_emails_list(self, emails_text):
        """Valide une liste d'emails"""
        if not emails_text:
            return []
        
        emails = [email.strip() for email in emails_text.split('\n') if email.strip()]
        
        if not emails:
            return []
        
        invalid_emails = []
        valid_emails = []
        
        for email in emails:
            try:
                validate_email(email)
                valid_emails.append(email)
            except ValidationError:
                invalid_emails.append(email)
        
        if invalid_emails:
            raise forms.ValidationError(
                f"Emails invalides : {', '.join(invalid_emails)}"
            )
        
        return list(dict.fromkeys(valid_emails))
    
    def clean(self):
        """Validation croisée des champs - Filtre automatiquement l'expéditeur"""
        cleaned_data = super().clean()
        
        to_emails = cleaned_data.get('to_emails', [])
        cc_emails = cleaned_data.get('cc_emails', [])
        from_email = cleaned_data.get('from_email')
        
        # 👈 FILTRER AUTOMATIQUEMENT L'EXPÉDITEUR DES DESTINATAIRES
        if from_email:
            # Filtrer TO
            if from_email in to_emails:
                to_emails = [email for email in to_emails if email != from_email]
                cleaned_data['to_emails'] = to_emails
            
            # Filtrer CC
            if from_email in cc_emails:
                cc_emails = [email for email in cc_emails if email != from_email]
                cleaned_data['cc_emails'] = cc_emails
        
        # Vérifier qu'il y a au moins un destinataire (TO ou CC)
        all_recipients = to_emails + cc_emails
        if not all_recipients:
            raise forms.ValidationError(
                "Veuillez entrer au moins un destinataire (TO ou CC)."
            )
        
        return cleaned_data