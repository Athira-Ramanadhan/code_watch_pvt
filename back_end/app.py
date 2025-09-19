from flask import Flask, request, jsonify
from flask_cors import CORS
from database import init_db, insert_user, check_user, update_password
from reset_password import create_reset_token, validate_reset_token, clear_reset_token
import subprocess, tempfile, os

# Import Blueprints
from faculty_routes import faculty_bp
from admin_routes import admin_bp
from student_routes import student_bp

app = Flask(__name__)
CORS(app)

# ✅ Initialize DB
init_db()
# ==========================
# Root Route (Welcome Page)
# ==========================
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "success", "message": "CodeWatch Backend is running"})
# ==========================
# User Authentication
# ==========================
@app.route("/api/register", methods=["POST"])
def register():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    role = data.get("role", "student")
    name = data.get("name", "Student")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password required"}), 400

    if insert_user(email, password, role, name):
        return jsonify({"status": "success", "message": "User created"})
    return jsonify({"status": "error", "message": "Email already exists"}), 409


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    user = check_user(email, password)
    if user:
        return jsonify({"status": "success", "user": user})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401
# ==========================
# Password Reset
# ==========================
@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"status": "error", "message": "Email required"}), 400

    token = create_reset_token(email)
    if token:
        return jsonify({"status": "success", "message": "Reset link sent"})
    return jsonify({"status": "error", "message": "Email not found"}), 404


@app.route("/api/verify-reset-token", methods=["POST"])
def verify_reset_token_route():
    token = (request.json or {}).get("token", "").strip()
    email = validate_reset_token(token)
    if email:
        return jsonify({"valid": True})
    clear_reset_token(token)
    return jsonify({"valid": False})
@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    data = request.json or {}
    token = data.get("token", "").strip()
    new_password = data.get("new_password", "").strip()

    if not token or not new_password:
        return jsonify({"status": "error", "message": "Token and new password required"}), 400
    if len(new_password) < 6:
        return jsonify({"status": "error", "message": "Password too short"}), 400

    email = validate_reset_token(token)
    if not email:
        return jsonify({"status": "error", "message": "Invalid or expired token"}), 400

    update_password(email, new_password)
    clear_reset_token(email)
    return jsonify({"status": "success", "message": "Password updated"})
# ==========================
# Code Execution
# ==========================
@app.route("/api/run", methods=["POST"])
def run_code():
    data = request.json or {}
    code = data.get("code", "")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as tmp:
            tmp.write(code)
            tmp_filename = tmp.name

        result = subprocess.run(
            ["python", tmp_filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            text=True
        )
        output = result.stdout if result.stdout else result.stderr

    except subprocess.TimeoutExpired:
        output = "❌ Code execution timed out."
    except Exception as e:
        output = f"❌ Error: {str(e)}"
    finally:
        if "tmp_filename" in locals() and os.path.exists(tmp_filename):
            os.remove(tmp_filename)

    return jsonify({"status": "success", "output": output})
# ==========================
# Register Blueprints
# ==========================
app.register_blueprint(faculty_bp, url_prefix="/api/faculty")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(student_bp, url_prefix="/api/student")
# ==========================
# Run Server
# ==========================
if __name__ == "__main__":
    print("✅ Flask server running on http://127.0.0.1:5000")
    app.run(debug=True, threaded=False)
