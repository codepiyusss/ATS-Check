"""Career fields the analyzer offers. (Phase 2 will load these from JSON taxonomy files.)"""

CAREER_FIELDS = [
    ("general", "General / not sure"),
    ("ai_ml", "AI/ML Engineer"),
    ("python_developer", "Python Developer"),
    ("data_analyst", "Data Analyst"),
    ("data_scientist", "Data Scientist"),
    ("frontend_developer", "Frontend Developer"),
    ("backend_developer", "Backend Developer"),
    ("fullstack_developer", "Full Stack Developer"),
    ("java_developer", "Java Developer"),
    ("cybersecurity", "Cybersecurity Analyst"),
]

_LABELS = dict(CAREER_FIELDS)


def is_valid_field(field_id):
    return field_id in _LABELS


def field_label(field_id):
    return _LABELS.get(field_id, _LABELS["general"])
