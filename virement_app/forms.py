# forms.py
from django import forms

class EmailForm(forms.Form):
    """
    Formulaire pour l'envoi d'email avec pièce jointe
    Permet à l'utilisateur de saisir ses propres identifiants email
    """
    
    # ===== SECTION 1 : PARAMÈTRES SMTP (EXPÉDITEUR) =====
    from_email = forms.EmailField(
        label="📧 Votre email (expéditeur)",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre.email@gmail.com',
            'required': 'required'
        }),
        help_text="L'adresse email qui enverra le message"
    )
    
    email_password = forms.CharField(
        label="🔐 Mot de passe de votre email",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '********',
            'required': 'required'
        }),
        help_text="Pour Gmail : utilisez un mot de passe d'application"
    )
    
    smtp_host = forms.CharField(
        label="🖥️ Serveur SMTP",
        initial='192.168.1.91',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'smtp.gmail.com'
        }),
        help_text="Ex: smtp.gmail.com, smtp.office365.com, etc."
    )
    
    smtp_port = forms.IntegerField(
        label="🔌 Port SMTP",
        initial=587,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '587'
        }),
        help_text="587 pour TLS, 465 pour SSL"
    )
    
    # ===== SECTION 2 : DESTINATAIRE =====
    to_email = forms.EmailField(
        label="📨 Email du destinataire",
        initial="tvarah@bnm.mr",  # 👈 Ajoutez cette ligne
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'destinataire@exemple.com',
            'required': 'required'
        }),
        help_text="L'adresse email qui recevra le fichier"
    )
    
    # ===== SECTION 3 : CONTENU DE L'EMAIL =====
    subject = forms.CharField(
        label="📝 Objet",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Objet de l\'email',
            'required': 'required'
        })
    )
    
    body = forms.CharField(
        label="💬 Message",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Écrivez votre message ici...',
            'required': 'required'
        })
    )
    
    def clean_smtp_port(self):
        """Validation personnalisée pour le port SMTP"""
        port = self.cleaned_data.get('smtp_port')
        if port not in [25, 465, 587, 2525]:
            raise forms.ValidationError(
                "Port SMTP invalide. Utilisez 25, 465, 587 ou 2525"
            )
        return port
    
    def clean(self):
        """Validation croisée des champs"""
        cleaned_data = super().clean()
        from_email = cleaned_data.get('from_email')
        to_email = cleaned_data.get('to_email')
        
        # Vérifier que l'expéditeur et le destinataire ne sont pas identiques
        if from_email and to_email and from_email == to_email:
            raise forms.ValidationError(
                "L'email expéditeur et destinataire ne peuvent pas être identiques"
            )
        
        return cleaned_data
    

    class EmailForm(forms.Form):
    # Copiez tout le code du formulaire EmailForm ici
      from_email = forms.EmailField(
        # ... etc ...
    )
    # ...
