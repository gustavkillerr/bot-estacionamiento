from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():  # 👈 CORREGIDO: ahora tiene los dos puntos
    return "Bot activo", 200

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
