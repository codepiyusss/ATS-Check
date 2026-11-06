# ATS-Check 2.0 — Implementation Roadmap

Based on `docs/PROJECT_AUDIT.md`. Assumes **Option A** (keep the flat folder layout and add `services/`, `data/`, `tests/`, `docs/`).

## How we work

- **One phase at a time.** Before each phase: objective, files that change, dependencies, risks. After each phase: summary, commands, test results, how to verify by hand, open issues.
- **Approval gates** (your 7 checkpoints) sit between groups of phases. Nothing past a gate starts until you approve it.
- **Git:** one branch per phase (for example `v2/phase-1-refactor`), branched from `main`, merged when you approve. Every phase ends with a suggested commit message.
- **The app stays runnable after every phase.**
- **Tests:** run after every phase. Results are reported as they actually come out, never assumed.

---

## Gate overview

| Gate | Your checkpoint | Phases | You approve |
|---|---|---|---|
| 1 | Review the audit | 0 | This document and the audit |
| 2 | Approve backend architecture | 1 | The refactor plan, then the refactored skeleton |
| 3 | Build and test the NLP engine | 2, 3, 4, 5 | Engine output on sample resumes + test report |
| 4 | Approve the UI redesign | 6, 7 | A design preview first, then the full pages |
| 5 | Implement Firebase | 8, 9 | Login works, history works |
| 6 | Test privacy and security | 10, 11 | Security checklist + full test run |
| 7 | Deploy and verify | 12, 13 | Live site passes the production checklist |

---

## Phase details

### Phase 0: Audit (done)
**Deliverables:** `PROJECT_AUDIT.md`, this roadmap.
**Acceptance:** you have reviewed both and answered the four open questions at the end of the audit.

---

### Phase 1: Refactor backend architecture (Gate 2)
**Objective:** tidy the structure without changing behaviour, so later phases have a clean place to land.

**Files that change:** `app.py`, `config.py`, `routes/main_routes.py` (split), new `routes/{main,analysis}.py`, new `services/`, `utils/` (moved helpers), new `tests/` skeleton, `requirements.txt`, `.gitignore`, `.env.example`.
**Delete:** `routes/Chunks/` (broken, unused).
**Depends on:** your answers to audit questions 1–4.

**Work:**
1. Config classes (Dev, Prod, Test). Production refuses to start without `SECRET_KEY`.
2. Split routes into blueprints. Keep the existing `/analyze` flow and its `finally` cleanup.
3. Add custom error handlers (404, 413, 429, 500) with friendly pages.
4. Add `/health` endpoint.
5. Fix `.gitignore` so `.env.example` can be committed, and add a placeholder `.env.example`.
6. Set up pytest with one smoke test (`GET /` returns 200).

**Acceptance criteria:**
- [ ] The app runs locally and behaves the same as before (upload, paste, result page).
- [ ] `pytest` passes.
- [ ] Production config fails fast if `SECRET_KEY` is missing.
- [ ] A file over 5 MB shows a friendly error, not a raw 413 page.

**Risks:** import paths break during the move. Mitigated by small commits and the smoke test.

---

### Phase 2: PDF extraction and career taxonomy (Gate 3)
**Objective:** reliable, safe input handling and the nine career profiles as data.

**Files:** `services/pdf_parser.py`, `services/resume_parser.py`, `utils/validators.py`, `utils/file_manager.py`, `data/skill_taxonomy/*.json` (9 files), fixtures.
**Depends on:** Phase 1.

**Work:**
- Layered validation: extension, MIME and magic bytes, size, page cap, extraction time limit.
- Section detection: contact, summary, education, experience, projects, skills, certifications, achievements. A section that is not found is reported as not found, never invented.
- Taxonomy JSON schema: required skills, optional skills, aliases, tools, frameworks, keywords, project terminology.

**Acceptance criteria:**
- [ ] Tests pass for: valid PDF, empty PDF, corrupted PDF, wrong file type, oversized file.
- [ ] Section detection is tested on at least 3 differently formatted sample resumes.
- [ ] Adding a tenth career field needs only a new JSON file.
- [ ] No resume text appears in logs.

**Risks:** column and table layouts confuse extraction. We report low confidence instead of guessing.

---

### Phase 3: NLP and matching engine (Gate 3)
**Objective:** replace substring matching with correct, explainable matching.

**Files:** `services/keyword_extractor.py`, `services/skill_matcher.py`, `services/job_description_parser.py`, `utils/text_cleaner.py`.
**Depends on:** Phase 2. **Dependencies added:** scikit-learn, NumPy.

**Work:**
- Normalisation, tokenisation, word-boundary matching, alias resolution ("ML" ↔ "Machine Learning").
- TF-IDF keywords from the job description.
- Three clearly separated match types: **exact**, **related**, **general text similarity** (cosine). Cosine similarity is never shown as a hiring probability.

**Acceptance criteria:**
- [ ] The audit's F1 case ("digital", "gitlab", "javascript-free", "sqlite-free", "reactive") matches **zero** skills.
- [ ] "ML" and "Machine Learning" resolve to the same skill and are counted once.
- [ ] Tests pass for keyword extraction, alias matching, missing-skill detection, JD parsing and similarity.
- [ ] Memory use stays well below the Render free-tier limit (measured, not guessed).

---

### Phase 4: Transparent scoring engine (Gate 3)
**Objective:** a score where every point can be explained.

**Files:** `services/scoring_engine.py`, a weights config, tests.
**Depends on:** Phase 3.

**Work:** the six configurable heuristic weights (skills 30, JD coverage 25, experience 15, projects 10, education/certifications 10, structure/readability 10). When no job description is given, the JD coverage weight is redistributed to the other components and the output says so. No base scores and no fixed fallback values. If analysis fails, an error is returned, not a number.

**Acceptance criteria:**
- [ ] Scores are always within 0–100 and component scores sum correctly.
- [ ] A skill is never counted twice.
- [ ] A missing section lowers only the relevant component, with a stated reason.
- [ ] The "30 × 'word'" case no longer receives a meaningful score; it returns insufficient content.
- [ ] Tests pass for weight calculation, empty input, missing sections, duplicates, invalid input and normalisation.
- [ ] The response schema includes the calculation breakdown.

---

### Phase 5: Resume enhancement engine (Gate 3)
**Objective:** useful rewrite suggestions that never invent facts.

**Files:** `services/enhancement_engine.py`, verb and phrase data, tests.
**Depends on:** Phase 2 (bullet extraction) and Phase 3 (keywords).

**Work:** detect weak verbs, vague phrases, repetition and missing metrics. Suggest rewrites using only words and technologies already present in the user's bullet or resume. Where a number would help, the suggestion prompts the user to add their own figure instead of making one up.

**Acceptance criteria:**
- [ ] Every suggestion carries a reason.
- [ ] Tests prove no suggestion adds a technology, number or responsibility that is not in the source.
- [ ] Original and suggested text are both returned.

**Gate 3 review:** you see the engine's output on sample resumes (before any UI), plus the full test report.

---

### Phase 6: Landing page and application UI (Gate 4)
**Objective:** the new design system and public pages.

**Depends on:** Phases 1 and 4 (so the UI shows real data).

**Process:** first a **design preview** (palette, type, one landing mock, one results mock) for your approval, *then* the full build.

**Work:** CSS variable system (dark default and light theme), landing, analyzer flow (upload, field, optional JD, processing state), About, Privacy. Lucide/SVG icons, no emoji icons. Keep the paste-text option.

**Acceptance criteria:**
- [ ] Works at phone, tablet and desktop widths.
- [ ] Fully usable with keyboard only, including the file picker (audit F13).
- [ ] Visible focus states, `prefers-reduced-motion` respected.
- [ ] Text contrast measured against WCAG AA.

### Phase 7: Dashboard and results interface (Gate 4)
**Work:** results page (overall and per-component scores, matched and missing skills, formatting issues, recommendations), enhancement view with accept / reject / edit and before-and-after, accessible score visuals with text summaries, downloadable report.

**Acceptance criteria:**
- [ ] Nothing is shown as a statistic unless it comes from real data (no fake stats for new users).
- [ ] Meaning is never conveyed by colour alone.
- [ ] Report export works with free libraries only.

---

### Phase 8: Firebase Authentication (Gate 5)
**Depends on:** Phase 6. **Needs from you:** a Firebase project (I will give exact steps).

**Work:** Google sign-in on the client, ID token sent in the `Authorization` header, verified with the Admin SDK, identity taken only from the verified token. Handle expired and invalid tokens. Guests can still run an analysis.

**Acceptance criteria:**
- [ ] Valid, invalid and expired tokens each tested.
- [ ] A user ID sent by the browser is ignored.
- [ ] No service-account JSON in the repo. Credentials come from environment variables.

### Phase 9: Firestore history (Gate 5)
**Work:** `users` and `analyses` collections, history list, view, delete report, delete all my data, Firestore security rules, retention policy. Only metadata and results are stored, not the resume text.

**Acceptance criteria:**
- [ ] A user can read and delete only their own records (tested with two users).
- [ ] Empty-history state is tested.
- [ ] Security rules are tested, not just written.

---

### Phase 10: Accessibility, security and privacy (Gate 6)
**Work:** Flask-Limiter with `ProxyFix`, CSRF on forms, secure headers, no resume content in logs, generic production errors, retention behaviour, accessibility pass with a checklist, and revision of the privacy copy so it matches what the app does.

### Phase 11: Testing and bug fixing (Gate 6)
**Work:** fill test gaps (frontend validation, error states, keyboard interaction), full run, fix what fails.

**Gate 6 acceptance criteria:**
- [ ] Full pytest run reported with real pass and fail counts.
- [ ] Manual security checklist completed (upload abuse, auth bypass attempts, rate-limit behaviour).
- [ ] Accessibility checklist completed.

---

### Phase 12: Production deployment (Gate 7)
**Needs from you:** Render and Firebase accounts. I provide the configuration (`requirements.txt` with gunicorn, `Procfile` or `render.yaml`, `.env.example`) and a step-by-step guide.

**Acceptance criteria:**
- [ ] The live site passes the production checklist (health check, login on the deployed domain, upload, history, delete).
- [ ] Debug mode is off, and `SECRET_KEY` and Firebase credentials come only from environment variables.
- [ ] Free-tier limits (cold starts, ephemeral disk, Firestore quotas) are documented honestly.

### Phase 13: README and documentation
**Work:** rewrite the README (features, architecture diagram, scoring explanation, setup, tests, deployment, privacy, limitations, roadmap) and the deployment guide. Screenshots are taken by you from the running app.

---

## Dependency map

```
0 → 1 → 2 → 3 → 4 → 5
              └──────┴──→ 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13
```

Phases 2–5 are the engine and can be shown without any UI. Phases 8–9 need the UI from Phases 6–7.

## What I cannot do for you

- Push commits to GitHub: you apply each phase's files and commit.
- Create your Firebase or Render accounts and projects: I provide exact steps.
- Verify the live deployment myself: I give you a checklist, and you report what you see.
- Test on your machine: I test in my own environment and report exactly what I ran.
