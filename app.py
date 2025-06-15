from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# Simple user database (in a real app, you'd use a proper database)
USERS_DB = {
    "admin": generate_password_hash("admin123")  # Default user
}

@app.route('/')
def index():
    return send_from_directory('.', 'login.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    if username in USERS_DB and check_password_hash(USERS_DB[username], password):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    if username in USERS_DB:
        return jsonify({'error': 'Username already exists'}), 400

    USERS_DB[username] = generate_password_hash(password)
    return jsonify({'message': 'Registration successful'}), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)
