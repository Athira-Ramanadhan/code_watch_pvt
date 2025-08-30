from flask import Flask, request, jsonify
from flask_cors import CORS
from database import init_db, insert_user, check_user, update_password
from reset_password import create_reset_token, validate_reset_token, clear_reset_token

app = Flask(__name__)
CORS(app)

# Initialize DB at startup
init_db()

# ----------------- Register -----------------
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password required'}), 400

    if insert_user(email, password):
        return jsonify({'status': 'success', 'message': 'User created'})
    else:
        return jsonify({'status': 'error', 'message': 'Email already exists'}), 409

# ----------------- Login -----------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if check_user(email, password):
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'})

# ----------------- Forgot Password -----------------
@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json or {}
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'status': 'error', 'message': 'Email required'}), 400

    token = create_reset_token(email)
    if token:
        return jsonify({'status': 'success', 'message': 'Reset email sent!'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send reset email. Check email address.'})

# ----------------- Verify Reset Token -----------------
@app.route('/verify-reset-token', methods=['POST'])
def verify_reset_token():
    data = request.json or {}
    token = data.get('token', '').strip()
    return jsonify({'valid': bool(validate_reset_token(token))})

# ----------------- Reset Password -----------------
@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json or {}
    token = data.get('token', '').strip()
    new_password = data.get('new_password', '').strip()

    if not token or not new_password:
        return jsonify({'status': 'error', 'message': 'Token and new password required'}), 400
    if len(new_password) < 8:
        return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters'}), 400

    email = validate_reset_token(token)
    if not email:
        return jsonify({'status': 'error', 'message': 'Invalid or expired token'})

    # Use update_password helper (safe context manager)
    update_password(email, new_password)
    clear_reset_token(email)

    return jsonify({'status': 'success', 'message': 'Password updated successfully'})

# ----------------- Run server -----------------
if __name__ == '__main__':
    print("✅ Flask server running on http://127.0.0.1:5000")
    app.run(debug=True)
