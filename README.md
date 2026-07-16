# Check Your Resume

> A simple resume analyzer made using Flask and Python.

I started building this project after seeing people talk about ATS (Applicant Tracking System) scores while applying for internships. I was curious about how resumes are checked before they reach recruiters, so I decided to build a small web application that could analyze resumes and point out possible improvements.

The idea isn't to create a perfect ATS engine. Instead, I wanted to learn how file uploads, PDF parsing, AI APIs, and backend development work together in one project.

**Current Status:** 🚧 Still under development.

---

## What it does

Currently, the application can:

- Upload a resume in PDF format
- Extract the resume text
- Estimate an ATS score
- Check formatting and readability
- Find missing keywords
- Suggest improvements using AI
- Remove uploaded files after analysis

The report is meant to give users an idea of what they can improve before applying for internships or jobs.

---

## Why Flask?

I chose Flask because I wanted to understand how a backend works instead of relying on full-stack frameworks. This project helped me learn routing, templates, file handling, environment variables, and API integration from scratch.

---

## Project Folder

```
resume-ats-checker
│
├── routes/
├── static/
│   ├── css/
│   └── js/
├── templates/
├── uploads/
├── utils/
├── app.py
├── config.py
└── requirements.txt
```

I tried to keep the folder structure simple so it's easy to understand and maintain.

---

## Things I Learned

Working on this project taught me a lot of things that I hadn't used together before.

- Working with Flask
- Uploading and validating files
- Reading text from PDF documents
- Using the Gemini API
- Organizing a Python project
- Writing cleaner HTML templates
- Basic security practices for file uploads

I also realized that extracting text from resumes isn't always straightforward because every resume has a different layout.

---

## Running the Project

Clone the repository

```bash
git clone https://github.com/codepiyusss/ATS-Check.git
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file and add your Gemini API key.

Start the server

```bash
python app.py
```

Open

```
http://127.0.0.1:5000
```

---

## Future Plans

There are still many things I want to improve.

- Resume vs Job Description matching
- Better ATS scoring logic
- DOCX support
- Downloadable report
- More accurate keyword detection
- Better mobile experience
- Improve UI while keeping it simple

---

## A Small Note

This project was built mainly for learning and practice. The ATS score generated here is only an estimate and shouldn't be treated as an official recruiter score. My goal was to understand how these systems work and build something useful while improving my backend development skills.

If you have any suggestions or find any issues, feel free to open one. I'm still learning, and every bit of feedback helps.
