import json
import re

# A small, common set of technical/professional keywords used by the
# fallback analyzer to estimate keyword match. A real project could
# expand this list per job role.
COMMON_KEYWORDS = [
    "python", "java", "javascript", "sql", "html", "css", "git",
    "docker", "kubernetes", "aws", "rest api", "machine learning",
    "testing", "agile", "react", "node.js", "linux", "communication",
    "leadership", "problem solving", "data analysis", "excel",
]

ACTION_VERBS = [
    "built", "developed", "designed", "created", "led", "managed",
    "improved", "increased", "reduced", "implemented", "launched",
    "optimized", "automated", "analyzed",
]


def analyze_resume(resume_text, api_key=None):
    if api_key:
        try:
            return _analyze_with_gemini(resume_text, api_key)
        except Exception as exc:
            # Don't crash the request just because the AI call failed -
            # fall back to the local analyzer and note it in the logs.
            print(f"[ai_analysis] Gemini call failed, using fallback: {exc}")

    return _analyze_with_heuristics(resume_text)


def _analyze_with_gemini(resume_text, api_key):
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
You are an ATS (Applicant Tracking System) resume analyzer.
Analyze the resume text below and return ONLY valid JSON (no markdown,
no extra commentary) with exactly these keys:

{{
  "ats_score": <integer 0-100>,
  "formatting_score": <integer 0-100>,
  "grammar_score": <integer 0-100>,
  "readability_score": <integer 0-100>,
  "keyword_match_percent": <integer 0-100>,
  "matched_keywords": [<strings>],
  "missing_keywords": [<strings>],
  "strong_sections": [<strings>],
  "weak_sections": [<strings>],
  "suggestions": [<strings, max 6>],
  "overall_feedback": "<2-3 sentence summary>"
}}

Resume text:
\"\"\"{resume_text[:12000]}\"\"\"
"""

    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # Strip markdown code fences if the model adds them anyway
    raw_text = re.sub(r"^```(json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()

    data = json.loads(raw_text)
    return _normalize_result(data)


def _analyze_with_heuristics(resume_text):
    text_lower = resume_text.lower()
    word_count = len(resume_text.split())

    # --- Keyword matching ---
    matched = [kw for kw in COMMON_KEYWORDS if kw in text_lower]
    missing = [kw for kw in COMMON_KEYWORDS if kw not in text_lower][:8]
    keyword_match_percent = round((len(matched) / len(COMMON_KEYWORDS)) * 100)

    # --- Formatting score (very rough heuristic) ---
    has_bullets = bool(re.search(r"(^|\n)\s*[•\-\*]", resume_text))
    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume_text))
    has_phone = bool(re.search(r"(\+?\d[\d\-\s]{8,}\d)", resume_text))
    section_headers = len(re.findall(
        r"(?im)^(experience|education|skills|projects|summary|certifications)\b",
        resume_text
    ))

    formatting_score = 40
    formatting_score += 15 if has_bullets else 0
    formatting_score += 15 if has_email else 0
    formatting_score += 10 if has_phone else 0
    formatting_score += min(section_headers * 5, 20)
    formatting_score = min(formatting_score, 100)

    # --- Grammar score (rough proxy: sentence length + repeated words) ---
    sentences = re.split(r"[.!?]\s+", resume_text)
    avg_sentence_len = word_count / max(len(sentences), 1)
    grammar_score = 90 if 5 <= avg_sentence_len <= 25 else 65

    # --- Readability score (based on word/section balance) ---
    readability_score = 85 if 200 <= word_count <= 900 else 60

    # --- Action verbs used ---
    verbs_used = [v for v in ACTION_VERBS if v in text_lower]

    # --- Overall ATS score: weighted average of the above ---
    ats_score = round(
        keyword_match_percent * 0.35
        + formatting_score * 0.25
        + grammar_score * 0.2
        + readability_score * 0.2
    )

    strong_sections = []
    weak_sections = []
    if has_bullets:
        strong_sections.append("Experience formatting (bullet points detected)")
    else:
        weak_sections.append("Experience section (no bullet points detected)")

    if section_headers >= 3:
        strong_sections.append("Clear section structure")
    else:
        weak_sections.append("Section headers (Skills/Education/Experience unclear)")

    if len(verbs_used) >= 3:
        strong_sections.append("Use of action verbs")
    else:
        weak_sections.append("Weak or passive action verbs")

    suggestions = []
    if keyword_match_percent < 60:
        suggestions.append("Add more role-relevant technical keywords")
    if not has_bullets:
        suggestions.append("Use bullet points to list achievements")
    if len(verbs_used) < 3:
        suggestions.append("Use stronger action verbs (e.g. built, led, improved)")
    if word_count < 200:
        suggestions.append("Expand your resume with more detail on projects/experience")
    if word_count > 900:
        suggestions.append("Reduce unnecessary paragraphs and keep it concise")
    if not has_email or not has_phone:
        suggestions.append("Make sure contact details (email/phone) are clearly visible")
    if not suggestions:
        suggestions.append("Add measurable achievements (numbers, %, results)")

    overall_feedback = (
        f"This resume scored an estimated {ats_score}% for ATS compatibility. "
        f"It matched {len(matched)} of {len(COMMON_KEYWORDS)} common keywords "
        f"and contains roughly {word_count} words."
    )

    result = {
        "ats_score": ats_score,
        "formatting_score": formatting_score,
        "grammar_score": grammar_score,
        "readability_score": readability_score,
        "keyword_match_percent": keyword_match_percent,
        "matched_keywords": [k.title() for k in matched] or ["None detected"],
        "missing_keywords": [k.title() for k in missing],
        "strong_sections": strong_sections or ["N/A"],
        "weak_sections": weak_sections or ["N/A"],
        "suggestions": suggestions[:6],
        "overall_feedback": overall_feedback,
    }

    return _normalize_result(result)


def _normalize_result(data):
    def clamp_score(value):
        try:
            return max(0, min(100, int(value)))
        except (TypeError, ValueError):
            return 0

    return {
        "ats_score": clamp_score(data.get("ats_score", 0)),
        "formatting_score": clamp_score(data.get("formatting_score", 0)),
        "grammar_score": clamp_score(data.get("grammar_score", 0)),
        "readability_score": clamp_score(data.get("readability_score", 0)),
        "keyword_match_percent": clamp_score(data.get("keyword_match_percent", 0)),
        "matched_keywords": data.get("matched_keywords", []) or ["None detected"],
        "missing_keywords": data.get("missing_keywords", []) or [],
        "strong_sections": data.get("strong_sections", []) or ["N/A"],
        "weak_sections": data.get("weak_sections", []) or ["N/A"],
        "suggestions": (data.get("suggestions", []) or [])[:6],
        "overall_feedback": data.get("overall_feedback", "").strip() or "No feedback available.",
    }
