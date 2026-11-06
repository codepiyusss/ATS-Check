import re

from tests.fixtures.pdf_factory import RESUME_LINES

LONG_TEXT = " ".join(RESUME_LINES)


def test_landing_has_cta_to_analyzer_and_dark_default(client):
    html = client.get("/").data.decode()
    assert 'href="/analyzer"' in html
    assert 'data-theme="dark"' in html


def test_landing_does_not_overclaim_unbuilt_features(client):
    html = client.get("/").data.decode()
    assert html.count("Coming soon") == 3  # career match, JD match, bullet rewrites
    assert "Live" in html


def test_every_page_has_skip_link_main_landmark_and_lang(client):
    for url in ("/", "/analyzer", "/about", "/contact", "/nope"):
        html = client.get(url).data.decode()
        assert '<html lang="en"' in html
        assert 'class="skip-link" href="#main"' in html
        assert 'id="main"' in html


def test_footer_year_is_not_hardcoded(client):
    from datetime import datetime, timezone
    assert str(datetime.now(timezone.utc).year) in client.get("/").data.decode()


def test_no_emoji_used_as_interface_icons(client):
    emoji = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B50\u2714]")
    for url in ("/", "/analyzer", "/about", "/contact"):
        assert not emoji.search(client.get(url).data.decode()), url


def test_privacy_copy_reflects_gemini_setting(app, client):
    app.config["GEMINI_API_KEY"] = None
    assert "Gemini" not in client.get("/").data.decode()
    app.config["GEMINI_API_KEY"] = "fake-key"
    assert "sent to Google" in client.get("/").data.decode()


# ---------- analyzer page accessibility ----------

def test_analyzer_inputs_are_labelled(client):
    html = client.get("/analyzer").data.decode()
    for field_id in ("resume_file", "resume_text", "career_field", "job_description"):
        assert f'id="{field_id}"' in html
    assert 'for="career_field"' in html and 'for="job_description"' in html
    assert 'for="resume_text"' in html and 'for="resume_file"' in html


def test_file_input_is_keyboard_focusable_not_hidden(client):
    """Audit F13: the old input used the `hidden` attribute so keyboards could not reach it."""
    html = client.get("/analyzer").data.decode()
    tag = re.search(r'<input type="file"[^>]*>', html).group(0)
    assert " hidden" not in tag and "sr-only" in tag


def test_tabs_use_aria_roles(client):
    html = client.get("/analyzer").data.decode()
    assert 'role="tablist"' in html and html.count('role="tab"') == 2
    assert html.count('role="tabpanel"') == 2 and 'aria-selected="true"' in html


def test_error_region_announces_to_screen_readers(client):
    assert 'id="resume-error" role="alert"' in client.get("/analyzer").data.decode()


def test_analyzer_lists_all_nine_fields_plus_general(client):
    html = client.get("/analyzer").data.decode()
    assert html.count("<option") == 10
    for label in ("AI/ML Engineer", "Cybersecurity Analyst", "Java Developer"):
        assert label in html


# ---------- career field + JD wiring ----------

def test_invalid_career_field_is_rejected(client):
    r = client.post("/analyze", data={"resume_text": LONG_TEXT, "career_field": "astronaut"})
    assert r.headers["Location"].endswith("/analyzer")
    with client.session_transaction() as s:
        assert any("career field" in m for _, m in s["_flashes"])


def test_career_field_shown_on_report(client):
    client.post("/analyze", data={"resume_text": LONG_TEXT, "career_field": "data_analyst"})
    html = client.get("/result").data.decode()
    assert "Data Analyst" in html
    assert "coming soon" in html.lower()  # honest about unused field


def test_job_description_is_not_stored_in_session(client):
    secret = "ConfidentialJobPostingText " * 20
    client.post("/analyze", data={"resume_text": LONG_TEXT, "career_field": "general",
                                  "job_description": secret})
    with client.session_transaction() as s:
        assert "ConfidentialJobPostingText" not in str(dict(s))
        assert s["analysis_result"]["jd_words"] == 20


# ---------- results page ----------

def test_results_use_progressbars_and_text_labels(client):
    client.post("/analyze", data={"resume_text": LONG_TEXT, "career_field": "general"})
    html = client.get("/result").data.decode()
    assert html.count('role="progressbar"') == 4
    assert 'role="img" aria-label="Estimated compatibility' in html
    assert "Not a grammar check" in html or "not a grammar check" in html


def test_results_hide_engine_placeholders(client):
    """'None detected' / 'N/A' are internal placeholders, not content to show users."""
    junk = "I enjoy gardening and cooking for my family every weekend with great dedication. " * 4
    client.post("/analyze", data={"resume_text": junk, "career_field": "general"})
    html = client.get("/result").data.decode()
    assert "None detected" not in html and ">N/A<" not in html
    assert "No keywords from the general list were found" in html
