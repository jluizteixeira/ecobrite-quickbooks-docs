import json
import base64
import requests
import time

client_id = 'ABlSXnqv7AK1tQPjd2L33D7n82tKyFH2n3w7NrSwWliXR66kmZ'
client_secret = 'EMb3dflsjKQQfSPJMOC5C2dz2xxP3MbKPZzdWqH8'
token_url = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'

def load_tokens():
    with open('tokens.json', 'r') as f:
        return json.load(f)

def save_tokens(tokens):
    with open('tokens.json', 'w') as f:
        json.dump(tokens, f, indent=4)

def exchange_code_for_tokens(code):
    credentials = f"{client_id}:{client_secret}"
    basic_auth = base64.b64encode(credentials.encode()).decode()

    headers = {
        'Authorization': f'Basic {basic_auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'authorization_code',
        'code': 'XAB11747679822fMJBwOT80qqOJKYYCMQSxPX9Yke3N9BgWwpn',
        'redirect_uri': 'https://ecobrite-oauth-callback.onrender.com/callback'  # sua redirect URI exata
    }

    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code == 200:
        tokens = response.json()
        save_tokens(tokens)
        print('✅ Tokens recebidos e salvos.')
        return tokens
    else:
        print('❌ Erro na troca do código pelo token:', response.text)
        return None

def get_valid_access_token():
    tokens = load_tokens()
    
    # Se não houver 'expires_at', assume que precisa renovar agora
    expires_at = tokens.get('expires_at', 0)
    now = int(time.time())
    
    # Se o token expirou ou não tem expires_at, renova
    if now >= expires_at:
        print("🔁 Access token expirado ou ausente. Renovando...")
        new_access_token = refresh_access_token()
        
        # Após renovar, recalcula 'expires_at'
        if new_access_token:
            updated_tokens = load_tokens()
            updated_tokens['expires_at'] = int(time.time()) + updated_tokens.get('expires_in', 3600)
            save_tokens(updated_tokens)
            return updated_tokens['access_token']
        else:
            raise Exception("❌ Falha ao renovar o token de acesso.")
    
    return tokens['access_token']

def refresh_access_token():
    tokens = load_tokens()
    refresh_token = tokens['refresh_token']

    credentials = f"{client_id}:{client_secret}"
    basic_auth = base64.b64encode(credentials.encode()).decode()

    headers = {
        'Authorization': f'Basic {basic_auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code == 200:
        new_tokens = response.json()
        new_tokens['expires_at'] = int(time.time()) + new_tokens.get('expires_in', 3600)
        save_tokens(new_tokens)
        print('✅ Access token atualizado.')
        return new_tokens['access_token']
    else:
        print('❌ Erro ao renovar token:', response.text)
        return None

# Para testar a troca do código, você pode chamar a função assim:
if __name__ == '__main__':
    code = input("Cole aqui o código que você recebeu na URL: ")
    exchange_code_for_tokens(code)