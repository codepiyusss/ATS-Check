"""Measures real colour contrast of the design tokens in static/css/style.css (WCAG 2.x)."""
import os
import re

import pytest

CSS = os.path.join(os.path.dirname(__file__), "..", "..", "static", "css", "style.css")


def _tokens(selector):
    css = open(CSS, encoding="utf-8").read()
    block = re.search(re.escape(selector) + r"\s*\{(.*?)\n\}", css, re.S).group(1)
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})", block))


def _lum(hex_):
    def ch(c):
        c = int(c, 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = hex_[1:3], hex_[3:5], hex_[5:7]
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def ratio(a, b):
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


THEMES = {"dark": ":root", "light": '[data-theme="light"]'}

# (foreground token, background token, minimum ratio, why)
TEXT = [
    ("text", "bg", 4.5), ("text", "surface", 4.5), ("text", "surface-2", 4.5),
    ("muted", "bg", 4.5), ("muted", "surface", 4.5), ("muted", "surface-2", 4.5),
    ("on-primary", "primary", 4.5), ("on-primary", "primary-hover", 4.5),
    ("primary-text", "bg", 4.5), ("primary-text", "surface", 4.5), ("primary-text", "surface-2", 4.5),
    ("accent", "bg", 4.5), ("accent", "surface", 4.5),
    ("danger", "bg", 4.5), ("danger", "surface", 4.5),
]
NON_TEXT = [  # icons, borders of inputs, focus ring: WCAG 1.4.11 needs 3:1
    ("success", "surface", 3.0), ("success", "surface-2", 3.0),
    ("warning", "surface", 3.0), ("warning", "surface-2", 3.0),
    ("danger", "surface-2", 3.0),
    ("border-strong", "surface", 3.0), ("border-strong", "surface-2", 3.0), ("border-strong", "bg", 3.0),
    ("focus", "bg", 3.0), ("focus", "surface", 3.0),
]


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("fg,bg,minimum", TEXT + NON_TEXT)
def test_contrast(theme, fg, bg, minimum):
    t = _tokens(THEMES[theme])
    got = ratio(t[fg], t[bg])
    assert got >= minimum, f"{theme}: {fg} {t[fg]} on {bg} {t[bg]} = {got:.2f}:1 (needs {minimum})"


def test_brand_palette_from_the_spec_is_present():
    dark = _tokens(":root")
    assert dark["primary"].upper() == "#22C55E"
    assert dark["bg"].upper() == "#000E1B" and dark["accent"].upper() == "#FF6300"
    assert dark["text"].upper() == "#FFE9DA" and dark["surface"].upper() == "#111D2D"
    assert dark["surface-2"].upper() == "#172638" and dark["muted"].upper() == "#A8B6C3"


def test_reduced_motion_is_respected():
    assert "prefers-reduced-motion: reduce" in open(CSS, encoding="utf-8").read()
