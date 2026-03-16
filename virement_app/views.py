# views.py
import os
import json
from datetime import datetime
import pandas as pd

from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.http import require_http_methods
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

# -------------------------
# CONFIGURATION
# -------------------------

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

# -------------------------
# FONCTIONS UTILES
# -------------------------

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


# -------------------------
# GESTION DU COMPTEUR
# -------------------------

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


# -------------------------
# VUES PRINCIPALES
# -------------------------

def home(request):
    """Page d'accueil - redirige vers login ou index."""
    if request.user.is_authenticated:
        return redirect("login")
    return redirect("login")


def login_view(request):
    """Vue de connexion."""
    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            messages.success(request, "Connexion réussie !")
            return redirect("index")
        
        messages.error(request, "Email ou mot de passe incorrect")
    
    return render(request, "login.html")


def register(request):
    """Vue d'inscription."""
    if request.method == "POST":
        name = request.POST.get("first_name")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        
        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas")
            return redirect("register")
        
        if User.objects.filter(username=email).exists():
            messages.error(request, "Cet email existe déjà")
            return redirect("register")
        
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password1,
            first_name=name
        )
        
        messages.success(request, "Compte créé avec succès")
        return redirect("login")
    
    return render(request, "register.html")


@login_required
def logout_view(request):
    """Vue de déconnexion."""
    logout(request)
    messages.success(request, "Déconnexion réussie")
    return redirect("login")


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


def generate_xml(request, apply_corrections=False):
    """Génère le fichier XML."""
    filename = request.session.get("filename")
    purpose_code = request.session.get("purpose_code")
    
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
    
    # Génération du XML
    df["Montant_num"] = df["Montant"].apply(to_number)
    debtor_account = str(df.iloc[0]["RIB_tirer"]).strip()
    debtor_name = str(df.iloc[0]["Nom_tirer"]).strip()
    total_amount = df["Montant_num"].sum()
    settlement_system = "ACH" if total_amount < 3000000 else "RTGS"
    
    now = datetime.utcnow()
    creation_dt = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    intrbk_date = now.strftime("%Y-%m-%d")
    nb_of_txs = len(df)
    
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
        if is_ccp:
            SubElement(cdtr, "Nm").text = "CCP"
        else:
            SubElement(cdtr, "Nm").text = str(row["Nom_Prenom_Beneficaire"]).strip()
        
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
    
    # Générer le XML
    xml_str = parseString(tostring(root)).toprettyxml(indent="  ")
    
    # Sauvegarder le fichier
    out_filename = f"{os.path.splitext(filename)[0]}_{now.strftime('%Y%m%d%H%M%S')}.xml"
    out_path = os.path.join(settings.MEDIA_ROOT, "outputs", out_filename)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml_str)
    
    save_last_id(last_id)
    
    # Nettoyer la session
    request.session.pop("rib_corrections", None)
    request.session.pop("filename", None)
    request.session.pop("purpose_code", None)
    
    # Messages de confirmation
    correction_msg = ""
    if apply_corrections:
        correction_msg = "<br>✅ Les RIBs ont été corrigés automatiquement.<br>"
    
    ccp_msg = ""
    if is_ccp:
        ccp_msg = f"<br>ℹ️ Type CCP: Tous les virements utilisent le compte {CCP_ACCOUNT}.<br>"
    
    messages.success(
        request,
        f"✅ Conversion réussie : {nb_of_txs} transactions.<br>"
        f"{correction_msg}"
        f"{ccp_msg}"
        f"📂 Fichier généré : {out_filename}<br><br>"
        f"⚠️ <strong>IMPORTANT :</strong> Ce fichier doit être envoyé à la BCM via ATS <u>avant la fin de la journée</u>. "
        f"Tout envoi ultérieur sera rejeté."
    )
    
    request.session["last_generated_file"] = out_filename
    return redirect("download_file", filename=out_filename)


@login_required
def download_file(request, filename):
    """Télécharge un fichier généré."""
    file_path = os.path.join(settings.MEDIA_ROOT, "outputs", filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), as_attachment=True)
    else:
        messages.error(request, "Fichier non trouvé")
        return redirect("index")


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