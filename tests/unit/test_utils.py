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
