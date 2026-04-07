# views.py
import os
import json
from datetime import datetime
import pandas as pd

from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, HttpResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.http import require_http_methods
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from virement_app.models import UserProfile

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import GeneratedXML
from django.core.mail import send_mail
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import GeneratedXML
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse  # ← AJOUTEZ CETTE LIGNE
from django.http import HttpResponse, HttpResponseNotFound
import os
import pandas as pd
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import GeneratedXML, EmailRecord
import os
from django.conf import settings


from django.db import transaction, connection
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
import json
from django.core.cache import cache
import logging

import os  # IMPORT AJOUTÉ EN HAUT DU FICHIER
from django.core.mail import EmailMessage
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import GeneratedXML
import traceback

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.shortcuts import get_object_or_404
from .forms import EmailForm
from .models import GeneratedXML, EmailRecord
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from .models import UserProfile
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import IntegrityError


BIC_MAP = {
    "00007": "AMDHMRMR",
    "00026": "AUBMMRMR",
    "00003": "BAAWMRMR",
    "00001": "BCEMMRMR",
    "00013": "BCMAMRMR",
    "00012": "BIIMMRMR",
    "00015": "BIMMMRMR",
    "00017": "BMSHMRMR",
    "00018": "BPMAMRMR",
    "00024": "BQMIMRMR",
    "00002": "BQNMMRMR",
    "00016": "CDDMMRXX",
    "00008": "COLIMRMR",
    "00004": "CZRZMRMR",
    "00021": "FIAQMRMR",
    "00006": "GBMCMRMR",
    "00025": "IBMRMRMR",
    "00010": "MBICMRMR",
    "00009": "ORBKMRMR",
    "00100": "BCEMMRMR"
}

PURPOSE_MAP = {
    "SALA": {"category": "SALA", "motif": "SALA"},
    "GOVT": {"category": "GOVT", "motif": "GOVT"},
    "OTHR": {"category": "CASH", "motif": "OTHR"},
    "CCP": {"category": "SALA", "motif": "SALA"},
}

DEBTOR_BIC = "BQNMMRMR"
CURRENCY = "MRU"
CCP_ACCOUNT = "00001000010000300110718"  # Fixed CCP account


def to_number(x):
    """Convertit une valeur en nombre."""
    try:
        if pd.isna(x):
            return 0.0
        if isinstance(x, str):
            x = x.replace(",", "").strip()
        return float(x)
    except Exception:
        return 0.0


def compute_cle_rib(rib):
    """Calcule la clé RIB mauritanienne (97 - mod 97)."""
    if not rib or not str(rib).isdigit() or len(str(rib)) != 23:
        return None
    rib = str(rib)
    banque = rib[0:5]
    agence = rib[5:10]
    compte = rib[10:21]
    try:
        rib_number = int(f"{banque}{agence}{compte}00")
        cle_calc = 97 - (rib_number % 97)
        return f"{cle_calc:02d}"
    except Exception:
        return None


def correct_rib(rib):
    """Retourne le RIB corrigé avec la bonne clé."""
    rib = str(rib)
    if not rib or len(rib) != 23:
        return None
    base = rib[:21]
    correct_key = compute_cle_rib(rib)
    if correct_key is None:
        return None
    return base + correct_key


COUNTER_FILE = os.path.join(settings.BASE_DIR, "counter.json")

def load_last_id():
    """Charge le dernier ID de transaction."""
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_id": 9000918401600000}, f)
        return 9000918401600000
    with open(COUNTER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("last_id", 9000918401600000)

def save_last_id(last_id):
    """Sauvegarde le dernier ID de transaction."""
    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_id": last_id}, f, indent=2)


def home(request):
    """Page d'accueil - redirige vers login ou index."""
    if request.user.is_authenticated:
        return redirect("login")
    return redirect("login")


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Si l'utilisateur est superuser, il est validé automatiquement
        is_valid = instance.is_superuser
        UserProfile.objects.create(user=instance, is_valid=is_valid)


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Superusers passent toujours
            if user.is_superuser or (hasattr(user, "userprofile") and user.userprofile.is_valid):
                login(request, user)
                messages.success(request, "")
                return redirect("admin_dashboard")
            
            messages.error(request, "❌ Votre compte n'est pas encore validé.")
            return redirect("login")
        
        messages.error(request, "Email ou mot de passe incorrect")
    
    return render(request, "login.html")


def register(request):
    if request.method == "POST":
        fullname = request.POST.get("fullname")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        role = request.POST.get("role", "user")
        
        # Validation
        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas")
            return render(request, "register.html")
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé")
            return render(request, "register.html")
        
        try:
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password1,
                first_name=fullname
            )
            
            # Utiliser get_or_create pour éviter les doublons
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'is_valid': False,
                    'can_view_files': False,
                    'role': role,
                    'fullname': fullname
                }
            )
            
            # Si le profil existait déjà, le mettre à jour
            if not created:
                profile.is_valid = False
                profile.can_view_files = False
                profile.role = role
                profile.fullname = fullname
                profile.save()
            
            # Si c'est un admin, le valider automatiquement
            if role == 'admin':
                profile.is_valid = True
                profile.can_view_files = True
                profile.save()
                messages.success(request, "Compte admin créé avec succès! Vous pouvez vous connecter.")
            else:
                messages.success(request, "Compte créé avec succès! En attente de validation par l'administrateur.")
            
            return redirect("login")
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création du compte: {str(e)}")
            return render(request, "register.html")
    
    return render(request, "register.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Déconnexion réussie")
    return redirect("login")


@login_required
def admin_dashboard(request):
    # Récupération des données
    files = GeneratedXML.objects.select_related('user').order_by('-created_at')
    users = User.objects.all().order_by('-date_joined')
    emails = EmailRecord.objects.all().order_by('-sent_at')

    # Statistiques
    total_files = files.count()
    total_users = users.count()
    total_emails = emails.count()

    # Calcul taille totale
    total_size_bytes = 0
    for file in files:
        if file.file_name:
            file_path = os.path.join(settings.MEDIA_ROOT, 'generated_xml', file.file_name)
            if os.path.exists(file_path):
                total_size_bytes += os.path.getsize(file_path)

    total_size_mb = round(total_size_bytes / (1024 * 1024), 2) if total_size_bytes else 0

    # Context
    context = {
        'total_files': total_files,
        'total_users': total_users,
        'total_emails': total_emails,
        'total_size': total_size_mb,
    }

    return render(request, "admin_dashboard.html", context)

@login_required
def user_dashboard(request):
    """Dashboard utilisateur standard"""
    # Vérifier si l'utilisateur peut voir les fichiers
    if hasattr(request.user, "userprofile"):
        if not request.user.userprofile.is_valid:
            messages.warning(request, "⚠️ Votre compte est en attente de validation par l'administrateur.")
        elif not request.user.userprofile.can_view_files:
            messages.info(request, "ℹ️ Vous n'avez pas encore accès aux fichiers. Contactez l'administrateur.")
    
    return render(request, "user_dashboard.html", {'user': request.user})


@login_required
def index(request):
    """Page principale d'upload."""
    return render(request, "upload.html")


@login_required
@require_http_methods(["POST"])
def upload_file(request):
    """Traitement du fichier Excel uploadé."""
    purpose_code = request.POST.get("purpose")
    if not purpose_code or purpose_code not in PURPOSE_MAP:
        messages.error(request, "Veuillez sélectionner un type de virement valide.")
        return redirect("index")
    
    file = request.FILES.get("file")
    if not file or file.name == "":
        messages.error(request, "Aucun fichier sélectionné.")
        return redirect("index")
    
    # Sauvegarder le fichier
    upload_path = os.path.join(settings.MEDIA_ROOT, "uploads", file.name)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    
    with open(upload_path, "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    # Lire le fichier Excel
    try:
        df = pd.read_excel(upload_path, dtype=str)
    except Exception as e:
        messages.error(request, f"Erreur lecture Excel : {e}")
        return redirect("index")
    
    # Vérifier les colonnes requises
    required_cols = ["RIB_tirer", "Nom_tirer", "RIB_Destinateur", "Nom_Prenom_Beneficaire", "Montant"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        messages.error(request, f"Colonnes manquantes : {', '.join(missing)}")
        return redirect("index")
    
    # Validation des RIBs
    invalid_ribs = []
    invalid_banks = []
    invalid_length = []
    rib_corrections = []
    
    # Vérifier le RIB débiteur
    debtor_account = str(df.iloc[0]["RIB_tirer"]).strip()
    
    if len(debtor_account) != 23:
        invalid_length.append((2, debtor_account, len(debtor_account), "Débiteur"))
    else:
        debtor_bank_code = debtor_account[:5]
        if debtor_bank_code not in BIC_MAP:
            invalid_banks.append((2, debtor_account, debtor_bank_code, "Débiteur"))
        else:
            expected_cle_tirer = compute_cle_rib(debtor_account)
            if expected_cle_tirer is None or debtor_account[-2:] != expected_cle_tirer:
                corrected_rib_tirer = correct_rib(debtor_account)
                rib_corrections.append({
                    "line": 2,
                    "type": "Débiteur",
                    "name": str(df.iloc[0]["Nom_tirer"]).strip(),
                    "original": debtor_account,
                    "corrected": corrected_rib_tirer,
                    "original_key": debtor_account[-2:],
                    "correct_key": expected_cle_tirer
                })
    
    # Vérifier les RIBs bénéficiaires
    for idx, row in df.iterrows():
        rib_dest = str(row["RIB_Destinateur"]).strip()
        beneficiary_name = str(row["Nom_Prenom_Beneficaire"]).strip()
        
        if len(rib_dest) != 23:
            invalid_length.append((idx + 2, rib_dest, len(rib_dest), beneficiary_name))
            continue
        
        bank_code = rib_dest[:5]
        if bank_code not in BIC_MAP:
            invalid_banks.append((idx + 2, rib_dest, bank_code, beneficiary_name))
            continue
        
        expected = compute_cle_rib(rib_dest)
        actual = rib_dest[-2:] if len(rib_dest) >= 2 else ""
        if expected is None or expected != actual:
            corrected_rib = correct_rib(rib_dest)
            rib_corrections.append({
                "line": idx + 2,
                "type": "Bénéficiaire",
                "name": beneficiary_name,
                "original": rib_dest,
                "corrected": corrected_rib,
                "original_key": actual,
                "correct_key": expected
            })
    
    # Gérer les erreurs
    if invalid_length:
        msg = "<br>".join([
            f"Ligne {l} ({t}): RIB doit contenir 23 chiffres, trouvé {length} chiffres<br>RIB: <code>{r}</code>" 
            for l, r, length, t in invalid_length
        ])
        messages.error(request, f"❌ RIBs avec longueur invalide:<br>{msg}")
        return redirect("index")
    
    if invalid_banks:
        msg = "<br>".join([
            f"Ligne {l} ({t}): code banque <strong>{b}</strong> inconnu<br>RIB: <code>{r}</code>" 
            for l, r, b, t in invalid_banks
        ])
        messages.error(request, f"❌ Codes banque non reconnus:<br>{msg}")
        return redirect("index")
    
    # Stocker les informations en session
    request.session["filename"] = file.name
    request.session["purpose_code"] = purpose_code
    
    if rib_corrections:
        request.session["rib_corrections"] = rib_corrections
        return redirect("confirm_corrections")
    
    # Pas de corrections nécessaires, générer directement le XML
    return generate_xml(request, apply_corrections=False)



@login_required
def confirm_corrections(request):
    """Page de confirmation des corrections RIB."""
    corrections = request.session.get("rib_corrections", [])
    if not corrections:
        messages.info(request, "Aucune correction à confirmer.")
        return redirect("index")
    
    return render(request, "confirm_corrections.html", {"corrections": corrections})


@login_required
@require_http_methods(["POST"])
def process_corrections(request):
    """Traitement de la confirmation des corrections."""
    choice = request.POST.get("choice")
    filename = request.session.get("filename")
    purpose_code = request.session.get("purpose_code")
    
    if not filename or not purpose_code:
        messages.error(request, "Session expirée. Veuillez réessayer.")
        return redirect("index")
    
    if choice == "yes":
        return generate_xml(request, apply_corrections=True)
    else:
        messages.warning(request, "❌ Génération annulée. Veuillez corriger les RIBs dans votre fichier Excel.")
        # Nettoyer la session
        request.session.pop("rib_corrections", None)
        request.session.pop("filename", None)
        request.session.pop("purpose_code", None)
        return redirect("index")

# views.py
@login_required
def generate_xml(request, apply_corrections=False):
    """Génère le fichier XML et enregistre l'information dans la base."""
    from .models import GeneratedXML  # Assurez-vous que le modèle est importé ici

    filename = request.session.get("filename")
    purpose_code = request.session.get("purpose_code")
    excel_file = request.FILES.get("file")

    if not filename or not purpose_code:
        messages.error(request, "Session expirée. Veuillez réessayer.")
        return redirect("index")
    
    category_code = PURPOSE_MAP[purpose_code]["category"]
    motif_code = PURPOSE_MAP[purpose_code]["motif"]
    is_ccp = (purpose_code == "CCP")
    
    file_path = os.path.join(settings.MEDIA_ROOT, "uploads", filename)
    
    try:
        df = pd.read_excel(file_path, dtype=str)
    except Exception as e:
        messages.error(request, f"Erreur lecture Excel : {e}")
        return redirect("index")
    
    # Appliquer les corrections si nécessaire
    if apply_corrections:
        corrections = request.session.get("rib_corrections", [])
        for correction in corrections:
            line_idx = correction["line"] - 2
            if correction["type"] == "Débiteur":
                df.at[0, "RIB_tirer"] = correction["corrected"]
            else:
                df.at[line_idx, "RIB_Destinateur"] = correction["corrected"]
    
    # Préparer les montants et informations
    df["Montant_num"] = df["Montant"].apply(to_number)
    debtor_account = str(df.iloc[0]["RIB_tirer"]).strip()
    debtor_name = str(df.iloc[0]["Nom_tirer"]).strip()
    total_amount = df["Montant_num"].sum()
    settlement_system = "ACH" if total_amount < 3000000 else "RTGS"
    
    now = datetime.utcnow()
    creation_dt = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    intrbk_date = now.strftime("%Y-%m-%d")
    nb_of_txs = len(df)
    
    # Création du XML
    root = Element("Document", {
        "xmlns": "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.07",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"
    })
    ftof = SubElement(root, "FIToFICstmrCdtTrf")
    
    # En-tête du groupe
    grp_hdr = SubElement(ftof, "GrpHdr")
    msg_id = f"{DEBTOR_BIC}{now.strftime('%Y%m%d%H%M%S')}"
    SubElement(grp_hdr, "MsgId").text = msg_id
    SubElement(grp_hdr, "CreDtTm").text = creation_dt
    SubElement(grp_hdr, "NbOfTxs").text = str(nb_of_txs)
    ttl_amt = SubElement(grp_hdr, "TtlIntrBkSttlmAmt", Ccy=CURRENCY)
    ttl_amt.text = str(int(total_amount)) if total_amount.is_integer() else str(total_amount)
    SubElement(grp_hdr, "IntrBkSttlmDt").text = intrbk_date
    
    # Informations de règlement
    sttlm_inf = SubElement(grp_hdr, "SttlmInf")
    SubElement(sttlm_inf, "SttlmMtd").text = "CLRG"
    clr_sys = SubElement(sttlm_inf, "ClrSys")
    SubElement(clr_sys, "Prtry").text = settlement_system
    
    # Agent instructeur
    instg = SubElement(grp_hdr, "InstgAgt")
    fin_id = SubElement(instg, "FinInstnId")
    SubElement(fin_id, "BICFI").text = DEBTOR_BIC
    
    last_id = load_last_id()
    
    # Création des transactions
    for _, row in df.iterrows():
        tx = SubElement(ftof, "CdtTrfTxInf")
        unique_id = str(last_id + 1)
        last_id += 1
        
        # Identifiants de paiement
        pmt_id = SubElement(tx, "PmtId")
        for tag in ["InstrId", "EndToEndId", "TxId"]:
            SubElement(pmt_id, tag).text = unique_id
        
        # Type de paiement
        pmt_tp_inf = SubElement(tx, "PmtTpInf")
        svc_lvl = SubElement(pmt_tp_inf, "SvcLvl")
        SubElement(svc_lvl, "Cd").text = "SEPA"
        lcl_instrm = SubElement(pmt_tp_inf, "LclInstrm")
        SubElement(lcl_instrm, "Cd").text = "B2B"
        ctgy_purp = SubElement(pmt_tp_inf, "CtgyPurp")
        SubElement(ctgy_purp, "Cd").text = category_code
        
        # Montant
        amt = SubElement(tx, "IntrBkSttlmAmt", Ccy=CURRENCY)
        val = float(row["Montant_num"])
        amt.text = str(int(val)) if val.is_integer() else str(val)
        SubElement(tx, "ChrgBr").text = "DEBT"
        
        # Débiteur
        dbtr = SubElement(tx, "Dbtr")
        SubElement(dbtr, "Nm").text = debtor_name
        dbtr_acct = SubElement(tx, "DbtrAcct")
        dbtr_id = SubElement(dbtr_acct, "Id")
        debtor_account_11 = debtor_account[10:21] if len(debtor_account) >= 21 else debtor_account
        SubElement(SubElement(dbtr_id, "Othr"), "Id").text = debtor_account_11
        SubElement(SubElement(SubElement(tx, "DbtrAgt"), "FinInstnId"), "BICFI").text = DEBTOR_BIC
        
        # Pour CCP : utiliser le compte fixe
        if is_ccp:
            cdtr_rib = CCP_ACCOUNT
            dst_bic = BIC_MAP.get(CCP_ACCOUNT[:5], DEBTOR_BIC)
        else:
            cdtr_rib = str(row["RIB_Destinateur"]).strip()
            dst_bic = BIC_MAP.get(cdtr_rib[:5], "")
        
        # Agent créditeur
        SubElement(SubElement(SubElement(tx, "CdtrAgt"), "FinInstnId"), "BICFI").text = dst_bic
        
        # Créditeur
        cdtr = SubElement(tx, "Cdtr")
        SubElement(cdtr, "Nm").text = "CCP" if is_ccp else str(row["Nom_Prenom_Beneficaire"]).strip()
        
        # Compte créditeur
        cdtr_acct = SubElement(tx, "CdtrAcct")
        cdtr_id = SubElement(cdtr_acct, "Id")
        SubElement(SubElement(cdtr_id, "Othr"), "Id").text = cdtr_rib
        
        # Informations de remise
        rmt_inf = SubElement(tx, "RmtInf")
        if is_ccp:
            beneficiary_name = str(row["Nom_Prenom_Beneficaire"]).strip()
            original_rib = str(row["RIB_Destinateur"]).strip()
            SubElement(rmt_inf, "Ustrd").text = f"fav {beneficiary_name} {original_rib}"
        else:
            SubElement(rmt_inf, "Ustrd").text = unique_id
    
    # Générer le XML en texte
    xml_str = parseString(tostring(root)).toprettyxml(indent="  ")
    
    # Sauvegarder le fichier XML sur disque
    out_filename = f"{os.path.splitext(filename)[0]}_{now.strftime('%Y%m%d%H%M%S')}.xml"
    out_path = os.path.join(settings.MEDIA_ROOT, "outputs", out_filename)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml_str)
    
    # ===================================================================
    # PARTIE MODIFIÉE : Enregistrement avec plus d'informations
    # ===================================================================
    # Au lieu de GeneratedXML.objects.create(...) simple,
    # on crée maintenant avec toutes les informations disponibles
    
    generated_xml = GeneratedXML.objects.create(
        user=request.user,
        file_name=out_filename,
        file_path=out_path,
        excel_file=excel_file,
        purpose_code=purpose_code,  # Code de finalité (SAL, FAC, CCP, etc.)
        total_amount=total_amount,  # Montant total de toutes les transactions
        transaction_count=nb_of_txs  # Nombre de transactions/lignes
    )
    
    # Stocker l'ID dans la session pour l'utiliser plus tard (pour les modales email)
    request.session["last_generated_xml_id"] = generated_xml.id
    
    # Optionnel : Stocker aussi dans une variable de session plus générale
    request.session["last_generated_file_id"] = generated_xml.id
    request.session["last_generated_file"] = out_filename
    
    
    save_last_id(last_id)
    
    # Nettoyer la session
    request.session.pop("rib_corrections", None)
    request.session.pop("filename", None)
    request.session.pop("purpose_code", None)
    
    # Messages pour l'utilisateur
    correction_msg = "✅ Les RIBs ont été corrigés automatiquement.<br>" if apply_corrections else ""
    ccp_msg = f"ℹ️ Type CCP: Tous les virements utilisent le compte {CCP_ACCOUNT}.<br>" if is_ccp else ""
    
    # Message enrichi avec les informations de résumé
    # messages.success(
    #     request,
    #     f"✅ Conversion réussie : {nb_of_txs} transactions.<br>"
    #     f"{correction_msg}"
    #     f"{ccp_msg}"
    #     f"💰 Montant total : {total_amount:,.2f} {CURRENCY}<br>"
    #     f"📂 Fichier généré : {out_filename}<br><br>"
    #     f"⚠️ <strong>IMPORTANT :</strong> Ce fichier doit être envoyé à la BCM via ATS <u>avant la fin de la journée</u>."
    # )
    
    # Rediriger vers la page de téléchargement qui affichera la modale email
    return redirect("download_file", filename=out_filename)

@login_required
def download_file(request, filename):
    """Télécharge le fichier généré et propose l'envoi par email"""
    file_path = os.path.join(settings.MEDIA_ROOT, "outputs", filename)
    
    if not os.path.exists(file_path):
        messages.error(request, "Le fichier n'existe pas.")
        return redirect("index")
    
    # Récupérer l'ID du fichier
    try:
        generated_xml = GeneratedXML.objects.get(file_name=filename, user=request.user)
        file_id = generated_xml.id
    except GeneratedXML.DoesNotExist:
        file_id = request.session.get("last_generated_xml_id")
    
    # Page avec modale
    context = {
        'filename': filename,
        'show_email_modal': True,
        'file_id': file_id
    }
    
    response = render(request, 'download_page.html', context)
    # Téléchargement automatique après 2 secondes - UTILISE reverse CORRECTEMENT
    response['Refresh'] = f"2;url={reverse('serve_file', args=[filename])}"
    
    return response

@login_required
def serve_file(request, filename):
    """Sert le fichier pour téléchargement"""
    file_path = os.path.join(settings.MEDIA_ROOT, "outputs", filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/xml")
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    return HttpResponseNotFound("Fichier non trouvé")

@login_required
def download_template(request):
    """Télécharge le template Excel."""
    template_path = os.path.join(settings.BASE_DIR, "static", "template_virement.xlsx")
    
    # Créer le template s'il n'existe pas
    if not os.path.exists(template_path):
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        template_df = pd.DataFrame(columns=[
            "RIB_tirer", "Nom_tirer", "RIB_Destinateur", 
            "Nom_Prenom_Beneficaire", "Montant"
        ])
        template_df.to_excel(template_path, index=False)
    
    return FileResponse(open(template_path, "rb"), as_attachment=True)


@login_required
@require_http_methods(["GET", "POST"])
def change_password(request):
    """Change le mot de passe de l'utilisateur."""
    if request.method == "POST":
        old = request.POST.get("old_password")
        new = request.POST.get("new_password")
        confirm = request.POST.get("confirm_password")
        
        if not request.user.check_password(old):
            messages.error(request, "❌ Ancien mot de passe incorrect.")
            return redirect("change_password")
        
        if new != confirm:
            messages.error(request, "❌ Les nouveaux mots de passe ne correspondent pas.")
            return redirect("change_password")
        
        request.user.set_password(new)
        request.user.save()
        
        # Re-authentifier l'utilisateur
        user = authenticate(request, username=request.user.username, password=new)
        if user:
            login(request, user)
        
        messages.success(request, "✅ Mot de passe mis à jour avec succès.")
        return redirect("index")
    
    return render(request, "change_password.html")


logger = logging.getLogger(__name__)

@login_required
def generated_files(request):
    """
    Affiche les fichiers générés selon le rôle et les permissions
    """
    user = request.user
    try:
        user_profile = user.userprofile
        # Rafraîchir depuis la base pour éviter le cache
        user_profile.refresh_from_db()
    except UserProfile.DoesNotExist:
        # Si le profil n'existe pas, le créer
        user_profile = UserProfile.objects.create(
            user=user,
            fullname=user.get_full_name() or user.email,
            role='user',
            can_view_files=False,
            can_view_all_files=False,
            can_manage_users=False,
            is_valid=True
        )
    
    # Récupérer tous les fichiers avec les relations nécessaires
    all_files = GeneratedXML.objects.select_related('user').order_by('-created_at')
    
    # Filtrer selon le rôle
    if user.is_superuser or user_profile.role == 'admin':
        # Admin voit tous les fichiers
        files = all_files
        
    elif user_profile.role == 'comptable':
        if user_profile.can_view_all_files:
            # Comptable avec accès à tous les fichiers
            files = all_files
            logger.info(f"Comptable {user.email} - Accès à tous les fichiers")
        else:
            allowed_user_ids = list(user_profile.can_view_users.values_list('id', flat=True))
            # Inclure ses propres fichiers
            if user.id not in allowed_user_ids:
                allowed_user_ids.append(user.id)
            
            files = all_files.filter(user_id__in=allowed_user_ids)
            
            logger.info(f"Comptable {user.email} - Accès limité à {len(allowed_user_ids)} utilisateurs")
            logger.info(f"IDs autorisés: {allowed_user_ids}")
            logger.info(f"Nombre de fichiers trouvés: {files.count()}")
            
    elif user_profile.role == 'user':
        # Utilisateur normal voit ses propres fichiers
        files = all_files.filter(user=user)
        logger.info(f"Utilisateur normal {user.email} - {files.count()} fichiers")
        
    else:
        files = []
    
    # Récupérer tous les utilisateurs pour l'affichage (sauf l'utilisateur courant)
    all_users = User.objects.exclude(id=user.id).select_related('userprofile')
    
    context = {
        'files': files,
        'active_tab': 'files',
        'users': all_users,
    }
    
    return render(request, "generated_files.html", context)

# @login_required
# def generated_files(request):
#     """
#     Affiche les fichiers générés selon le rôle et les permissions
#     - Si can_view_files = True: Affiche tous les fichiers (ou fichiers spécifiques)
#     - Si can_view_files = False: Affiche uniquement ses propres fichiers
#     """
#     user = request.user
#     try:
#         user_profile = user.userprofile
#         # Rafraîchir depuis la base pour éviter le cache
#         user_profile.refresh_from_db()
#     except UserProfile.DoesNotExist:
#         # Si le profil n'existe pas, le créer
#         user_profile = UserProfile.objects.create(
#             user=user,
#             fullname=user.get_full_name() or user.email,
#             role='user',
#             can_view_files=False,
#             can_view_all_files=False,
#             can_manage_users=False,
#             is_valid=True
#         )
    
#     # Récupérer tous les fichiers avec les relations nécessaires
#     all_files = GeneratedXML.objects.select_related('user').order_by('-created_at')
    
#     # Vérification de can_view_files
#     if user_profile.can_view_files:
#         # 🔓 can_view_files = True: Afficher TOUS les fichiers (ou un autre ensemble)
#         files = all_files  # Affiche tous les fichiers de tous les utilisateurs
#         logger.info(f"Utilisateur {user.email} - can_view_files=True: Accès à tous les fichiers ({files.count()})")
#     else:
#         # 🔒 can_view_files = False: Garder le comportement normal selon le rôle
#         if user.is_superuser or user_profile.role == 'admin':
#             # Admin voit tous les fichiers
#             files = all_files
            
#         elif user_profile.role == 'comptable':
#             if user_profile.can_view_all_files:
#                 # Comptable avec accès à tous les fichiers
#                 files = all_files
#                 logger.info(f"Comptable {user.email} - Accès à tous les fichiers")
#             else:
#                 allowed_user_ids = list(user_profile.can_view_users.values_list('id', flat=True))
#                 # Inclure ses propres fichiers
#                 if user.id not in allowed_user_ids:
#                     allowed_user_ids.append(user.id)
                
#                 files = all_files.filter(user_id__in=allowed_user_ids)
                
#                 logger.info(f"Comptable {user.email} - Accès limité à {len(allowed_user_ids)} utilisateurs")
#                 logger.info(f"IDs autorisés: {allowed_user_ids}")
#                 logger.info(f"Nombre de fichiers trouvés: {files.count()}")
                
#         elif user_profile.role == 'user':
#             # Utilisateur normal voit ses propres fichiers
#             files = all_files.filter(user=user)
#             logger.info(f"Utilisateur normal {user.email} - {files.count()} fichiers")
            
#         else:
#             files = []
    
#     # Récupérer tous les utilisateurs pour l'affichage (sauf l'utilisateur courant)
#     all_users = User.objects.exclude(id=user.id).select_related('userprofile')
    
#     context = {
#         'files': files,
#         'active_tab': 'files',
#         'users': all_users,
#         'can_view_files': user_profile.can_view_files,  # Passer au template
#     }
    
#     return render(request, "generated_files.html", context)

def is_admin(user):
    return user.is_superuser

@login_required

def manage_users(request):
    users = User.objects.select_related("userprofile").all()
    return render(request, "manage_users.html", {"users": users})


def toggle_validation(request, user_id):
    """Active ou désactive la validation de l'utilisateur."""
    try:
        user = User.objects.get(id=user_id)
        
        # Try to get the profile, create it if it doesn't exist
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        profile.is_valid = not profile.is_valid
        profile.save()
        
        if created:
            messages.success(request, f"Profil créé pour {user.username}. Validation: {profile.is_valid}")
        else:
            messages.success(request, f"Validation modifiée pour {user.username}: {profile.is_valid}")
            
        return redirect("manage_users")
        
    except User.DoesNotExist:
        messages.error(request, "Utilisateur non trouvé")
        return redirect("manage_users")

@login_required
def toggle_file_access(request, user_id):
    """Active ou désactive le droit de voir les fichiers générés."""
    try:
        user = User.objects.get(id=user_id)
        profile = user.userprofile
        profile.can_view_files = not profile.can_view_files
        profile.save()
        return redirect("manage_users")
    except User.DoesNotExist:
        return redirect("manage_users")


@login_required
def my_generated_files(request):
    """
    Affiche les fichiers XML générés par l'utilisateur connecté.
    """
    # Récupérer uniquement les fichiers générés par cet utilisateur
    files = GeneratedXML.objects.filter(user=request.user).order_by('-created_at')

    return render(request, "my_generated_files.html", {"files": files})


@login_required
def send_file_email(request):
    if request.method == "POST":
        file_id = request.POST.get("file_id")
        recipient_email = request.POST.get("recipient_email")
        
        print(f"Tentative d'envoi: fichier {file_id} vers {recipient_email}")  # Debug
        
        # Validation
        if not recipient_email:
            messages.error(request, "❌ Veuillez spécifier un email destinataire")
            return redirect("my_generated_files")

        try:
            # Récupérer le fichier
            file_obj = get_object_or_404(GeneratedXML, id=file_id, user=request.user)
            
            # CONSTRUCTION DU CHEMIN - Version simplifiée car nous connaissons la structure du modèle
            from django.conf import settings
            
            # Le champ file_path contient déjà le chemin complet
            file_path = file_obj.file_path
            print(f"Chemin du fichier: {file_path}")
            
            # Vérifier si le chemin est absolu ou relatif
            if not os.path.isabs(file_path):
                # Si c'est un chemin relatif, le joindre avec MEDIA_ROOT
                abs_path = os.path.join(settings.MEDIA_ROOT, file_path)
                if os.path.exists(abs_path):
                    file_path = abs_path
                else:
                    messages.error(request, f"❌ Le fichier n'existe pas: {file_path}")
                    return redirect("my_generated_files")
            else:
                # Chemin absolu, vérifier directement
                if not os.path.exists(file_path):
                    messages.error(request, f"❌ Le fichier n'existe pas: {file_path}")
                    return redirect("my_generated_files")
            
            file_name = os.path.basename(file_path)
            print(f"Fichier trouvé: {file_path}")
            
            # Mettre à jour l'email destinataire dans le modèle
            file_obj.recipient_email = recipient_email
            file_obj.save()
            
            # Créer l'email
            email = EmailMessage(
                subject=f"Fichier XML généré : {file_name}",
                body=f"""
                Bonjour,
                
                Veuillez trouver le fichier XML "{file_name}" en pièce jointe.
                
                Ce fichier a été généré par {request.user.username} ({request.user.email}).
                
                Cordialement,
                L'équipe
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
                reply_to=[request.user.email] if request.user.email else [settings.DEFAULT_FROM_EMAIL],
            )
            
            # Ajouter la pièce jointe
            email.attach_file(file_path)
            
            # Envoyer
            email.send(fail_silently=False)
            
            messages.success(
                request, 
                f"✅ Email envoyé avec succès à {recipient_email}"
            )
            
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"ERREUR DÉTAILLÉE: {error_trace}")
            messages.error(
                request, 
                f"❌ Erreur lors de l'envoi : {str(e)}"
            )
    
    return redirect("my_generated_files")
  

@login_required
def ask_send_email(request, file_id):
    """Première modale : Voulez-vous envoyer par email?"""
    generated_xml = get_object_or_404(GeneratedXML, id=file_id, user=request.user)
    
    context = {
        'file_id': file_id,
        'file_name': generated_xml.file_name
    }
    return render(request, 'ask_send_email.html', context)

# @login_required
# def send_email_form(request, file_id):
#     """Deuxième modale : Formulaire d'envoi d'email"""
#     generated_xml = get_object_or_404(GeneratedXML, id=file_id, user=request.user)
    
#     if request.method == 'POST':
#         form = EmailForm(request.POST)
#         if form.is_valid():
#             # Récupérer les données du formulaire
#             data = form.cleaned_data
            
#             try:
#                 # Créer le message
#                 msg = MIMEMultipart()
#                 msg['From'] = data['from_email']
#                 msg['To'] = data['to_email']
#                 msg['Subject'] = data['subject']
#                 msg.attach(MIMEText(data['body'], 'plain'))
                
#                 # Ajouter la pièce jointe (fichier XML)
#                 with open(generated_xml.file_path, "rb") as attachment:
#                     part = MIMEBase("application", "octet-stream")
#                     part.set_payload(attachment.read())
                
#                 encoders.encode_base64(part)
#                 part.add_header(
#                     "Content-Disposition",
#                     f"attachment; filename={generated_xml.file_name}",
#                 )
#                 msg.attach(part)
                
#                 # Connexion au serveur SMTP
#                 if data['smtp_port'] == 587:
#                     server = smtplib.SMTP(data['smtp_host'], data['smtp_port'])
#                     server.starttls()
#                 else:
#                     server = smtplib.SMTP_SSL(data['smtp_host'], data['smtp_port'])
                
#                 # Authentification et envoi
#                 server.login(data['from_email'], data['email_password'])
#                 server.send_message(msg)
#                 server.quit()
                
#                 # Enregistrer le succès
#                 EmailRecord.objects.create(
#                     user=request.user,
#                     generated_xml=generated_xml,
#                     from_email=data['from_email'],
#                     to_email=data['to_email'],
#                     subject=data['subject'],
#                     body=data['body'],
#                     status='sent'
#                 )
                
#                 messages.success(request, f"✅ Email envoyé avec succès à {data['to_email']}")
                
#             except Exception as e:
#                 # Enregistrer l'échec
#                 EmailRecord.objects.create(
#                     user=request.user,
#                     generated_xml=generated_xml,
#                     from_email=data.get('from_email', ''),
#                     to_email=data.get('to_email', ''),
#                     subject=data.get('subject', ''),
#                     body=data.get('body', ''),
#                     status='failed',
#                     error_message=str(e)
#                 )
                
#                 messages.error(request, f"❌ Erreur lors de l'envoi : {str(e)}")
            
#             return redirect('download_file', filename=generated_xml.file_name)
#     else:
#         # Formulaire initial avec l'email de l'utilisateur
#         initial_data = {
#             'from_email': request.user.email,
#             'subject': f"Fichier XML de virement - {generated_xml.file_name}",
#             'body': f"Bonjour,\n\nVeuillez trouver ci-joint le fichier XML de virement généré le {generated_xml.created_at.strftime('%d/%m/%Y à %H:%M')}.\n\nCordialement,"
#         }
#         form = EmailForm(initial=initial_data)
    
#     context = {
#         'form': form,
#         'file_id': file_id,
#         'file_name': generated_xml.file_name
#     }
#     return render(request, 'send_email_form.html', context)

@login_required
def send_email_form(request, file_id):
    """Formulaire d'envoi d'email"""
    
    generated_xml = get_object_or_404(GeneratedXML, id=file_id)
    
    # Vérifier les permissions
    user_profile = request.user.userprofile
    is_admin = request.user.is_superuser or user_profile.role == 'admin'
    
    if not is_admin and generated_xml.user != request.user:
        messages.error(request, "❌ Vous n'avez pas la permission d'envoyer ce fichier.")
        return redirect('generated-files')
    
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            try:
                # ... votre code d'envoi d'email ...
                
                # Enregistrement du succès
                EmailRecord.objects.create(
                    user=request.user,
                    generated_xml=generated_xml,
                    from_email=data['from_email'],
                    to_email=data['to_email'],
                    subject=data['subject'],
                    body=data['body'],
                    status='sent'
                )
                
                # ✅ MESSAGE SIMPLE SANS DÉTAILS
                messages.success(request, "✅ Email envoyé avec succès !")
                
            except Exception as e:
                # Enregistrement de l'échec
                EmailRecord.objects.create(
                    user=request.user,
                    generated_xml=generated_xml,
                    from_email=data.get('from_email', ''),
                    to_email=data.get('to_email', ''),
                    subject=data.get('subject', ''),
                    body=data.get('body', ''),
                    status='failed',
                    error_message=str(e)
                )
                
                # ❌ MESSAGE D'ERREUR SIMPLE
                messages.error(request, "❌ Échec de l'envoi de l'email. Veuillez réessayer.")
            
            return render(request, 'send_email_form.html')
    else:
        # Formulaire initial
        initial_data = {
            'from_email': request.user.email,
            'subject': f"Fichier XML de virement - {generated_xml.file_name}",
            'body': f"Bonjour,\n\nVeuillez trouver ci-joint le fichier XML de virement généré le {generated_xml.created_at.strftime('%d/%m/%Y à %H:%M')}.\n\nCordialement,"
        }
        
        if is_admin and generated_xml.user != request.user:
            initial_data['body'] += f"\n\nNote: Ce fichier a été généré par {generated_xml.user.username}"
        
        form = EmailForm(initial=initial_data)
    
    context = {
        'form': form,
        'file_id': file_id,
        'file_name': generated_xml.file_name,
        'file_owner': generated_xml.user if is_admin and generated_xml.user != request.user else None,
    }
    return render(request, 'send_email_form.html', context)

@login_required
def skip_send_email(request, file_id):
    """Action quand l'utilisateur choisit de ne pas envoyer par email"""
    generated_xml = get_object_or_404(GeneratedXML, id=file_id, user=request.user)
    messages.info(request, "Envoi par email ignoré. Vous pouvez télécharger le fichier.")
    return redirect('download_file', filename=generated_xml.file_name)

@login_required
def email_history(request):
    """Historique des emails envoyés"""
    emails = EmailRecord.objects.filter(user=request.user).order_by('-sent_at')
    return render(request, 'email_history.html', {'emails': emails})

@login_required
def delete_generated_file(request, id):
    file = get_object_or_404(GeneratedXML, id=id, user=request.user)
    
    # Supprimer le fichier XML s'il existe
    if file.file_path and os.path.exists(file.file_path):
        os.remove(file.file_path)
    
    # Supprimer le fichier Excel s'il existe
    if file.excel_file and os.path.exists(file.excel_file.path):
        os.remove(file.excel_file.path)
    
    # Supprimer l'objet en base
    file.delete()
    
    messages.success(request, "✅ Fichier supprimé avec succès.")
    
    # Redirige vers l’historique des fichiers (nom valide)
    return redirect('generated-files')

def delete_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, id=user_id)
        user.delete()
        messages.success(request, "Utilisateur supprimé avec succès")
    return redirect('manage_users')  # redirige vers la page de gestion


@csrf_exempt  # temporaire pour test, mieux utiliser le CSRF token
def edit_user(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            user.first_name = request.POST.get('first_name')
            user.email = request.POST.get('email')
            role = request.POST.get('role')
            user.is_superuser = True if role == 'admin' else False
            password = request.POST.get('password')
            if password:
                user.set_password(password)
            user.save()
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Utilisateur non trouvé'})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})



    from django.shortcuts import render, redirect, get_object_or_404

def is_admin(user):
    """Vérifie si l'utilisateur est admin"""
    return user.is_superuser or (hasattr(user, 'userprofile') and user.userprofile.role == 'admin')
# Vérifie que l'utilisateur est admin

def is_admin(user):
    return user.is_superuser

logger = logging.getLogger(__name__)
def add_user_view(request):
    """
    API pour ajouter un utilisateur (retourne du JSON)
    """
    if request.method == 'POST':
        fullname = request.POST.get('fullname', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', 'user')

        # Comptable
        access_type = request.POST.get('access_type', 'all')
        selected_users = request.POST.getlist('selected_users')

        errors = []

        # 🔎 VALIDATION
        if not fullname:
            errors.append("Le nom complet est requis")
        if not email:
            errors.append("L'email est requis")
        if not password1:
            errors.append("Le mot de passe est requis")
        if password1 != password2:
            errors.append("Les mots de passe ne correspondent pas")
        if len(password1) < 8:
            errors.append("Le mot de passe doit contenir au moins 8 caractères")
        
        # Vérifier si l'utilisateur existe déjà
        if User.objects.filter(email__iexact=email).exists():
            errors.append("Cet email est déjà utilisé")
            
            # Récupérer l'utilisateur existant pour debug
            existing_user = User.objects.get(email__iexact=email)
            logger.info(f"Utilisateur existant: ID={existing_user.id}, email={existing_user.email}")
            
            # Vérifier si un profil existe déjà
            if hasattr(existing_user, 'userprofile'):
                logger.info(f"Profil existe déjà pour l'utilisateur {existing_user.id}")
                errors.append("Un profil existe déjà pour cet utilisateur")

        if errors:
            return JsonResponse({
                'success': False,
                'error': errors[0]
            })

        try:
            with transaction.atomic():
                # 1. Créer l'utilisateur
                username = email
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                    first_name=fullname.split()[0] if fullname else '',
                    last_name=' '.join(fullname.split()[1:]) if len(fullname.split()) > 1 else ''
                )

                # 2. CRÉER LE PROFIL MANUELLEMENT
                # Vérifier si le profil n'existe pas déjà (par sécurité)
                if not hasattr(user, 'userprofile'):
                    profile = UserProfile.objects.create(
                        user=user,
                        fullname=fullname,
                        role=role
                    )
                else:
                    # Si le profil existe déjà (cas rare), on le récupère
                    profile = user.userprofile
                    profile.fullname = fullname
                    profile.role = role

                # 🔐 GESTION DES RÔLES
                if role == 'admin':
                    user.is_superuser = True
                    user.is_staff = True
                    profile.can_view_files = True
                    profile.can_view_all_files = True
                    profile.can_manage_users = True
                    profile.is_valid = True

                elif role == 'comptable':
                    logger.info("Configuration du rôle COMPTABLE")
                    user.is_superuser = False
                    user.is_staff = False
                    user.save()
                    
                    profile.role = 'comptable'
                    profile.can_view_files = True
                    profile.can_manage_users = True
                    profile.is_valid = True
                    
                    # Gestion des accès
                    if access_type == 'all':
                        profile.can_view_all_files = True
                        profile.can_view_users.clear()
                        logger.info("Accès TOTAL configuré")
                        
                    elif access_type == 'selected':
                        profile.can_view_all_files = False
                        profile.can_view_users.clear()
                        
                        # Traitement des IDs
                        selected_ids = []
                        for sid in selected_users:
                            try:
                                selected_ids.append(int(sid))
                            except (ValueError, TypeError):
                                pass
                        
                        # Ajouter les utilisateurs
                        for uid in selected_ids:
                            if uid != user.id:  # Éviter l'auto-sélection
                                profile.can_view_users.add(uid)
                                logger.info(f"Ajout de l'utilisateur {uid}")
                        
                        logger.info(f"Accès LIMITÉ configuré pour {len(selected_ids)} utilisateurs")
                    
                    profile.save()
                    
                    # Forcer le rechargement
                    profile.refresh_from_db()
                    logger.info(f"Profil sauvegardé - can_view_all_files: {profile.can_view_all_files}")
                    
                else:  # user simple
                    profile.can_view_files = False
                    profile.can_view_all_files = False
                    profile.can_manage_users = False
                    profile.is_valid = False

                # 3. Sauvegarder les modifications
                user.save()
                profile.save()

                return JsonResponse({
                    'success': True,
                    'message': f"Utilisateur '{fullname}' créé avec succès"
                })

        except IntegrityError as e:
            error_msg = str(e)
            logger.error(f"Erreur IntegrityError: {error_msg}")
            
            # Vérifier si c'est une erreur de duplication
            if "Duplicate entry" in error_msg or "UNIQUE constraint" in error_msg:
                return JsonResponse({
                    'success': False,
                    'error': "Un profil existe déjà pour cet utilisateur. Veuillez contacter l'administrateur."
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f"Erreur de base de données: {error_msg}"
                })
        except Exception as e:
            logger.exception("Erreur lors de la création de l'utilisateur")
            return JsonResponse({
                'success': False,
                'error': f"Erreur serveur: {str(e)}"
            })

    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée'
    })



def edit_user_view(request, user_id):
    # ========== DÉBOGAGE AU TOUT DÉBUT ==========
    import logging
    logger = logging.getLogger(__name__)
    if request.method == 'POST':
        try:
            # Afficher les données POST (mais NE PAS accéder à request.body)
            print(f"📢 request.POST: {request.POST}")
            print(f"📢 request.FILES: {request.FILES}")
     
            
            first_name = request.POST.get('first_name', '').strip()
            email = request.POST.get('email', '').strip()
            role = request.POST.get('role', 'user')
            password = request.POST.get('password', '')
            # CORRECTION: Utilisez 'edit_access_type' au lieu de 'access_type'
            access_type = request.POST.get('edit_access_type', 'all')
            # CORRECTION: Utilisez 'edit_selected_users' au lieu de 'selected_users'
            selected_users = request.POST.getlist('edit_selected_users')
            
            # ==================== VALIDATION ====================
            if not first_name:
                print("❌ Erreur: Nom requis")
                return JsonResponse({'success': False, 'error': 'Nom requis'})

            if not email:
                print("❌ Erreur: Email requis")
                return JsonResponse({'success': False, 'error': 'Email requis'})

            # ==================== RÉCUPÉRATION USER ====================
            user = get_object_or_404(User, id=user_id)
            print(f"✅ User trouvé: {user.username} (ID: {user.id})")

            # ==================== MISE À JOUR USER ====================
            user.first_name = first_name
            user.email = email

            if password:
                user.set_password(password)
                print("✅ Mot de passe mis à jour")

            user.save()
            print("✅ User sauvegardé")

            # ==================== MISE À JOUR PROFIL ====================
            profile, created = UserProfile.objects.get_or_create(user=user)
            print(f"✅ Profile {'créé' if created else 'récupéré'} (ID: {profile.id})")

            profile.role = role
            profile.fullname = first_name
            profile.save()  # Sauvegarde initiale
            print(f"✅ Profile sauvegardé avec rôle: {profile.role}")

            # Vérification CRITIQUE
            print(f"🔍 Vérification: role='{role}' == 'comptable'? {role == 'comptable'}")
            print(f"🔍 Type de role: {type(role)}")
            
            if role == 'comptable':
                print("🎯🎯🎯 ENTRÉE DANS LE BLOC COMPTABLE 🎯🎯🎯")
                
                if access_type == 'all':
                    print("✅✅✅ hello - setting all access ✅✅✅")
                    profile.can_view_all_files = True
                    profile.can_view_users.clear()
                    print("✅ All access configuré")
                    
                elif access_type == 'selected':
                    print("✅✅✅ hello - setting selected access ✅✅✅")
                    profile.can_view_all_files = False
                    
                    # Conversion des IDs
                    user_ids = []
                    for id_val in selected_users:
                        try:
                            user_ids.append(int(id_val))
                            print(f"   - ID ajouté: {id_val}")
                        except (ValueError, TypeError) as e:
                            print(f"   ⚠️ ID invalide ignoré: {id_val} - Erreur: {e}")
                    
                    if user_ids:
                        profile.can_view_users.set(user_ids)
                        print(f"✅ Selected access configuré avec {len(user_ids)} utilisateurs: {user_ids}")
                    else:
                        profile.can_view_users.clear()
                        print("⚠️ Aucun ID valide, liste vidée")
                else:
                    print(f"⚠️ Access type non reconnu: '{access_type}'")
                    
            else:
                print(f"❌ BLOCK NON EXÉCUTÉ: rôle = '{role}' n'est pas 'comptable'")
                profile.can_view_all_files = False
                profile.can_view_users.clear()
                print("✅ Configuration reset pour non-comptable")

            # Sauvegarde finale
            profile.save()
            print("✅ Profile final sauvegardé")
            
            # Vérification post-sauvegarde
            profile.refresh_from_db()
            print(f"📊 État final dans la DB:")
            print(f"   - can_view_all_files: {profile.can_view_all_files}")
            print(f"   - can_view_users count: {profile.can_view_users.count()}")
            print(f"   - can_view_users IDs: {list(profile.can_view_users.values_list('id', flat=True))}")
            print("=" * 80)

            return JsonResponse({
                'success': True,
                'debug': {
                    'user_id': user.id,
                    'first_name': user.first_name,
                    'email': user.email,
                    'role_received': role,
                    'role_saved': profile.role,
                    'access_type': access_type,
                    'selected_users': selected_users,
                    'can_view_all_files': profile.can_view_all_files,
                    'can_view_users_count': profile.can_view_users.count(),
                    'can_view_users_ids': list(profile.can_view_users.values_list('id', flat=True))
                }
            })

        except Exception as e:
            import traceback
            print("=" * 80)
            print("❌❌❌ EXCEPTION DANS LA VUE ❌❌❌")
            print(f"Erreur: {str(e)}")
            print("Traceback complet:")
            traceback.print_exc()
            print("=" * 80)
            
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    print("❌ Méthode non autorisée")
    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée'
    }, status=405)

def get_user_permissions_view(request, user_id):
    """
    API pour récupérer les permissions d'un utilisateur
    """
    if request.method == 'GET':
        try:
            user = get_object_or_404(User, id=user_id)
            
            if not hasattr(user, 'userprofile'):
                return JsonResponse({
                    'success': False,
                    'error': "Profil utilisateur non trouvé"
                })
            
            profile = user.userprofile
            
            # Récupérer la liste des utilisateurs sélectionnés
            selected_users = list(profile.can_view_users.values_list('id', flat=True))
            
            # Déterminer le type d'accès
            if profile.role == 'comptable':
                if profile.can_view_all_files:
                    access_type = 'all'
                else:
                    access_type = 'selected'
            else:
                access_type = None
            
            # Récupérer les détails des utilisateurs sélectionnés
            selected_users_details = []
            for uid in selected_users:
                try:
                    target_user = User.objects.get(id=uid)
                    selected_users_details.append({
                        'id': target_user.id,
                        'name': target_user.get_full_name() or target_user.first_name or target_user.email,
                        'email': target_user.email
                    })
                except User.DoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'permissions': {
                    'role': profile.role,
                    'access_type': access_type,
                    'selected_users': selected_users,
                    'selected_users_details': selected_users_details,
                    'can_view_files': profile.can_view_files,
                    'can_view_all_files': profile.can_view_all_files,
                    'can_manage_users': profile.can_manage_users,
                    'is_valid': profile.is_valid
                }
            })
            
        except Exception as e:
            logger.exception("Erreur lors de la récupération des permissions")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée'
    }, status=405)

 
def get_users_list(request):
    """
    API pour récupérer la liste des utilisateurs (sauf les comptables et optionnellement l'utilisateur courant)
    """
    if request.method == 'GET':
        try:
            exclude_current = request.GET.get('exclude_current', 'false').lower() == 'true'
      
            users = User.objects.exclude(
                userprofile__role='comptable'  # Exclure tous les comptables
            )
            if exclude_current and request.user.is_authenticated:
                users = users.exclude(id=request.user.id)
            users_list = []
            for user in users:
                # Récupérer le profil pour avoir le rôle
                profile = None
                role = 'user'  # rôle par défaut
                if hasattr(user, 'userprofile') and user.userprofile:
                    profile = user.userprofile
                    role = profile.role if profile.role else 'user'
                
                if role == 'comptable':
                    continue  # Sauter les comptables au cas où
                
                users_list.append({
                    'id': user.id,
                    'name': user.get_full_name() or user.first_name or user.email.split('@')[0],
                    'email': user.email,
                    'role': role,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                })
            
            return JsonResponse({
                'success': True,
                'users': users_list,
                'count': len(users_list)
            })
            
        except Exception as e:
            logger.exception("Erreur lors de la récupération des utilisateurs")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée'
    }, status=405)