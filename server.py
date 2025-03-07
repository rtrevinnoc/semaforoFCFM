from flask import Flask, render_template, jsonify, request, redirect, url_for
from pymongo import MongoClient
import jwt
import datetime
from functools import wraps
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a strong secret key

# Conexión a MongoDB
CONNECTION_STRING = 'mongodb+srv://clientapp:LLjALBUEvLGjGgph@cluster0.x5fa5jl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(CONNECTION_STRING)
db = client['semaforo']
collection = db['trafico']

# Decorador para proteger rutas con JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'status': 'error', 'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token.split(" ")[-1], app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user = data['email']
        except:
            return jsonify({'status': 'error', 'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/mapa')
@token_required
def mapa():
    return render_template('index.html')

@app.route('/map_data')
@token_required
def map_data():
    semaphores = list(collection.find({}, {"_id": 0, "serial": 1, "state": 1, "location": 1, "mode": 1}))
    return jsonify(semaphores)

@app.route('/login', methods=['POST'])
def login():
    users_collection = db['usuarios']
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = users_collection.find_one({'correo': email})
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        token = jwt.encode({
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({'status': 'success', 'token': token}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Usuario no encontrado'}), 404

@app.route('/logout', methods=['POST'])
def logout():
    return jsonify({'status': 'success', 'message': 'Logged out successfully'}), 200

@app.route('/change_color/<serial>/<color>', methods=['POST'])
@token_required
def change_color(serial, color):
    if color not in ['0', '1']:
        return jsonify({'status': 'error', 'message': 'Color inválido'}), 400
    
    collection.update_one(
        {"serial": serial},
        {"$set": {"state": int(color), "change_flag": 1}}
    )
    
    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(debug=True)
