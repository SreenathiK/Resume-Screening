---
title: Resume Screening Environment
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
sdk_version: "1.0"
app_file: server/app.py
pinned: false
---

# Resume Screening Environment

An AI-powered system that automatically screens job candidates for software engineering roles (Junior, Mid, Senior). An LLM agent evaluates resumes and decides to shortlist, reject, or hold candidates based on role requirements.

## Features

- 🎯 **3 Difficulty Levels** - Easy, Medium, Hard
- 👥 **3 Job Roles** - Junior, Mid-level, Senior Engineer
- 📊 **Realistic Data** - Education, skills, projects, experience, career gaps
- 🐳 **Docker Support** - Containerized deployment
- 🔌 **OpenEnv Compatible** - Standard API for AI agents

## API Endpoints

| Endpoint  | Method |           Description                |
|-----------|--------|--------------------------------------|
| `/reset`  | POST   | Start a new screening session        |
| `/step`   | POST   | Make a decision on current candidate |
| `/health` | GET    | Health check                         |
| `/docs`   | GET    | Interactive API documentation        |

## Decisions

| Action      |           Description                |
|-------------|--------------------------------------|
| `shortlist` | Candidate meets requirements         |
| `reject`    | Candidate does not meet requirements |
| `hold`      | Borderline case, needs review        |

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn server.app:app --reload --port 7860

# Run inference (another terminal)
python inference.py