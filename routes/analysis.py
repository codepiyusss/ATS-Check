import os

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, current_app, flash,
)
from werkzeug.utils import secure_filename

from utils.pdf_parser import extract_text_from_pdf, PDFParsingError
from utils.ai_analysis import analyze_resume
from services.career_fields import is_valid_field, field_label
from utils.helpers import generate_temp_filename, sanitize_text
from utils.security import RateLimiter
from utils.validators import allowed_file

analysis_bp = Blueprint("analysis", __name__)

MAX_JD_CHARS = 8000

# Created once; limits come from config the first time a request needs them.
_limiter = None


def get_limiter():
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter(
            window_seconds=current_app.config["RATE_LIMIT_WINDOW"],
            max_requests=current_app.config["RATE_LIMIT_MAX_REQUESTS"],
        )
    return _limiter


def reset_limiter():
    """Forget all rate-limit state (used by tests)."""
    global _limiter
    _limiter = None


@analysis_bp.route("/analyze", methods=["POST"])
def analyze():
    ip_address = request.remote_addr or "unknown"
    if get_limiter().is_limited(ip_address):
        flash("You're sending requests too quickly. Please wait a minute and try again.", "error")
        return redirect(url_for("main.analyzer"))

    career_field = request.form.get("career_field", "general")
    if not is_valid_field(career_field):
        flash("Please choose a career field from the list.", "error")
        return redirect(url_for("main.analyzer"))
    job_description = sanitize_text(request.form.get("job_description", ""), max_length=MAX_JD_CHARS)

    resume_text = ""
    uploaded_file = request.files.get("resume_file")
    pasted_text = request.form.get("resume_text", "")

    temp_path = None

    try:
        if uploaded_file and uploaded_file.filename:
            filename = secure_filename(uploaded_file.filename)

            if not allowed_file(filename, current_app.config["ALLOWED_EXTENSIONS"]):
                flash("Only PDF files are supported.", "error")
                return redirect(url_for("main.analyzer"))

            temp_filename = generate_temp_filename(filename)
            temp_path = os.path.join(current_app.config["UPLOAD_FOLDER"], temp_filename)
            uploaded_file.save(temp_path)

            try:
                resume_text = extract_text_from_pdf(temp_path)
            except PDFParsingError as exc:
                flash(str(exc), "error")
                return redirect(url_for("main.analyzer"))
        elif pasted_text.strip():
            resume_text = pasted_text
        else:
            flash("Please upload a PDF or paste your resume text.", "error")
            return redirect(url_for("main.analyzer"))

        resume_text = sanitize_text(resume_text)

        if len(resume_text.split()) < 20:
            flash("That doesn't look like enough resume content to analyze.", "error")
            return redirect(url_for("main.analyzer"))

        result = analyze_resume(resume_text, api_key=current_app.config.get("GEMINI_API_KEY"))
        # Only small metadata goes in the cookie, never the resume or JD text.
        result["career_field_label"] = field_label(career_field)
        result["jd_words"] = len(job_description.split())
        session["analysis_result"] = result
        return redirect(url_for("analysis.result"))

    except Exception:
        # Never log resume text: log the traceback only.
        current_app.logger.exception("Unexpected error during resume analysis")
        flash("Something went wrong while analyzing your resume. Please try again.", "error")
        return redirect(url_for("main.analyzer"))

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@analysis_bp.route("/result")
def result():
    data = session.get("analysis_result")
    if not data:
        flash("No analysis found. Please upload or paste a resume first.", "error")
        return redirect(url_for("main.analyzer"))

    return render_template("result.html", data=data)
