import os
import requests
import json
import time

# === CREDENCIAIS DO APP AZURE ===
CLIENT_ID = "ff064952-edbc-4b73-b565-904af73f474c"
CLIENT_SECRET = "Kg98Q~lXfPoFL~KqIrd5ZA0ew_DoKAc.fwBMgatM"
TENANT_ID = "a320b90f-c4a8-491a-a5e1-b8dba71beebb"

# === CONFIGURAÇÃO DO DESTINO ===
SHAREPOINT_SITE_NAME = "FPA-ECOS"
SHAREPOINT_DRIVE_NAME = "Documents"
TARGET_FOLDER_PATH = "ECOS Quickbooks Data"  # Subpasta dentro do drive
LOCAL_FOLDER = "output"

# === Autentica e retorna access_token ===
def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# === Busca o site_id do site SharePoint ===
def get_site_id(access_token):
    hostname = "netorgft5199713.sharepoint.com"
    site_path = "/sites/FPA-ECOS"
    url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["id"]

# === Busca o drive_id da biblioteca "Documentos Compartilhados" ===
def get_drive_id(access_token, site_id):
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    for drive in response.json()["value"]:
        if drive["name"] == SHAREPOINT_DRIVE_NAME or drive["name"] == "Documentos":
            return drive["id"]
    raise Exception("Drive não encontrado.")

# === Faz upload do arquivo para a pasta SharePoint ===
def upload_file(access_token, site_id, drive_id, local_file_path, sharepoint_file_path, retries=3):
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{sharepoint_file_path}:/content"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    for attempt in range(1, retries + 1):
        try:
            with open(local_file_path, "rb") as f:
                response = requests.put(url, headers=headers, data=f)
            if response.status_code in [200, 201]:
                print(f"✅ Upload de {os.path.basename(local_file_path)} concluído.")
                return
            else:
                print(f"❌ Falha ao enviar {local_file_path}: {response.status_code} - {response.text}")
                return
        except requests.exceptions.SSLError as e:
            print(f"⚠️ Tentativa {attempt} falhou com SSLError: {e}")
            if attempt < retries:
                print("🔁 Aguardando 5 segundos para nova tentativa...")
                time.sleep(5)
            else:
                print(f"❌ Todas as tentativas de upload falharam para {local_file_path}")

# === MAIN ===
def main():
    print("🔐 Autenticando com Microsoft Graph...")
    token = get_access_token()

    print("🔎 Buscando site_id e drive_id...")
    site_id = get_site_id(token)
    drive_id = get_drive_id(token, site_id)

    print(f"📤 Iniciando upload de arquivos da pasta '{LOCAL_FOLDER}' para o SharePoint...")

    files = [f for f in os.listdir(LOCAL_FOLDER) if f.endswith(".json") or f.endswith(".csv")]
    if not files:
        print("⚠️ Nenhum arquivo '.json' ou '.csv' encontrado na pasta 'output/'. Nada para enviar.")
        return

    for filename in files:
        local_path = os.path.join(LOCAL_FOLDER, filename)
        sharepoint_path = f"{TARGET_FOLDER_PATH}/{filename}"
        upload_file(token, site_id, drive_id, local_path, sharepoint_path)


    print("🏁 Upload finalizado.")

if __name__ == "__main__":
    main()
