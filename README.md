# 🧭 CareerPilot AI

### AI Career Intelligence Platform powered by Multi-Agent AI

CareerPilot AI is a full-stack AI Career Intelligence Platform that helps professionals optimise their careers through intelligent resume analysis, job matching, career strategy generation, interview preparation, and continuous career guidance.

Unlike traditional resume analysers, CareerPilot AI combines multiple specialised AI agents working together around a continuously evolving **Career Digital Twin** to provide personalised career intelligence.

It helps students, job seekers, and professionals:

🎯 Analyse resumes intelligently

💼 Match resumes with job descriptions

📊 Improve ATS compatibility

🧬 Build an evolving Career Digital Twin

🤖 Receive personalised AI career coaching

🗺️ Generate career roadmaps

🎤 Practice AI-powered mock interviews

📋 Track job applications in one place

---

# 🚀 Features

## 📄 Resume Intelligence

✅ Resume Upload (PDF & DOCX)

✅ Resume Parsing & Structuring

✅ Resume Version Management

✅ Resume Editing

✅ Resume Download

---

## 💼 Job Intelligence

✅ Job Description Upload

✅ AI Job Parsing

✅ Structured Job Intelligence

✅ Skill Extraction

---

## 🎯 Resume ↔ Job Match Engine

✅ ATS Match Score

✅ Skill Gap Analysis

✅ Missing Skills Detection

✅ Resume Improvement Suggestions

---

## 🧬 Career Digital Twin

✅ AI-generated Career Profile

✅ Strength & Weakness Analysis

✅ Career Readiness Score

✅ Skills Intelligence

✅ Timeline & Growth Tracking

---

## 🤖 AI Career Coach

✅ Personalised Career Advice

✅ Career Forecasting

✅ Learning Recommendations

✅ Market Intelligence

---

## 🗺️ Career Strategy Engine

✅ Weekly Goals

✅ Monthly Goals

✅ Learning Roadmaps

✅ Certification Recommendations

✅ Project Recommendations

✅ Progress Tracking

---

## 🎤 AI Mock Interview

✅ AI-generated Interview Questions

✅ Personalised Feedback

✅ Performance Insights

---

## 📋 Application Tracker

✅ Track Applications

✅ Application Status

✅ Match Score Monitoring

---

# 🏗️ System Architecture

```
                 User
                  │
                  ▼
        Streamlit Frontend
                  │
                  ▼
          FastAPI Backend
                  │
      ┌───────────┼────────────┐
      ▼           ▼            ▼
 Resume AI    Job AI      Career AI
      │           │            │
      └───────────┼────────────┘
                  ▼
         Career Digital Twin
                  │
                  ▼
    Career Coach & Strategy Agents
                  │
                  ▼
 Interview Agent • Match Engine
                  │
                  ▼
 PostgreSQL • ChromaDB • Redis
```

---

# 🛠️ Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy Async
- PostgreSQL
- Alembic

### AI

- LangChain
- OpenRouter / OpenAI
- ChromaDB
- Redis

### Frontend

- Streamlit

### Testing

- Pytest

### Authentication

- JWT Authentication

---

# 📂 Project Structure

```text
CareerPilot-AI/
│
├── src/
│   ├── agents/
│   │   ├── resume/
│   │   ├── job/
│   │   ├── career/
│   │   ├── interview/
│   │   └── strategy/
│   │
│   ├── api/
│   │   ├── routes/
│   │   ├── middleware/
│   │   └── main.py
│   │
│   ├── services/
│   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   └── engine.py
│   │
│   ├── infrastructure/
│   ├── schemas/
│   ├── config/
│   └── utils/
│
├── web/
│   ├── pages/
│   ├── components/
│   ├── styles/
│   └── app.py
│
├── tests/
├── alembic/
├── requirements.txt
├── README.md
└── .env
```

---

# 🎯 How It Works

### 1️⃣ Upload Resume

Users upload their resumes in PDF or DOCX format.

↓

### 2️⃣ Resume Intelligence

The Resume Agent parses the document, extracts structured information, and stores multiple resume versions.

↓

### 3️⃣ Upload Job Description

Users upload or create job descriptions.

↓

### 4️⃣ Job Intelligence

The Job Agent analyses requirements, skills, experience, and technologies.

↓

### 5️⃣ Match Intelligence

The Match Agent compares the resume against the job description and generates:

- ATS Match Score
- Skill Gap Analysis
- Missing Skills
- Improvement Suggestions

↓

### 6️⃣ Career Digital Twin

The Career Twin Agent continuously updates the user's evolving AI career profile using:

- Resume Data
- Skills
- Applications
- Job Matches
- Career Progress

↓

### 7️⃣ AI Career Intelligence

Additional AI agents generate:

- Career Advice
- Learning Roadmaps
- Certifications
- Projects
- Career Forecasts
- Interview Preparation

↓

### 8️⃣ Application Tracking

Users manage and monitor all job applications from a single dashboard.

---

# 📊 Example Workflow

```
Resume
      │
      ▼
Resume Intelligence
      │
      ▼
Job Intelligence
      │
      ▼
Match Intelligence
      │
      ▼
Career Digital Twin
      │
      ▼
Career Coach
      │
      ▼
Career Strategy
      │
      ▼
Mock Interview
```

---

# 💡 Future Improvements

- GitHub Integration
- LinkedIn Integration
- Portfolio Intelligence
- Recruiter Dashboard
- AI Resume Builder
- AI Cover Letter Generator
- Multi-language Support
- Email Automation
- Cloud Deployment
- Docker & Kubernetes Deployment

---

# 🧑‍💻 Author

**Hoor Shumail**

AI | Machine Learning | Agentic AI | Multi-Agent Systems | Career Intelligence

---

# 📜 License

This project is developed for educational, research, and portfolio purposes.