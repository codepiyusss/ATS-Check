"""Builds tiny valid PDFs in memory so tests need no binary fixture files."""


def make_pdf(text_lines):
    """Return bytes of a one-page PDF containing `text_lines` (list of str)."""
    def esc(s):
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content = "BT /F1 11 Tf 50 750 Td 14 TL\n"
    for line in text_lines:
        content += f"({esc(line)}) Tj T*\n"
    content += "ET"
    stream = content.encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    ).encode()
    return out


RESUME_LINES = [
    "Jane Doe  jane@example.com  +91 98765 43210",
    "Summary",
    "Python developer who built and developed web applications using Flask and SQL.",
    "Experience",
    "- Developed REST API services and improved test coverage using git and docker.",
    "- Implemented automated testing and optimized database queries for reporting.",
    "Education",
    "B.Tech Computer Science with projects in machine learning and data analysis.",
    "Skills",
    "Python, SQL, Git, Docker, HTML, CSS, Linux",
]
