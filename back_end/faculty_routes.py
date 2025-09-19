from flask import Blueprint, request, jsonify
from datetime import datetime
from database import (
    insert_exam, delete_exam, safe_execute,
    insert_question, get_questions, delete_question,
    link_exam_questions, get_exam_questions,
    grade_submission
)

faculty_bp = Blueprint("faculty", __name__)

# ----------------- Helper -----------------
def compute_status(exam_date_str):
    """Return exam status: upcoming, ongoing, completed"""
    try:
        today = datetime.now().date()
        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        if exam_date == today:
            return "ongoing"
        elif exam_date > today:
            return "upcoming"
        else:
            return "completed"
    except Exception:
        return "unknown"


# ----------------- Exams -----------------
@faculty_bp.route("/exams", methods=["POST"])
def create_exam():
    """Faculty creates an exam + links questions"""
    try:
        data = request.json or {}
        title = data.get("title")
        description = data.get("description", "")
        faculty_id = data.get("faculty_id")
        date = data.get("date")  # expect YYYY-MM-DD
        questions = data.get("questions", [])

        if not title or not faculty_id or not date:
            return jsonify({"status": "error", "message": "Title, date, and faculty_id required"}), 400

        # ✅ insert_exam now returns exam_id directly
        exam_id = insert_exam(title, description, faculty_id, date)

        if questions:
            link_exam_questions(exam_id, questions)

        return jsonify({"status": "success", "message": "Exam created", "exam_id": exam_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@faculty_bp.route("/exams", methods=["GET"])
def list_all_exams():
    """Return all exams with linked questions + status"""
    try:
        cur = safe_execute("SELECT * FROM exams ORDER BY date ASC", commit=False)
        exams = [dict(row) for row in cur.fetchall()]

        for exam in exams:
            exam["questions"] = get_exam_questions(exam["id"])
            exam["status"] = compute_status(exam["date"])

        return jsonify(exams)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@faculty_bp.route("/exams/<int:faculty_id>", methods=["GET"])
def list_exams(faculty_id):
    """Return exams created by a specific faculty"""
    try:
        cur = safe_execute("SELECT * FROM exams WHERE faculty_id=? ORDER BY date ASC", (faculty_id,), commit=False)
        exams = [dict(row) for row in cur.fetchall()]

        for exam in exams:
            exam["questions"] = get_exam_questions(exam["id"])
            exam["status"] = compute_status(exam["date"])

        return jsonify(exams)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@faculty_bp.route("/exams/<int:exam_id>", methods=["DELETE"])
def remove_exam(exam_id):
    """Delete an exam + cleanup linked questions"""
    try:
        safe_execute("DELETE FROM exam_questions WHERE exam_id=?", (exam_id,))
        delete_exam(exam_id)
        return jsonify({"status": "success", "message": f"Exam {exam_id} deleted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ✅ Get questions of a specific exam
@faculty_bp.route("/exam_questions/<int:exam_id>", methods=["GET"])
def exam_questions(exam_id):
    try:
        return jsonify(get_exam_questions(exam_id))
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ----------------- Questions -----------------
@faculty_bp.route("/questions/<int:faculty_id>", methods=["GET"])
def list_questions(faculty_id):
    try:
        return jsonify(get_questions(faculty_id))
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@faculty_bp.route("/questions", methods=["POST"])
def create_question():
    try:
        data = request.json or {}
        insert_question(
            data.get("title"),
            data.get("statement"),
            data.get("input_format"),
            data.get("output_format"),
            data.get("sample_tests"),
            data.get("hidden_tests"),
            data.get("faculty_id"),
            data.get("language", "python")  # ✅ default to python if not provided
        )
        return jsonify({"status": "success", "message": "Question added"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@faculty_bp.route("/questions/<int:question_id>", methods=["DELETE"])
def remove_question(question_id):
    try:
        delete_question(question_id)
        return jsonify({"status": "success", "message": f"Question {question_id} deleted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ----------------- Submissions & Results -----------------
@faculty_bp.route("/submissions/<int:exam_id>", methods=["GET"])
def exam_submissions(exam_id):
    """Get all submissions for an exam (with student & exam info)"""
    try:
        cur = safe_execute("""
            SELECT s.*, u.name AS student_name, e.title AS exam_title
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            JOIN exams e ON s.exam_id = e.id
            WHERE s.exam_id=?
            ORDER BY s.timestamp DESC
        """, (exam_id,), commit=False)
        return jsonify([dict(row) for row in cur.fetchall()])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@faculty_bp.route("/results", methods=["GET"])
def all_results():
    """Return all graded submissions for reporting"""
    try:
        cur = safe_execute("""
            SELECT s.*, u.name AS student_name, e.title AS exam_title, q.title AS question_title
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            JOIN exams e ON s.exam_id = e.id
            JOIN questions q ON s.question_id = q.id
            WHERE s.status='graded'
            ORDER BY s.timestamp DESC
        """, commit=False)
        return jsonify([dict(row) for row in cur.fetchall()])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@faculty_bp.route("/grade/<int:submission_id>", methods=["POST"])
def grade(submission_id):
    try:
        data = request.json or {}
        score = data.get("score", 0)
        feedback = data.get("feedback", "")
        grade_submission(submission_id, score, feedback)
        return jsonify({"status": "success", "message": f"Submission {submission_id} graded"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
