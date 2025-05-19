from flask import Flask, request

app = Flask(__name__)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if code:
        return f"OAuth callback recebido com sucesso! Código: {code}"
    else:
        return "Nenhum código OAuth encontrado no callback.", 400

if __name__ == '__main__':
    app.run()
