from flask import Flask, request, jsonify
from flask_cors import CORS
from insert_user import insert_user
from check_user import check_user
from reset_password import send_reset_email

app = Flask(__name__)
CORS(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    if insert_user(email, password):
        return jsonify({'status': 'success', 'message': 'User registered successfully'})
    return jsonify({'status': 'error', 'message': 'Registration failed. Email might already be in use.'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    if check_user(email, password):
        return jsonify({'status': 'success', 'message': 'Login successful'})
    return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')

    try:
        if send_reset_email(email):
            return jsonify({'status': 'success', 'message': 'Password reset email sent'})
        else:
            return jsonify({'status': 'error', 'message': 'Email not found'}), 404
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Failed to send reset email'}), 500

if __name__ == '__main__':
    app.run(debug=True)
