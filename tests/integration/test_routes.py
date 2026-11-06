import io
import os

from tests.fixtures.pdf_factory import make_pdf, RESUME_LINES

LONG_TEXT = " ".join(RESUME_LINES)


def _flashes(client):
    with client.session_transaction() as s:
        return [m for _, m in s.get("_flashes", [])]


def _post_pdf(client, data, filename="resume.pdf"):
    return client.post(
        "/analyze",
        data={"resume_file": (io.BytesIO(data), filename)},
        content_type="multipart/form-data",
    )


# ---------- simple pages ----------

def test_public_pages_load(client):
    for url in ("/", "/about", "/contact"):
        assert client.get(url).status_code == 200


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.get_json() == {"status": "ok"}


def test_unknown_page_gives_friendly_404(client):
    r = client.get("/nope")
    assert r.status_code == 404
    assert b"Page not found" in r.data
    assert b"Traceback" not in r.data


def test_contact_no_longer_accepts_posts(client):
    """The old form printed personal data to logs and sent it nowhere."""
    assert client.post("/contact", data={"name": "x"}).status_code == 405


def test_contact_page_links_to_github_issues(client):
    assert b"github.com/codepiyusss/ATS-Check/issues" in client.get("/contact").data


# ---------- analyze: input handling ----------

def test_analyze_with_nothing_submitted(client):
    r = client.post("/analyze", data={})
    assert r.status_code == 302 and r.headers["Location"].endswith("/")
    assert any("upload a PDF or paste" in m for m in _flashes(client))


def test_wrong_extension_is_rejected(client, upload_dir):
    _post_pdf(client, b"hello", filename="resume.exe")
    assert any("Only PDF" in m for m in _flashes(client))
    assert os.listdir(upload_dir) == []


def test_fake_pdf_is_rejected_and_file_deleted(client, upload_dir):
    _post_pdf(client, b"MZ not really a pdf", filename="resume.pdf")
    assert any("not a valid PDF" in m for m in _flashes(client))
    assert os.listdir(upload_dir) == []


def test_corrupted_pdf_is_rejected_and_file_deleted(client, upload_dir):
    _post_pdf(client, make_pdf(RESUME_LINES)[:60])
    assert _flashes(client)  # some friendly error was shown
    assert os.listdir(upload_dir) == []


def test_too_little_text_is_rejected(client):
    client.post("/analyze", data={"resume_text": "just a few words"})
    assert any("enough resume content" in m for m in _flashes(client))


def test_oversized_upload_gets_friendly_413(client):
    big = b"%PDF-1.4\n" + b"0" * (5 * 1024 * 1024 + 10)
    r = _post_pdf(client, big)
    assert r.status_code == 413
    assert b"5 MB" in r.data and b"Traceback" not in r.data


# ---------- analyze: happy paths ----------

def test_valid_pdf_full_flow(client, upload_dir):
    r = _post_pdf(client, make_pdf(RESUME_LINES))
    assert r.status_code == 302 and r.headers["Location"].endswith("/result")
    page = client.get("/result")
    assert page.status_code == 200
    assert b"Estimated ATS Compatibility Score" in page.data
    assert os.listdir(upload_dir) == [], "uploaded resume must be deleted after processing"


def test_pasted_text_flow(client):
    r = client.post("/analyze", data={"resume_text": LONG_TEXT})
    assert r.headers["Location"].endswith("/result")
    assert client.get("/result").status_code == 200


def test_result_without_analysis_redirects_home(client):
    r = client.get("/result")
    assert r.status_code == 302
    assert any("No analysis found" in m for m in _flashes(client))


# ---------- robustness ----------

def test_unexpected_error_is_generic_and_cleans_up(client, upload_dir, monkeypatch):
    def boom(*a, **k):
        raise ValueError("secret internal detail")

    monkeypatch.setattr("routes.analysis.analyze_resume", boom)
    r = _post_pdf(client, make_pdf(RESUME_LINES))
    assert r.status_code == 302
    msgs = _flashes(client)
    assert any("Something went wrong" in m for m in msgs)
    assert not any("secret internal detail" in m for m in msgs)
    assert os.listdir(upload_dir) == []


def test_rate_limit_kicks_in_after_five_requests(client):
    for _ in range(5):
        client.post("/analyze", data={})
    client.post("/analyze", data={})
    assert any("too quickly" in m for m in _flashes(client))
