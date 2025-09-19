from flask import Blueprint, jsonify, request
from database import safe_execute, update_password

admin_bp = Blueprint("admin", __name__)

# ----------------- Users -----------------
@admin_bp.route("/users", methods=["GET"])
def list_users():
    try:
        cur = safe_execute("SELECT id, name, email, role FROM users ORDER BY id ASC", commit=False)
        return jsonify([dict(row) for row in cur.fetchall()])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/delete-user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        cur = safe_execute("SELECT role FROM users WHERE id=?", (user_id,), commit=False)
        row = cur.fetchone()
        if not row:
            return jsonify({"status": "error", "message": "User not found"}), 404
        if row["role"] == "admin":
            return jsonify({"status": "error", "message": "Cannot delete an admin account"}), 403

        safe_execute("DELETE FROM submissions WHERE student_id=?", (user_id,))
        safe_execute("DELETE FROM event_logs WHERE student_id=?", (user_id,))
        safe_execute("DELETE FROM users WHERE id=?", (user_id,))

        return jsonify({"status": "success", "message": f"User {user_id} deleted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/reset-password", methods=["POST"])
def reset_password_admin():
    try:
        data = request.json or {}
        email = data.get("email", "").lower()
        new_password = data.get("new_password", "")
        if not email or not new_password:
            return jsonify({"status": "error", "message": "Email and password required"}), 400
        update_password(email, new_password)
        return jsonify({"status": "success", "message": f"Password reset for {email}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ----------------- Submissions -----------------
@admin_bp.route("/submissions", methods=["GET"])
def all_submissions():
    try:
        cur = safe_execute("SELECT * FROM submissions ORDER BY timestamp DESC", commit=False)
        return jsonify([dict(row) for row in cur.fetchall()])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ----------------- Event Logs -----------------
@admin_bp.route("/events", methods=["GET"])
def all_events():
    try:
        cur = safe_execute("SELECT * FROM event_logs ORDER BY timestamp DESC", commit=False)
        return jsonify([dict(row) for row in cur.fetchall()])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
