from flask import Blueprint, request, jsonify
from datetime import datetime
from database import (
    insert_submission, insert_event_log, get_results,
    get_exams, get_exam_questions, safe_execute
)

student_bp = Blueprint("student", __name__)

# ----------------- Submissions -----------------
@student_bp.route("/submit", methods=["POST"])
def submit_code():
    try:
        data = request.json
        insert_submission(
            data.get("exam_id"),
            data.get("student_id"),
            data.get("question_id"),
            data.get("code", ""),
            data.get("language", "python"),
            data.get("hash"),
            data.get("timestamp")
        )
        return jsonify({"status": "success", "message": "Code submitted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ----------------- Event Logging -----------------
@student_bp.route("/events", methods=["POST"])
def log_events():
    try:
        data = request.json
        student_id = data.get("student_id")
        exam_id = data.get("exam_id", None)

        logs = data.get("logs", [])
        if logs:
            for log in logs:
                insert_event_log(
                    student_id,
                    log.get("exam_id", exam_id),
                    log.get("event_type"),
                    log.get("timestamp"),
                    log.get("content_length"),
                )
        else:
            insert_event_log(
                student_id,
                exam_id,
                data.get("event_type"),
                data.get("timestamp"),
                data.get("content_length"),
            )

        return jsonify({"status": "success", "message": "Events logged"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ----------------- Results -----------------
@student_bp.route("/results/<int:student_id>", methods=["GET"])
def get_results_route(student_id):
    try:
        results = get_results(student_id)
        return jsonify(results)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ----------------- Exams -----------------
@student_bp.route("/exams/<int:student_id>", methods=["GET"])
def list_exams(student_id):
    """Get all exams with status for a student (upcoming / ongoing / completed)."""
    try:
        exams = get_exams()  # returns all exams
        today = datetime.now().date()

        for exam in exams:
            exam_date = datetime.strptime(exam["date"], "%Y-%m-%d").date()

            if exam_date > today:
                exam["status"] = "upcoming"
            elif exam_date < today:
                exam["status"] = "completed"
            else:
                # exam is today → check if student already submitted
                cur = safe_execute(
                    "SELECT 1 FROM submissions WHERE exam_id=? AND student_id=? LIMIT 1",
                    (exam["id"], student_id),
                    commit=False
                )
                exam["status"] = "completed" if cur.fetchone() else "ongoing"

            # Optional: include linked questions
            exam["questions"] = get_exam_questions(exam["id"])

        return jsonify(exams)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@student_bp.route("/exams/<int:exam_id>/questions", methods=["GET"])
def exam_questions(exam_id):
    """Get all questions linked to an exam."""
    try:
        questions = get_exam_questions(exam_id)
        return jsonify(questions)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
