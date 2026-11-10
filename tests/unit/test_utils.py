import time

from utils.helpers import generate_temp_filename, sanitize_text
from utils.security import RateLimiter
from utils.validators import allowed_file


def test_allowed_file_accepts_pdf_any_case():
    assert allowed_file("cv.pdf", {"pdf"})
    assert allowed_file("CV.PDF", {"pdf"})


def test_allowed_file_rejects_others():
    assert not allowed_file("cv.exe", {"pdf"})
    assert not allowed_file("cv", {"pdf"})
    assert not allowed_file("", {"pdf"})
    assert not allowed_file("cv.pdf.exe", {"pdf"})


def test_temp_filename_is_random_and_keeps_extension():
    a, b = generate_temp_filename("my resume.pdf"), generate_temp_filename("my resume.pdf")
    assert a != b and a.endswith(".pdf")
    assert "resume" not in a  # original name must not leak into the path


def test_sanitize_strips_control_chars_and_truncates():
    assert sanitize_text("a\x00b\x07c") == "abc"
    assert len(sanitize_text("x" * 20000)) == 15000
    assert sanitize_text(None) == ""


def test_rate_limiter_blocks_after_max():
    rl = RateLimiter(window_seconds=60, max_requests=3)
    assert [rl.is_limited("ip") for _ in range(4)] == [False, False, False, True]


def test_rate_limiter_is_per_key():
    rl = RateLimiter(window_seconds=60, max_requests=1)
    assert rl.is_limited("a") is False
    assert rl.is_limited("b") is False
    assert rl.is_limited("a") is True


def test_rate_limiter_window_expires():
    rl = RateLimiter(window_seconds=0.1, max_requests=1)
    assert rl.is_limited("ip") is False
    assert rl.is_limited("ip") is True
    time.sleep(0.15)
    assert rl.is_limited("ip") is False


def test_keyword_display_names_are_properly_cased():
    from utils.ai_analysis import _analyze_with_heuristics
    text = "Built and developed sql and html and css apps on aws with node.js and a rest api. " * 3
    shown = _analyze_with_heuristics(text)["matched_keywords"]
    for expected in ("SQL", "HTML", "CSS", "AWS", "Node.js", "REST API"):
        assert expected in shown
    assert "Sql" not in shown and "Aws" not in shown


# ---------- client IP detection (matters behind Render's proxy) ----------

class _Req:
    def __init__(self, headers=None, remote_addr="10.0.0.1"):
        self.headers = headers or {}
        self.remote_addr = remote_addr


def test_client_ip_uses_true_client_ip_only_when_trusted():
    from utils.security import get_client_ip
    req = _Req({"True-Client-IP": "203.0.113.7"})
    assert get_client_ip(req, trust_proxy=True) == "203.0.113.7"
    assert get_client_ip(req, trust_proxy=False) == "10.0.0.1"  # header ignored: cannot be spoofed


def test_client_ip_falls_back_on_missing_or_garbage_header():
    from utils.security import get_client_ip
    assert get_client_ip(_Req(), True) == "10.0.0.1"
    assert get_client_ip(_Req({"True-Client-IP": "not-an-ip"}), True) == "10.0.0.1"
    assert get_client_ip(_Req({"True-Client-IP": "1.2.3.4, 5.6.7.8"}), True) == "10.0.0.1"
    assert get_client_ip(_Req(remote_addr=None), False) == "unknown"


def test_client_ip_accepts_ipv6():
    from utils.security import get_client_ip
    assert get_client_ip(_Req({"True-Client-IP": "2001:db8::1"}), True) == "2001:db8::1"


def test_rate_limiter_prunes_stale_keys():
    rl = RateLimiter(window_seconds=0.05, max_requests=1)
    for i in range(5001):
        rl.is_limited(f"ip{i}")
    time.sleep(0.08)
    rl.is_limited("trigger")
    assert len(rl._hits) < 100
