from flask import render_template

_MESSAGES = {
    404: ("Page not found", "That page doesn't exist. Check the address or go back home."),
    413: ("File too large", "That file is over the 5 MB limit. Please upload a smaller PDF."),
    429: ("Too many requests", "You're going a bit fast. Please wait a minute and try again."),
    500: ("Something went wrong", "An unexpected error occurred. Please try again."),
}


def _render(code):
    title, message = _MESSAGES[code]
    return render_template("error.html", code=code, title=title, message=message), code


def register_error_handlers(app):
    for code in _MESSAGES:
        app.register_error_handler(code, lambda err, c=code: _render(c))
