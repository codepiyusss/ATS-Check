import os
import time
from collections import defaultdict

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, current_app, flash
)
from werkzeug.utils import secure_filename

from utils.pdf_parser import extract_text_from_pdf, PDFParsingError
from utils.ai_analysis import analyze_resume
from utils.helpers import allowed_file, generate_temp_filename, sanitize_text, sanitize_form_field

main_bp = Blueprint("main", __name__)

# --- very basic in-memory rate limiter ---
# Not meant for production (won't work across multiple server workers),
# but stops a single user from spamming the /analyze route.
_request_log = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 5


def _is_rate_limited(ip_address):
    now = time.time()
    recent = [t for t in _request_log[ip_address] if now - t < RATE_LIMIT_WINDOW]
    _request_log[ip_address] = recent
    if len(recent) >= RATE_LIMIT_MAX_REQUESTS:
        return True
    _request_log[ip_address].append(now)
    return False


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = sanitize_form_field(request.form.get("name", ""), max_length=100)
        email = sanitize_form_field(request.form.get("email", ""), max_length=150)
        message = sanitize_form_field(request.form.get("message", ""), max_length=2000)

        if not name or not email or not message:
            flash("Please fill in all fields before submitting.", "error")
            return redirect(url_for("main.contact"))

        # In a real project this would send an email or save to a database.
        # For this student project, we just confirm it was "received".
        print(f"[contact form] {name} <{email}>: {message}")
        flash("Thanks! Your message has been received.", "success")
        return redirect(url_for("main.contact"))

    return render_template("contact.html")


@main_bp.route("/analyze", methods=["POST"])
def analyze():
    ip_address = request.remote_addr or "unknown"
    if _is_rate_limited(ip_address):
        flash("You're sending requests too quickly. Please wait a minute and try again.", "error")
        return redirect(url_for("main.index"))

    resume_text = ""
    uploaded_file = request.files.get("resume_file")
    pasted_text = request.form.get("resume_text", "")

    temp_path = None

    try:
        # Option 1: a PDF file was uploaded
        if uploaded_file and uploaded_file.filename:
            filename = secure_filename(uploaded_file.filename)

            if not allowed_file(filename, current_app.config["ALLOWED_EXTENSIONS"]):
                flash("Only PDF files are supported.", "error")
                return redirect(url_for("main.index"))

            # Save with a random name so we never trust the original filename
            temp_filename = generate_temp_filename(filename)
            temp_path = os.path.join(current_app.config["UPLOAD_FOLDER"], temp_filename)
            uploaded_file.save(temp_path)

            try:
                resume_text = extract_text_from_pdf(temp_path)
            except PDFParsingError as exc:
                flash(str(exc), "error")
                return redirect(url_for("main.index"))

        # Option 2: resume text was pasted directly
        elif pasted_text.strip():
            resume_text = pasted_text

        else:
            flash("Please upload a PDF or paste your resume text.", "error")
            return redirect(url_for("main.index"))

        resume_text = sanitize_text(resume_text)

        if len(resume_text.split()) < 20:
            flash("That doesn't look like enough resume content to analyze.", "error")
            return redirect(url_for("main.index"))

        # Run the (AI or fallback) analysis
        api_key = current_app.config.get("GEMINI_API_KEY")
        result = analyze_resume(resume_text, api_key=api_key)

        # Store in the session so the /result page can render it after redirect
        session["analysis_result"] = result

        return redirect(url_for("main.result"))

    except Exception:
        # Catch-all so we never leak a stack trace to the user.
        current_app.logger.exception("Unexpected error during resume analysis")
        flash("Something went wrong while analyzing your resume. Please try again.", "error")
        return redirect(url_for("main.index"))

    finally:
        # Always delete the temporary uploaded file, whether analysis
        # succeeded or failed - we never keep resumes on disk.
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@main_bp.route("/result")
def result():
    data = session.get("analysis_result")
    if not data:
        flash("No analysis found. Please upload or paste a resume first.", "error")
        return redirect(url_for("main.index"))

    return render_template("result.html", data=data)
