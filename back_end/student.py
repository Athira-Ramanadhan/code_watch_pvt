# student.py
from flask import Blueprint, jsonify
from database import safe_execute, get_exam_questions

student_bp = Blueprint("student", __name__)

# ==========================
# Get exam questions for a student
# ==========================
@student_bp.route("/exam/<int:exam_id>/questions", methods=["GET"])
def get_exam_questions_route(exam_id):
    try:
        # Get exam info
        cur = safe_execute("SELECT * FROM exams WHERE id=?", (exam_id,), commit=False)
        exam = cur.fetchone()
        if not exam:
            return jsonify({"status": "error", "message": "Exam not found"}), 404

        # Get linked questions
        questions = get_exam_questions(exam_id)

        return jsonify({
            "exam_id": exam["id"],
            "title": exam["title"],
            "description": exam["description"],
            "date": exam["date"],
            "duration": 60,  # optional, can be added in DB
            "questions": questions
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
