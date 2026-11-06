# ATS-Check — Project Audit (Phase 0)

**Audited:** every source file in the uploaded `ATS-Check.zip` (app, config, routes, utils, templates, static JS/CSS, README, `.gitignore`, `requirements.txt`, git history).
**Method:** files were read in full. Claims marked **[verified]** were confirmed by running the code. Claims marked **[from reading]** come from reading the code but were not run.
**Status:** audit only. No application code has been changed.

---

## 1. Summary

ATS-Check is a small, tidy Flask app (about 20 source files) with a good foundation: an app factory, a blueprint, safe temporary-file handling, and a sensible 5 MB upload limit. It is a good base to enhance.

The weakest part is the **scoring logic**. It is not tied to a career field or a job description, it uses naive substring matching, and several score components are invented defaults rather than measurements. Those problems are exactly what the 2.0 engine is designed to fix, so the audit recommends replacing the scoring and keeping nearly everything else.

---

## 2. Existing architecture

```
ATS-Check/
├── app.py                  App factory: create_app(), registers one blueprint
├── config.py               SECRET_KEY, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, 5 MB limit, GEMINI_API_KEY
├── routes/
│   ├── main_routes.py      All routes: /, /about, /contact, /analyze, /result + in-memory rate limiter
│   └── Chunks/             Stray files (see finding F10)
├── utils/
│   ├── pdf_parser.py       pdfplumber text extraction + "%PDF-" header check
│   ├── ai_analysis.py      Gemini call OR keyword/regex heuristic fallback + score normalisation
│   └── helpers.py          allowed_file, temp filename, text sanitising
├── templates/              base, index, result, about, contact (Jinja2)
└── static/                 css/style.css (603 lines), js/script.js (nav toggle), js/upload.js (tabs, drag-drop)
```

### Request flow for `POST /analyze`

1. Rate-limit check by IP, using an in-memory dictionary.
2. Either a PDF upload or pasted text is accepted.
3. For a PDF: `secure_filename`, extension check, save under a random UUID name in `uploads/`, extract text with pdfplumber, delete the file in a `finally` block.
4. Text is sanitised and truncated to 15,000 characters, and at least 20 words are required.
5. `analyze_resume()` calls Gemini if `GEMINI_API_KEY` is set. If that fails or no key is set, it silently uses the heuristic scorer.
6. The result dictionary is stored in the Flask `session` (a signed browser cookie) and the user is redirected to `/result`.

---

## 3. Features that work today (to be preserved)

| Feature | Notes |
|---|---|
| PDF upload with drag-and-drop | Keep, and improve accessibility |
| **Paste resume text as an alternative to PDF** | Not in the 2.0 master prompt, but it works. Keep it, because working features should not be dropped without a reason. |
| PDF text extraction with friendly errors | Good error design (empty, corrupt, scanned PDFs). Reuse the structure. |
| Temporary-file deletion in `finally` | Correct pattern. Keep. |
| Random UUID temp filenames + `secure_filename` | Correct. Keep. |
| 5 MB upload cap via `MAX_CONTENT_LENGTH` | Keep |
| Input sanitising (control characters, length caps) | Reuse |
| App factory + blueprint structure | Reuse as the base for the refactor |
| Responsive navbar, flash messages, result page layout | Reuse the layout ideas, restyle for the new design system |

---

## 4. Findings

Severity: **High** means it breaks correctness or trust, **Medium** means a real risk or gap, **Low** means polish or hygiene.

### Scoring and analysis

**F1. Substring matching produces false positives. (High) [verified]**
`kw in text_lower` matches inside other words. A resume with no technical skills at all, containing only "digital", "gitlab-style", "javascript-free", "sqlite-free" and "reactive", was reported as matching **Java, Javascript, Sql, Git and React** and scored 48.
`"java"` also always matches inside `"javascript"`, and `"git"` matches inside `"digital"`.
*Fix:* word-boundary matching against a skill taxonomy with aliases (Phase 3).

**F2. One fixed list of 22 keywords is used for every resume. (High) [verified]**
Career field and job description are never considered. A nurse's resume is told that Python, Java, SQL, Docker and others are "missing" and receives a score of 38.
*Fix:* career profiles in JSON plus optional job-description matching (Phases 2–3).

**F3. Several scores are invented rather than measured. (High) [verified]**
- Formatting starts at a base of 40 points before anything is checked.
- "Grammar score" is 90 if average sentence length is 5–25 words, otherwise 65. No grammar is checked, so the "Grammar Review" feature card on the home page is misleading.
- "Readability score" is 85 if the word count is 200–900, otherwise 60.
- Result: a file containing the word "word" thirty times scores **35**.

*Fix:* remove the base and default values. Every point must come from a stated rule with a stated reason (Phase 4).

**F4. Gemini and the heuristic scorer silently replace each other. (High) [from reading]**
Both return the same fields, so the user cannot tell which engine produced a score, and the two methods give different numbers for the same resume. If Gemini fails, the failure is `print()`ed to the console only.
The Gemini model name (`gemini-1.5-flash`) is hard-coded and may be retired. The `google-generativeai` package is Google's older SDK. This should be checked before relying on it.
*Fix:* remove the Gemini dependency, per the zero-paid-API goal (Phases 3–5).

**F5. Privacy claims do not match behaviour when Gemini is enabled. (Medium) [from reading]**
The home page says the resume "is processed temporarily and never permanently stored". With a Gemini key set, up to 12,000 characters of the resume are sent to a third party. That is not disclosed anywhere.
*Fix:* removing Gemini resolves this. The new privacy copy must describe exactly what happens, including what is stored in Firestore.

### Security and reliability

**F6. Insecure fallback `SECRET_KEY`. (High) [from reading]**
`config.py` falls back to `"dev-secret-key-change-me"` when the environment variable is missing. A deployed app would then silently sign session cookies with a publicly known key.
*Fix:* fail at startup in production if `SECRET_KEY` is missing.

**F7. The rate limiter will not work on Render. (Medium) [from reading]**
- It is an in-memory dictionary, so each worker process has its own counts, and it resets on restart or sleep.
- Behind Render's proxy, `request.remote_addr` is the proxy's address, so every visitor can look like one user.
- Entries for old IPs are never removed.

*Fix:* Flask-Limiter plus `ProxyFix` for the real client IP (Phase 10).

**F8. Upload validation is shallow. (Medium) [from reading]**
Checked today: file extension and a `%PDF-` header. Not checked: MIME type, page count limit, extraction time limit, or total extracted size (the 15,000-character cut happens after every page has already been extracted).
Exceeding 5 MB raises a `413` error, and no error handler exists, so the user sees a raw default error page.
*Fix:* layered validation and custom error handlers (Phases 2 and 10).

**F9. No CSRF protection on forms. (Medium) [verified: no CSRF code exists]**
`/analyze` and `/contact` accept POSTs with no token.
*Fix:* CSRF for form posts. Firebase-authenticated API calls will use a bearer token instead, so no cookie is involved there.

**F10. The contact form does not do anything useful. (Medium) [from reading]**
The submitted name, email and message are `print()`ed to the server console, and the user is told "Your message has been received." Nothing is sent or saved, and personal data ends up in logs. On Render's free tier those logs are also ephemeral.
*Options:* remove the page, replace it with a `mailto:` link or a GitHub-issues link, or store messages in Firestore. This needs your decision. It conflicts with the rule "no nonfunctional buttons or placeholder pages".

### Code hygiene

**F11. Stray broken file: `routes/Chunks/Tokenization.py`. (Low) [verified]**
It is a copy of `app.py` with a syntax error (`SyntaxError: '(' was never closed`), a typo (`exit_ok`), and an undefined name (`Delete`). Nothing imports it, so it does not affect the running app, but it would crash if imported. `tokens.txt` beside it is empty.
*Fix:* delete both files in Phase 1.

**F12. Repo and deployment gaps. (Medium) [verified]**
- `.gitignore` lists `.env.example`, which prevents the example env file from being committed. The history shows it was added, then deleted.
- No `tests/`, no `Procfile` or `render.yaml`, no `gunicorn`, no health endpoint, no `docs/`.
- The README folder tree is labelled `resume-ats-checker` and only mentions Gemini.
- Git history contains two stray files, `junk.txt` and `Chunked_tokens`. This is harmless and does not need rewriting.
- Your local branch `yolo-trigger` is 2 commits (README edits) ahead of `main`.
- **Good news:** no `.env` or secrets were ever committed.

### Frontend and accessibility

**F13. Accessibility gaps. (Medium) [from reading]**
- The file input is inside a `hidden` attribute, so keyboard users cannot focus it. The label wraps it, but there is no keyboard route to open the file picker.
- The Upload / Paste tabs are plain buttons with no tab roles and no arrow-key support.
- Errors use `alert()` and flash `<div>`s with no `role="alert"`, so screen readers may not announce them.
- Progress bars have no `role="progressbar"` or text alternative. The score label uses text plus colour, which is good, and the suggestion ✔ is a text character.
- The mobile menu button has an `aria-label` but no `aria-expanded`.
- Colour contrast has not been measured yet. This will be checked during the redesign.

**F14. Branding and content issues. (Low) [from reading]**
- The site is called "CHECK YOUR RESUME" in the UI and "ATS-Check" in the repo.
- Footer GitHub and LinkedIn links point to the generic `github.com` and `linkedin.com`.
- The copyright year is hard-coded as `{{ 2026 }}`.
- The "Grammar Review" and "AI Suggestions" feature cards describe things the app does not really do.

**F15. Result data lives in a cookie. (Low) [from reading, not stress-tested]**
The whole result is stored in the signed `session` cookie, which browsers limit to about 4 KB. Today's result is probably small enough, but richer 2.0 results (breakdowns, suggestions) will not fit. There is also no way to revisit a past result.
*Fix:* hold results server-side briefly for guests and in Firestore for signed-in users.

---

## 5. Reuse / refactor / replace

| Component | Decision | Reason |
|---|---|---|
| `app.py` factory pattern | **Reuse**, extend | Already correct. Add config validation and error handlers. |
| `config.py` | **Refactor** | Add environment classes, remove the insecure default, remove the Gemini key. |
| `routes/main_routes.py` | **Refactor** | Split into several blueprints. Keep the `/analyze` control flow and its `finally` cleanup. |
| `utils/pdf_parser.py` | **Reuse and extend** | Keep the error design. Add MIME check, page cap, and section detection. |
| `utils/helpers.py` | **Reuse** | Keep the sanitising and filename helpers. Move `allowed_file` into the validators module. |
| `utils/ai_analysis.py` | **Replace** | Becomes taxonomy, matcher, scoring engine and enhancement engine. |
| Rate limiter in `main_routes.py` | **Replace** | Flask-Limiter. |
| Templates and CSS | **Rebuild on the new design system** | Keep the structure that works (base layout, flash messages). Restyle fully. |
| `upload.js` | **Refactor** | Keep the drag-and-drop idea. Fix accessibility, add progress and inline errors. |
| `routes/Chunks/*` | **Delete** | Broken and unused. |
| Gemini integration | **Remove** | Conflicts with zero paid API dependency and the privacy claims. |

---

## 6. Proposed implementation architecture

### Decision for you: folder layout

The master prompt suggests an `app/` package but also says to adapt to the repository and not to create duplicate structures. Two honest options:

- **Option A (recommended): keep your current flat layout and add to it.** It matches what you already know, keeps imports unchanged (`from utils...`, `from routes...`), and the diff stays small and easy to review.
- **Option B: move everything into an `app/` package.** This is more conventional for larger Flask apps but touches every import and every path, and has little benefit at this size.

The roadmap below assumes **Option A**.

### Target layout (Option A)

```
ATS-Check/
├── app.py                      # factory, kept
├── config.py                   # Dev / Prod / Test config classes
├── routes/
│   ├── main.py                 # landing, about, health check
│   ├── analysis.py             # upload, analyse, results
│   ├── auth.py                 # token verify, session endpoints   (Phase 8)
│   └── history.py              # list / view / delete reports      (Phase 9)
├── services/                   # NEW: all analysis logic, no Flask imports
│   ├── pdf_parser.py
│   ├── resume_parser.py        # section detection
│   ├── job_description_parser.py
│   ├── keyword_extractor.py
│   ├── skill_matcher.py
│   ├── scoring_engine.py
│   ├── enhancement_engine.py
│   ├── report_generator.py
│   └── firebase_service.py     # Phase 8–9
├── data/skill_taxonomy/        # NEW: one JSON per career field (9 fields)
├── utils/                      # validators, security, text_cleaner, file_manager
├── templates/  static/         # redesigned in Phases 6–7
├── tests/{unit,integration,fixtures}/
└── docs/
```

Key principle: **`services/` never imports Flask**, so the analysis engine can be tested on its own, quickly and with no web server.

### Technology decisions (with reasons)

| Question | Recommendation | Why |
|---|---|---|
| spaCy? | **Not initially** | The models are large and Render's free tier has limited RAM (about 512 MB, so check the current limit). scikit-learn plus regex plus the taxonomy covers the requirements. We can add spaCy later if tests show a real gap. |
| pandas? | **No** | Nothing here needs it. |
| Flask-CORS? | **No** | The frontend and backend are served from the same origin. |
| Chart.js? | **No, not initially** | CSS/SVG progress rings with a text summary are lighter and easier to make accessible. |
| Auth model | Firebase ID token in an `Authorization` header, verified with the Admin SDK on every protected request | The user ID comes only from the verified token, never from the browser. No cookie session is needed for those calls, so CSRF is not an issue there. |
| Guest access | **Yes**: guests can analyse but get no saved history | Matches the prompt, and results are held server-side briefly (see F15). |
| Contact page | **Decision needed** (see F10) | |

### Risks to plan around

1. **Render free tier sleeps and has ephemeral disk.** Nothing persistent may touch local disk. Uploaded PDFs are deleted immediately and user data goes to Firestore.
2. **Scoring will be heuristic.** The UI must say "estimate". No claim of matching real ATS software.
3. **Section detection from PDFs is imperfect** (columns, tables, icons). The parser must say "section not detected" rather than invent content.
4. **Enhancement suggestions must not invent facts.** Suggestions can only reuse technologies and results already in the user's own bullet.

---

## 7. Open questions for you

1. **Folder layout:** Option A (recommended) or Option B?
2. **Contact page:** remove it, replace it with a `mailto:` or GitHub-issues link, or save messages to Firestore?
3. **Branding:** is the product name "ATS-Check" everywhere? If so, "Check Your Resume" gets retired.
4. **Branch:** shall we start new work from `main`, using one branch per phase, and leave `yolo-trigger` alone?
