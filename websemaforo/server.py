from flask import Flask, render_template, jsonify, request, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

# Conexión a MongoDB
CONNECTION_STRING = 'mongodb+srv://clientapp:LLjALBUEvLGjGgph@cluster0.x5fa5jl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(CONNECTION_STRING)
db = client['semaforo']
collection = db['trafico']

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/mapa')
def mapa():
    return render_template('index.html')

@app.route('/map_data')
def map_data():
    # Obtén todos los semáforos
    semaphores = list(collection.find({}, {"_id": 0, "serial": 1, "state": 1, "location": 1, "mode": 1}))
    return jsonify(semaphores)

@app.route('/login', methods=['POST'])
def login():
    collection = db['usuarios']
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Buscar el usuario en la base de datos
    user = collection.find_one({'correo': email, 'password': password})
    
    if user:
        # En lugar de redirect, retornamos un JSON con la URL a redirigir
        return jsonify({'status': 'success', 'redirect': url_for('mapa')}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Usuario no encontrado'}), 404

@app.route('/logout')
def logout():
    return redirect(url_for('login_page'))

@app.route('/change_color/<serial>/<color>', methods=['POST'])
def change_color(serial, color):
    # Verificar que el color es válido (0: rojo, 1: verde)
    if color not in ['0', '1']:
        return jsonify({'status': 'error', 'message': 'Color inválido'}), 400

    # Actualizar el estado del semáforo
    collection.update_one(
        {"serial": serial},
        {"$set": {"state": int(color), "change_flag": 1}}
    )
    
    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(debug=True)