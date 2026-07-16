# Check Your Resume

A small web app that lets you upload (or paste) your resume and get
back an estimated ATS (Applicant Tracking System) compatibility
report — score, formatting/grammar/readability checks, keyword
matching, and improvement suggestions.

This was built as a learning project to practice full-stack
development with Flask.

## Features

- Upload a PDF resume or paste resume text directly
- Extracts text from PDFs with `pdfplumber`
- Generates an ATS score, formatting/grammar/readability scores,
  keyword match %, and suggestions
- Uses the Gemini API for AI-based analysis if a key is provided,
  otherwise falls back to a built-in rule-based analyzer
- Uploaded files are deleted immediately after processing — nothing
  is stored permanently

## Project Structure

```
resume-ats-checker/
├── app.py                 # App entry point
├── config.py               # Configuration (upload limits, secret key, etc.)
├── requirements.txt
├── .env.example
├── routes/
│   └── main_routes.py       # All page routes (home, about, contact, analyze, result)
├── utils/
│   ├── pdf_parser.py         # PDF validation + text extraction
│   ├── ai_analysis.py        # Gemini API call + fallback heuristic analyzer
│   └── helpers.py            # Small shared helper functions
├── templates/                # Jinja2 HTML templates
├── static/
│   ├── css/style.css
│   └── js/
└── uploads/                  # Temporary storage, auto-cleared
```

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your values:
   ```bash
   cp .env.example .env
   ```
   - `SECRET_KEY` — any random string, used by Flask sessions
   - `GEMINI_API_KEY` — optional. Leave blank to use the built-in
     fallback analyzer instead of calling the Gemini API.

4. Run the app:
   ```bash
   python app.py
   ```

5. Open `http://127.0.0.1:5000` in your browser.

## Security Notes

- Only `.pdf` files are accepted, and files are checked for the real
  PDF header (`%PDF-`), not just the file extension.
- Uploads are capped at 5 MB (`MAX_CONTENT_LENGTH` in `config.py`).
- Uploaded files are saved with a random filename in `uploads/` and
  deleted immediately after analysis (success or failure).
- Basic rate limiting is applied to the `/analyze` route.
- API keys and the Flask secret key are loaded from environment
  variables, never hardcoded.
- Errors are caught and shown as a friendly message — no stack traces
  or internal details are exposed to the user.

## Notes

This is a portfolio/learning project, not a production-grade SaaS
tool — the fallback analyzer especially is a simple heuristic, not a
real ATS engine. It's meant to demonstrate a complete, working
full-stack app end to end.
