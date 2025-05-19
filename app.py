from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def oauth_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if code:
        return f"Received code: {code}"
    return "No code found"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
