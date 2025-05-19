from flask import Flask, request

app = Flask(__name__)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    realm_id = request.args.get('realmId')
    state = request.args.get('state')
    
    # Simplesmente para debug agora — depois você faz o token exchange
    return f"Code: {code}<br>Realm ID: {realm_id}<br>State: {state}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
