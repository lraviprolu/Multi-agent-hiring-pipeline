# Enterprise Hiring Pipeline — Multi-Agent Orchestration

A production-style, multi-agent AI system that automates the candidate screening process. Given a resume and a job description, it routes candidates through a conditional pipeline i.e either to an interview stage or a skill gap report — without any human intervention at the routing layer.

---

## Problem Statement

Enterprise hiring teams face a common bottleneck: manually screening hundreds of resumes against job descriptions is slow, inconsistent, and expensive. Recruiters spend significant time reading resumes that may not even be qualified, and candidates who are close-but-not-ready receive no actionable feedback.

This project addresses three specific problems:

1. **No structured extraction** — resumes come in unstructured formats (PDF, DOCX, plain text) and must be normalized before any comparison can happen.
2. **Inconsistent scoring** — human evaluators apply different standards; an LLM-based scorer applies the same rubric every time.
3. **Binary outcomes** — most screening tools say yes/no. This pipeline gives qualified candidates a tailored interview plan and unqualified candidates a personalized improvement roadmap.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│            (entry point — accepts resume + JD path)         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    orchestrator.py                          │
│              HiringPipelineOrchestrator                     │
└──┬────────────────────────────────────────────────────────┬─┘
   │                                                        │
   ▼                                                        │
┌──────────────────┐    ┌──────────────────┐               │
│  file_reader.py  │───▶│  Agent 1         │               │
│  (PDF/DOCX/TXT)  │    │  Resume Parser   │               │
└──────────────────┘    │  CandidateProfile│               │
                        └────────┬─────────┘               │
                                 │                          │
                                 ▼                          │
                        ┌──────────────────┐               │
                        │  Agent 2         │               │
                        │  Skill Matcher   │               │
                        │  MatchResult     │               │
                        └────────┬─────────┘               │
                                 │                          │
                    ┌────────────┴──────────────┐           │
                    │   Conditional Routing      │           │
                    │   score > 85%  score ≤ 85% │           │
                    └─────┬──────────────┬───────┘           │
                          │              │                   │
                          ▼              ▼                   │
              ┌───────────────┐  ┌──────────────────┐       │
              │   Agent 3     │  │   Agent 4        │       │
              │   Interview   │  │   Gap Analysis   │       │
              │   Planner     │  │   GapReport      │       │
              │   5 Questions │  │   + Roadmap      │       │
              └───────────────┘  └──────────────────┘       │
```

**Data contracts between agents:**

```
file_reader     →  raw text string
resume_parser   →  CandidateProfile (name, skills, experience, roles, education)
skill_matcher   →  MatchResult (score, matched_skills, missing_skills, reasoning)
interview_planner → InterviewPlan (candidate_name, 5 questions)
gap_analysis    →  GapReport (candidate_name, score, missing_skills, recommendations)
```

---

## Project Structure

```
Multi-agent-hiring-pipeline/
│
├── main.py                    # Entry point
├── orchestrator.py            # Conditional routing logic
│
├── agents/
│   ├── resume_parser.py       # Agent 1 — structured extraction from raw resume text
│   ├── skill_matcher.py       # Agent 2 — scores candidate against job description
│   ├── interview_planner.py   # Agent 3 — generates 5 tailored questions (score > 85%)
│   └── gap_analysis.py        # Agent 4 — identifies gaps + learning roadmap (score ≤ 85%)
│
├── models/
│   └── candidate.py           # Typed dataclasses for all agent inputs/outputs
│
├── utils/
│   └── file_reader.py         # Handles PDF, DOCX, and TXT resume formats
│
├── sample_data/
│   ├── sample_resume.txt      # Example candidate resume
│   └── job_description.txt    # Example job description (Senior Data Engineer)
│
├── .env                       # GROQ_API_KEY (gitignored)
├── requirements.txt
└── README.md
```

---

## Step-by-Step: How the Code Works

### Step 1 — Entry Point (`main.py`)
Reads two CLI arguments: path to resume and path to job description. Loads the `.env` file for the API key, then hands control to the orchestrator.

```bash
python main.py sample_data/sample_resume.txt sample_data/job_description.txt
```

---

### Step 2 — Resume Reading (`utils/file_reader.py`)
Detects the file extension and routes to the appropriate parser:
- `.pdf` → `pdfplumber` extracts text page by page
- `.docx` → `python-docx` reads paragraph by paragraph
- `.txt` → standard file read

Output is a single raw text string passed to Agent 1.

---

### Step 3 — Agent 1: Resume Parser (`agents/resume_parser.py`)
Makes a Groq API call with a strict system prompt instructing the model to return only a JSON object. Extracts:
- Name, email, phone
- Years of experience
- Skills list
- Education
- Previous roles
- Professional summary

Returns a typed `CandidateProfile` dataclass. The strict JSON-only prompt and `temperature=0.1` ensures deterministic, parseable output.

---

### Step 4 — Agent 2: Skill Matcher (`agents/skill_matcher.py`)
Takes the `CandidateProfile` + raw job description text. Makes a second independent Groq API call to score the candidate from 0–100 by comparing their skills, experience level, and roles against the job requirements.

Returns a `MatchResult` with:
- `score` — numeric match percentage
- `matched_skills` — skills the candidate has that the JD needs
- `missing_skills` — skills the JD requires that the candidate lacks
- `reasoning` — plain-English explanation of the score

---

### Step 5 — Conditional Routing (`orchestrator.py`)
The orchestrator checks `match.score` against the threshold (`85.0`):

```python
if match.score > SKILL_MATCH_THRESHOLD:
    # route to Agent 3
else:
    # route to Agent 4
```

*This is the core of the multi-agent orchestration. Agents are not called in sequence blindly; the pipeline branches based on real output data.*

---

### Step 6a — Agent 3: Interview Planner (`agents/interview_planner.py`) — Score > 85%
Uses the candidate's matched skills, years of experience, and previous roles to generate exactly 5 interview questions. Questions are calibrated to the candidate. A candidate with Kafka experience gets a Kafka question; one with MLflow gets an MLOps question. Uses `temperature=0.7` for more varied, creative question generation.

---

### Step 6b — Agent 4: Gap Analysis (`agents/gap_analysis.py`) — Score ≤ 85%
Uses the missing skills list and current skill set to produce a personalized learning roadmap. Recommends specific courses, certifications, or tools the candidate should pursue. Uses `temperature=0.5` as it needs creativity but must stay grounded and specific.

---

## Why This Approach

### Why separate agents instead of one big prompt?
Each agent has a single responsibility with its own system prompt, temperature, and input/output contract. This makes agents independently testable, swappable, and debuggable. A single monolithic prompt would conflate concerns and produce less reliable structured output.

### Why typed dataclasses for agent I/O?
Passing raw dictionaries between agents is fragile. Typed `dataclasses` in `models/candidate.py` enforce a contract between agents — if an agent's output changes shape, the error surfaces immediately rather than silently corrupting downstream results.

### Why `llama-3.3-70b-versatile`?
- The 70B parameter scale handles nuanced skill matching and question generation better than smaller models
- Strong instruction-following reduces JSON parse failures compared to smaller alternatives like `llama-3.1-8b-instant`

### Why `temperature=0.1` for parsing/matching and `temperature=0.7` for questions?
- Parsing and scoring tasks need **consistency** — the same resume should always produce the same score. Low temperature minimizes randomness.
- Question generation benefits from **variety** — higher temperature produces more diverse, non-repetitive interview questions.

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/lraviprolu/Multi-agent-hiring-pipeline.git
cd Multi-agent-hiring-pipeline

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your .env file with your Groq API key (free at console.groq.com)
echo "GROQ_API_KEY=your_key_here" > .env

# 4. Run the pipeline
python main.py sample_data/sample_resume.txt sample_data/job_description.txt
```

---

## Sample Output

**If score > 85% (Interview Path):**
```
► Agent 1: Resume Parser       ✓ Extracted candidate profile
► Agent 2: Skill Matcher       ✓ Score: 91.0% — above threshold
✓ Score 91.0% > 85.0% → Routing to Interview Planner
► Agent 3: Interview Planner   ✓ Generated 5 tailored questions

Interview Questions for Alex Johnson
 1. Walk me through how you designed a Spark pipeline at TechCorp...
 2. How did you handle schema evolution in Snowflake when upstream...
 ...
```

**If score ≤ 85% (Gap Analysis Path):**
```
► Agent 1: Resume Parser       ✓ Extracted candidate profile
► Agent 2: Skill Matcher       ✓ Score: 62.0% — below threshold
✗ Score 62.0% ≤ 85.0% → Routing to Gap Analysis
► Agent 4: Gap Analysis        ✓ Generated gap report

Gap Report for Candidate
 Missing Skills: dbt, Kubernetes, Airflow
 Recommendations: Begin with the official dbt Learn course...
```

---

## Requirements

```
groq
pdfplumber
python-docx
python-dotenv
rich
```

---

## Disclaimer

This project is intended for educational and portfolio demonstration purposes only. It is not production-ready hiring software and should not be used as the sole basis for any real employment decisions.

- **AI outputs are not guarantees.** Skill match scores, interview questions, and gap reports are generated by a large language model and may contain inaccuracies, biases, or inconsistencies.
- **No bias auditing has been performed.** LLM-based screening systems can reflect or amplify biases present in training data. Any real-world deployment would require fairness audits and human oversight to comply with employment law and ethical standards.
- **Resume data is processed externally.** Resumes sent to the Groq API are subject to Groq's data privacy and terms of service. Do not use real candidate data without appropriate consent and legal review.
- **The 85% threshold is arbitrary.** The routing threshold used in this demo was chosen for illustration purposes and has no empirical basis. A production system would require calibration and validation.

This project demonstrates multi-agent orchestration patterns, conditional routing, and structured LLM output  and is not a substitute for qualified human recruiters or compliant HR software.
