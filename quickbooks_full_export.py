import requests
import json
import os
import time
import csv
from datetime import datetime
from token_manager import get_valid_access_token
from tqdm import tqdm

# --- CONFIGURAÇÕES ---
COMPANY_ID = '9130357580307926'
OUTPUT_FOLDER = 'output'
MINOR_VERSION = '65'
LAST_RUN_FILE = os.path.join(OUTPUT_FOLDER, 'last_run.txt')

# --- ENTIDADES ESSENCIAIS ---
cdc_supported_entities = {
    "Account", "Customer", "Invoice", "Payment",
    "Bill", "BillPayment", "Vendor", "Deposit", "Transfer",
    "Purchase", "JournalEntry", "Item"
}

all_entities = [
    "Account", "Customer", "Invoice", "Payment",
    "Bill", "BillPayment", "Vendor", "Deposit", "Transfer",
    "Purchase", "JournalEntry", "Item", "Class"
]

# --- Função para obter data da última execução ---
def get_last_run():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            return f.read().strip()
    return None

# --- Atualiza timestamp da última execução ---
def update_last_run():
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(datetime.utcnow().isoformat() + 'Z')

# --- Executa query com paginação ---
def run_paginated_query(entity_name, access_token, changed_since=None):
    url = f'https://quickbooks.api.intuit.com/v3/company/{COMPANY_ID}/query'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/text'
    }

    all_data = []
    start_position = 1
    page_size = 1000

    while True:
        # Monta query com ou sem filtro de data
        query = f"SELECT * FROM {entity_name}"
        if changed_since and entity_name in cdc_supported_entities:
            query += f" WHERE MetaData.LastUpdatedTime >= '{changed_since}'"
        query += f" STARTPOSITION {start_position} MAXRESULTS {page_size}"

        params = {
            'query': query,
            'minorversion': MINOR_VERSION
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            items = data.get('QueryResponse', {}).get(entity_name, [])
            if not items:
                return 'vazio'
            all_data.extend(items)

            if len(items) < page_size:
                break
            start_position += page_size
        else:
            log_error(entity_name, response.status_code, response.text)
            return 'erro'

    return {entity_name: all_data}

# --- Salva os dados JSON e CSV ---
def save_output(entity_name, data):
    json_path = os.path.join(OUTPUT_FOLDER, f"{entity_name.lower()}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    records = data.get(entity_name, [])
    if records:
        csv_path = os.path.join(OUTPUT_FOLDER, f"{entity_name.lower()}.csv")
        keys = set().union(*(r.keys() for r in records))
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted(keys))
            writer.writeheader()
            writer.writerows(records)
    else:
        os.remove(json_path)

# --- Registra erro no log ---
def log_error(entity_name, status_code, response_text):
    with open(os.path.join(OUTPUT_FOLDER, 'erros.txt'), 'a', encoding='utf-8') as f:
        f.write(f"{entity_name}: {status_code}\n{response_text}\n\n")

# --- FUNÇÃO PRINCIPAL ---
def main():
    start_time = time.time()
    access_token = get_valid_access_token()
    changed_since = get_last_run()

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    success_count = 0
    fail_count = 0

    print(f"\n🚀 Iniciando exportação incremental de {len(all_entities)} entidades do QuickBooks...\n")

    for entity in tqdm(all_entities, desc="📦 Exportando entidades"):
        resultado = run_paginated_query(entity, access_token, changed_since)

        if resultado == 'vazio':
            fail_count += 1
            print(f"⚠️ Nenhum dado alterado para {entity}\n")
        elif resultado == 'erro':
            fail_count += 1
            print(f"❌ Erro ao exportar {entity}\n")
        else:
            save_output(entity, resultado)
            success_count += 1
            print(f"✅ {entity} exportado com sucesso\n")

    update_last_run()

    end_time = time.time()
    minutes, seconds = divmod(int(end_time - start_time), 60)

    print("🎯 Exportação finalizada.")
    print(f"✔️ {success_count} sucesso(s), ❌ {fail_count} falha(s).")
    if fail_count > 0:
        print("📄 Verifique o arquivo 'output/erros.txt' para detalhes.")
    print(f"⏱️ Tempo total de execução: {minutes}m {seconds}s\n")

if __name__ == "__main__":
    main()

    import sharepoint_upload
    sharepoint_upload.main()