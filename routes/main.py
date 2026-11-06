from flask import Blueprint, jsonify, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/contact")
def contact():
    return render_template("contact.html")


@main_bp.route("/health")
def health():
    """Used by Render (and you) to check the app is up. Reveals nothing private."""
    return jsonify(status="ok")
