# AI Resume Analyzer
 
An AI-powered web app that scores how well a resume matches a job description, then generates an optimized version of the resume — with a validation layer that blocks the AI from inventing skills or experience the candidate doesn't actually have.
 
## Overview
 
Most "AI resume tools" just paste your resume into a chatbot and hope for a sensible answer. This project takes a stricter, two-stage approach:
 
1. **Analyze** — score the resume against the job description using a hybrid of embedding similarity and LLM judgment
2. **Optimize** — rewrite the resume to better match the job, then validate the rewrite against the original to catch any claims (skills, tools, experience) the AI added that aren't actually backed by the source resume. If the rewrite fails validation or scores lower than the original, the app falls back to the original resume rather than shipping a dishonest one.
## Features
 
- **PDF resume parsing** via PyMuPDF, plus TXT/CSV support for job descriptions
- **Hybrid match scoring** — combines OpenAI embedding cosine similarity (30%) with a GPT-4o mini judgment score (70%) into a single match percentage
- **Skill breakdown** — matched, partially matched, and missing skills between resume and job description
- **AI resume optimization** — rewrites the resume to close the gap with the job description
- **Anti-hallucination validation** — every optimized resume is checked against the original; unsupported claims trigger a strict retry, and if no safe improvement can be produced, the original resume is returned unchanged rather than a fabricated one
- **Before/after comparison** — professional summary and technical skills are compared side by side, with the overall score improvement
## Tech Stack
 
**Backend**
- Python, FastAPI
- OpenAI API — `gpt-4o-mini` for scoring/optimization, `text-embedding-3-small` for similarity
- PyMuPDF (`fitz`) for PDF text extraction
- Pydantic for request/response schemas
**Frontend**
- React 19 + TypeScript
- Vite
- jsPDF (for exporting results)
## How It Works
 
1. User uploads a resume (PDF) and a job description (PDF/TXT/CSV) through the React frontend
2. FastAPI backend extracts and cleans text from both files
3. `/analyze` generates embeddings for both documents, computes cosine similarity, and asks GPT-4o mini to independently score the match — the two scores are blended into a final match percentage, alongside matched/partial/missing skill lists
4. `/optimize` first extracts only the skills genuinely supported by the original resume, then asks the model to rewrite the resume against the job description
5. The rewrite is validated against the original resume text to catch unsupported claims; if it fails, a stricter retry runs with the flagged claims blocked
6. If no valid rewrite scores at or above the original, the original resume is returned as-is, with a warning explaining why
7. Results — match scores, skill gaps, and the before/after comparison — are returned to the frontend
## API Endpoints
 
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/debug/routes` | Lists all registered routes |
| `POST` | `/analyze` | Upload `resume_file` (PDF) + `job_file`, returns match score and skill breakdown |
| `POST` | `/optimize` | Upload `resume_file` (PDF) + `job_file`, returns a validated, optimized resume with before/after comparison |
 
## Getting Started
 
### Prerequisites
- Python 3.10+
- Node.js and npm
- An OpenAI API key
### Backend Setup
 
```bash
cd be
pip install -r requirements.txt
```
 
Create a `.env` file in `be/`:
 
```
OPENAI_API_KEY=your_api_key_here
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
MAX_RESUME_CHARS=30000
MAX_JOB_CHARS=12000
```
 
Run the backend:
 
```bash
uvicorn app.main:app --reload
```
 
The API will be available at `http://localhost:8000` (interactive docs at `/docs`).
 
### Frontend Setup
 
```bash
cd fe/resume-analyzer-ui
npm install
npm run dev
```
 
The app will be available at `http://localhost:5173`.
 
## Project Structure
 
```
File-To-Share/
├── be/
│   ├── app/
│   │   ├── main.py                # FastAPI app + routes
│   │   ├── core/config.py         # Settings (API key, model names, char limits)
│   │   ├── models/schemas.py      # Pydantic response models
│   │   ├── services/
│   │   │   ├── analyzer.py            # Hybrid embedding + LLM match scoring
│   │   │   ├── optimizer.py           # Optimization + validation/retry loop
│   │   │   ├── openai_service.py      # OpenAI API calls
│   │   │   ├── resume_comparison.py   # Before/after comparison builder
│   │   │   └── file_reader.py         # PDF/TXT/CSV text extraction
│   │   └── utils/text_cleaner.py
│   └── requirements.txt
└── fe/
    └── resume-analyzer-ui/         # React + TypeScript + Vite frontend
```
 
## Future Improvements
 
- Support for DOCX resume uploads
- Batch analysis against multiple job descriptions at once
- Persist analysis history per user
- Inline diff view for the optimized resume rather than a flat comparison
## Author
 
**Pradnya Gajare**
[LinkedIn](https://www.linkedin.com/in/pradnya-gajare-912011285/) | [GitHub](https://github.com/Pradnya3018)
