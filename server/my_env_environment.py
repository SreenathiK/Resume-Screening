# server/environment.py - Fixed Resume Screening Environment

from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import uuid

class TaskDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

@dataclass
class State:
    episode_id: str
    step_count: int

ROLE_SKILLS = {
    "junior": {
        "Python", "Java", "JavaScript", "Git", "SQL",
        "HTML/CSS", "C", "C++", "React", "Node.js"
    },
    "mid": {
        "Python", "JavaScript", "React", "Node.js", "Docker",
        "PostgreSQL", "REST APIs", "Redis", "CI/CD", "AWS",
        "Java", "Spring Boot", "MySQL", "TypeScript"
    },
    "senior": {
        "System Design", "AWS", "Leadership", "Mentoring",
        "Architecture", "Kubernetes", "Go", "Rust", "Python",
        "Team Management", "Distributed Systems", "C++"
    },
}
ROLE_SKILL_THRESHOLD = {
    "junior": 3,
    "mid":    5,
    "senior": 4,
}

def calculate_quality_score(candidate: Dict) -> float:
    """
    Calculate quality score (0.0 to 1.0) using role-aware skill matching.
    Always called at runtime — never hardcoded on candidates.

    Breakdown:
        Experience score  : 0.0 → 0.40  (role-specific ceiling)
        Skills score      : 0.0 → 0.40  (role-specific required skills)
        Education score   : 0.0 → 0.20
        Certification bonus: 0.0 → 0.05
        Gap year penalty  : up to -0.12
    """
    role = candidate.get("target_role", "junior")
    required_skills = ROLE_SKILLS.get(role, ROLE_SKILLS["junior"])
    threshold = ROLE_SKILL_THRESHOLD.get(role, 3)
    exp_ceiling = {"junior": 3.0, "mid": 6.0, "senior": 10.0}.get(role, 5.0)
    exp_score = min(candidate.get("experience_years", 0.0) / exp_ceiling, 1.0) * 0.40
    candidate_skills = {s.strip().lower() for s in candidate.get("skills", [])}
    required_lower = {s.lower() for s in required_skills}
    matched = len(candidate_skills & required_lower)
    skills_score = min(matched / threshold, 1.0) * 0.40
    education = candidate.get("education", "").lower()
    if "phd" in education:
        edu_score = 0.20
    elif any(k in education for k in ["ms", "master", "msc"]):
        edu_score = 0.18
    elif any(k in education for k in ["bs", "bachelor", "be", "btech"]):
        edu_score = 0.14
    elif any(k in education for k in ["bootcamp", "nanodegree", "diploma"]):
        edu_score = 0.08
    else:
        edu_score = 0.02
    cert_bonus = min(len(candidate.get("certifications") or []) * 0.02, 0.05)
    gap_penalty = min(candidate.get("gap_years", 0.0) * 0.03, 0.12)
    raw = exp_score + skills_score + edu_score + cert_bonus - gap_penalty
    return round(max(0.0, min(raw, 1.0)), 3)

def derive_is_borderline(quality_score: float) -> bool:
    """
    FIX 4 — always derived from quality_score, never hardcoded.
    Borderline zone: 0.40 < quality_score < 0.72
    """
    return 0.40 < quality_score < 0.72

CANDIDATES = {
    "easy": [
        {
            "candidate_id": "EASY_J001",
            "target_role": "junior",
            "education": "BS Computer Science, GPA 3.7, State University",
            "experience_years": 1.5,
            "skills": ["Python", "Java", "Git", "SQL", "HTML/CSS"],
            "projects": [
                "Built e-commerce site handling 500 daily users (Django + PostgreSQL)",
                "Task management REST API (Flask)",
            ],
            "certifications": ["AWS Cloud Practitioner"],
            "gap_years": 0.0,
            "ground_truth": "shortlist",
        },
        {
            "candidate_id": "EASY_J002",
            "target_role": "junior",
            "education": "MS Computer Science, Top-10 University",
            "experience_years": 8.0,
            "skills": ["Python", "Java", "AWS", "Docker", "Kubernetes", "System Design"],
            "projects": [
                "Architected microservices platform serving 1M users",
                "Led migration of monolith to distributed system",
            ],
            "certifications": ["AWS Solutions Architect", "GCP Professional"],
            "gap_years": 0.0,
            "ground_truth": "reject",      
        },
        {
            "candidate_id": "EASY_M001",
            "target_role": "mid",
            "education": "BS Software Engineering, City College",
            "experience_years": 3.5,
            "skills": ["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker"],
            "projects": [
                "Real-time chat application (WebSockets, Redis pub/sub)",
                "API gateway with rate limiting and auth middleware",
            ],
            "certifications": None,
            "gap_years": 0.0,
            "ground_truth": "shortlist",
        },
        {
            "candidate_id": "EASY_S001",
            "target_role": "senior",
            "education": "MS Computer Science, State University",
            "experience_years": 7.0,
            "skills": ["Python", "System Design", "AWS", "Leadership", "Mentoring", "Go"],
            "projects": [
                "Led team of 5 engineers, delivered product 2 weeks ahead of schedule",
                "Architected data pipeline processing 50GB/day (Kafka + Spark)",
            ],
            "certifications": ["AWS Solutions Architect"],
            "gap_years": 0.0,
            "ground_truth": "shortlist",
        },
        {
            "candidate_id": "EASY_J003",
            "target_role": "junior",
            "education": "High School Diploma",
            "experience_years": 0.0,
            "skills": ["Basic HTML"],
            "projects": [],
            "certifications": None,
            "gap_years": 0.0,
            "ground_truth": "reject",
        },
        {
            "candidate_id": "EASY_M002",
            "target_role": "mid",
            "education": "BS Computer Science, GPA 3.9",
            "experience_years": 4.0,
            "skills": ["Java", "Spring Boot", "MySQL", "Redis", "CI/CD", "Docker"],
            "projects": [
                "Payment service handling $2M daily transactions",
                "Reduced API latency by 40% via caching layer",
            ],
            "certifications": ["Oracle Java Certified"],
            "gap_years": 0.0,
            "ground_truth": "shortlist",
        },
        {
            "candidate_id": "EASY_S002",
            "target_role": "senior",
            "education": "BS Computer Engineering",
            "experience_years": 9.0,
            "skills": ["C++", "Python", "System Design", "AWS", "Team Management"],
            "projects": [
                "Principal engineer on autonomous vehicle perception stack",
                "Managed cross-functional team of 12 across 3 time zones",
            ],
            "certifications": ["AWS DevOps Professional"],
            "gap_years": 0.0,
            "ground_truth": "shortlist",
        },
        {
            "candidate_id": "EASY_J004",
            "target_role": "junior",
            "education": "BS Computer Science (Year 2, incomplete)",
            "experience_years": 0.5,
            "skills": ["Python", "C", "Git"],
            "projects": [
                "University assignment: simple calculator app",
                "CLI to-do list in Python",
            ],
            "certifications": None,
            "gap_years": 0.0,
            "ground_truth": "reject",      
        },
    ],
    "medium": [
        {
            "candidate_id": "MED_M001",
            "target_role": "mid",
            "education": "BS Computer Science, GPA 2.8",
            "experience_years": 2.2,
            "skills": ["Python", "Django", "SQL"],
            "projects": [
                "Internal CRM tool for 50 employees",
                "Automated report generation script",
            ],
            "certifications": None,
            "gap_years": 0.0,
            "ground_truth": "hold",        
        },
        {
            "candidate_id": "MED_J001",
            "target_role": "junior",
            "education": "Coding Bootcamp (6 months) + 2 years self-taught",
            "experience_years": 1.0,
            "skills": ["JavaScript", "React", "Node.js", "SQL"],
            "projects": [
                "Full-stack blog platform with auth and comments",
                "Weather app using public API",
            ],
            "certifications": ["freeCodeCamp Full Stack"],
            "gap_years": 0.5,
            "ground_truth": "hold",        
        },
        {
            "candidate_id": "MED_S001",
            "target_role": "senior",
            "education": "MS Computer Science",
            "experience_years": 5.0,
            "skills": ["Python", "SQL", "Airflow", "Spark"],
            "projects": [
                "Built ETL pipeline for analytics team",
                "Data warehouse migration to Redshift",
            ],
            "certifications": None,
            "gap_years": 0.0,
            "ground_truth": "hold",        
        },
        {
            "candidate_id": "MED_M002",
            "target_role": "mid",
            "education": "BS Mechanical Engineering (career change)",
            "experience_years": 1.0,
            "skills": ["Python", "JavaScript", "React", "Git"],
            "projects": [
                "Portfolio site with 5 React projects",
                "Python automation scripts for manufacturing",
            ],
            "certifications": ["Google IT Support", "Udacity React Nanodegree"],
            "gap_years": 1.0,
            "ground_truth": "hold",       
        },
        {
            "candidate_id": "MED_J002",
            "target_role": "junior",
            "education": "BS Information Technology, GPA 3.5",
            "experience_years": 2.5,
            "skills": ["Java", "SQL", "REST APIs", "Git"],
            "projects": [
                "CRUD API for university library system",
                "Android app for campus events (500 downloads)",
            ],
            "certifications": None,
            "gap_years": 0.0,
            "ground_truth": "shortlist",   
        },
        {
            "candidate_id": "MED_S002",
            "target_role": "senior",
            "education": "BS Computer Science",
            "experience_years": 6.0,
            "skills": ["PHP", "MySQL", "JavaScript", "Leadership"],
            "projects": [
                "E-commerce platform with 10k active users",
                "Mentored 2 junior developers",
            ],
            "certifications": None,
            "gap_years": 0.0,
            "ground_truth": "hold",        
        },
        {
            "candidate_id": "MED_M003",
            "target_role": "mid",
            "education": "MS Software Engineering",
            "experience_years": 3.0,
            "skills": ["Python", "REST APIs", "Docker", "PostgreSQL", "Git"],
            "projects": [
                "Image classification service deployed on AWS",
                "NLP sentiment analysis API for product reviews",
            ],
            "certifications": ["DeepLearning.AI Specialization"],
            "gap_years": 0.0,
            "ground_truth": "shortlist",   
        },
        {
            "candidate_id": "MED_J003",
            "target_role": "junior",
            "education": "BS Computer Science, GPA 3.2",
            "experience_years": 0.8,
            "skills": ["Python", "JavaScript", "HTML/CSS", "Git", "React"],
            "projects": [
                "Personal finance tracker (React + FastAPI)",
                "Fixed 3 bugs in popular open source npm package",
            ],
            "certifications": None,
            "gap_years": 0.0,
            "ground_truth": "shortlist",   
        },
    ],
    "hard": [
        {
            "candidate_id": "HARD_J001",
            "target_role": "junior",
            "education": "BS Comptr Sci",           
            "experience_years": 1.0,
            "skills": ["pythn", "javva", "giit"],    
            "projects": ["proj1", "proj2"],           
            "certifications": None,
            "gap_years": 0.0,
            "ground_truth": "hold",                  
        },
        {
            "candidate_id": "HARD_M001",
            "target_role": "mid",
            "education": "",                         
            "experience_years": 0.0,
            "skills": [],
            "projects": [],
            "certifications": None,
            "gap_years": 0.0,
            "ground_truth": "reject",                
        },
        {
            "candidate_id": "HARD_S001",
            "target_role": "senior",
            "education": "B.S. Comp. Eng.",          
            "experience_years": 10.0,
            "skills": ["Leadership", "Agile", "Scrum", "Stakeholder Mgmt"],
            "projects": [
                "Managed enterprise software delivery",
                "Led digital transformation initiative",
            ],
            "certifications": ["PMP", "Scrum Master"],
            "gap_years": 3.0,
            "ground_truth": "hold",                  
        },
        {
            "candidate_id": "HARD_J002",
            "target_role": "junior",
            "education": "Batchelor of Sciense, CS", 
            "experience_years": 5.0,                 
            "skills": ["Basic Python", "MS Office"],
            "projects": [],
            "certifications": None,
            "gap_years": 0.0,
            "ground_truth": "reject",                
        },
        {
            "candidate_id": "HARD_M002",
            "target_role": "mid",
            "education": "PhD Physics, MIT",
            "experience_years": 1.5,
            "skills": ["Python", "MATLAB", "C++", "Git"],
            "projects": [
                "Quantum simulation software used by 3 research labs",
                "High-performance numerical solver (10x faster than baseline)",
            ],
            "certifications": None,
            "gap_years": 0.0,
            "ground_truth": "hold",                  
        },
        {
            "candidate_id": "HARD_S002",
            "target_role": "senior",
            "education": "No formal degree (self-taught)",
            "experience_years": 8.0,
            "skills": ["Python", "AWS", "Kubernetes", "System Design", "Go", "Rust"],
            "projects": [
                "Founded and sold SaaS startup (50k users at exit)",
                "Core contributor to open source project (8k GitHub stars)",
                "Architected infrastructure now used by Fortune 500 company",
            ],
            "certifications": ["AWS Solutions Architect Professional"],
            "gap_years": 0.0,
            "ground_truth": "shortlist",             
        },
        {
            "candidate_id": "HARD_M003",
            "target_role": "mid",
            "education": "BS Comp. Sci.",            
            "experience_years": 4.0,
            "skills": ["Java", "Python", "AWS", "Docker", "React"],
            "projects": [
                "Worked on team that built internal tooling",  
                "Contributed to migration project",            
            ],
            "certifications": None,
            "gap_years": 2.0,
            "ground_truth": "hold",                 
        },
        {
            "candidate_id": "HARD_J003",
            "target_role": "junior",
            "education": "BS Computer Science, GPA 3.9, Ivy League",
            "experience_years": 0.3,
            "skills": ["Python", "Java", "Git", "SQL"],
            "projects": [
                "Research paper on graph algorithms (published, 2nd author)",
                "Competitive programming: Top 500 on LeetCode",
            ],
            "certifications": None,
            "gap_years": 0.0,
            "ground_truth": "shortlist",            
        },
    ],
}

def calculate_reward(decision: str, candidate: Dict, ground_truth: str) -> float:
    """
    Reward function with all 5 fixes applied:
      FIX 1 — role-aware quality scoring via calculate_quality_score
      FIX 2 — quality_score always calculated, never hardcoded
      FIX 4 — is_borderline always derived from quality_score

    Reward structure:
      +1.0  correct decision
      +0.2  bonus: correctly shortlisted high-quality candidate (>0.80)
      +0.4  hold bonus: candidate is genuinely borderline
      -0.2  hold penalty: candidate was clear-cut, hold was lazy
      -0.5  generic wrong decision
      -0.7  shortlisted a candidate that should be rejected
      -0.8  rejected a candidate that should be shortlisted
    Clamped to [-1.0, 1.0].
    """
    quality_score = calculate_quality_score(candidate)
    is_borderline = derive_is_borderline(quality_score)

    score = 0.0
    if decision == ground_truth:
        score += 1.0
    else:
        score -= 0.5
    if ground_truth == "shortlist" and decision == "reject":
        score = -0.8

    elif ground_truth == "reject" and decision == "shortlist":
        score = -0.7
    elif decision == "hold" and ground_truth != "hold":
        if is_borderline:
            score += 0.4    
        else:
            score -= 0.2    
    if quality_score > 0.80 and decision == "shortlist" and ground_truth == "shortlist":
        score += 0.2

    return round(max(min(score, 1.0), -1.0), 3)

class ResumeScreeningEnvironment:
    """
    Resume screening RL environment.

    Simulates an HR recruiter evaluating candidates across
    three difficulty levels: easy, medium, hard.

    FIX 5 — Score is normalized by actual candidate count,
    not a hardcoded MAX_STEPS value.
    """

    def __init__(self, difficulty: TaskDifficulty = TaskDifficulty.EASY):
        self.difficulty = difficulty
        self._state = State(episode_id=str(uuid.uuid4()), step_count=0)
        self._current_candidate_idx = 0
        self._score = 0.0
        self._action_history = []
        self._candidates = []
        self._load_candidates()

    def _load_candidates(self):
        key = (
            self.difficulty.value
            if isinstance(self.difficulty, TaskDifficulty)
            else str(self.difficulty).lower()
        )
        self._candidates = CANDIDATES.get(key, CANDIDATES["easy"]).copy()

    def reset(self, difficulty=None):
        """Reset the environment, optionally switching difficulty."""
        if difficulty is not None:
            if isinstance(difficulty, str):
                self.difficulty = TaskDifficulty(difficulty.lower())
            else:
                self.difficulty = difficulty
            self._load_candidates()

        self._state = State(episode_id=str(uuid.uuid4()), step_count=0)
        self._current_candidate_idx = 0
        self._score = 0.0
        self._action_history = []
        return self._get_observation()

    def step(self, action):
        """Evaluate one candidate and return the result."""
        from models import ResumeObservation

        self._state.step_count += 1

        if self._current_candidate_idx >= len(self._candidates):
            return self._make_result(self._get_observation(done=True), 0.0, True)

        candidate = self._candidates[self._current_candidate_idx]
        ground_truth = candidate.get("ground_truth", "shortlist")

        reward = calculate_reward(action.decision, candidate, ground_truth)
        self._score += reward
        qs = calculate_quality_score(candidate)
        self._action_history.append({
            "candidate_id":  candidate["candidate_id"],
            "decision":      action.decision,
            "ground_truth":  ground_truth,
            "quality_score": qs,
            "is_borderline": derive_is_borderline(qs),
            "reward":        reward,
        })

        self._current_candidate_idx += 1
        done = self._current_candidate_idx >= len(self._candidates)

        obs = self._get_observation(done=done)
        obs.reward = reward

        return self._make_result(obs, reward, done)

    def _get_observation(self, done=False):
        from models import ResumeObservation

        if done or self._current_candidate_idx >= len(self._candidates):
            return ResumeObservation(
                candidate_id="",
                target_role="",
                education="",
                experience_years=0.0,
                skills=[],
                projects=[],
                done=True,
                reward=self._score,
            )

        c = self._candidates[self._current_candidate_idx]
        return ResumeObservation(
            candidate_id=c["candidate_id"],
            target_role=c["target_role"],
            education=c.get("education", ""),
            experience_years=c.get("experience_years", 0.0),
            skills=c.get("skills", []),
            projects=c.get("projects", []),
            certifications=c.get("certifications"),
            gap_years=c.get("gap_years", 0.0),
            ground_truth_decision=c.get("ground_truth"),
            done=False,
            reward=0.0,
        )

    @staticmethod
    def _make_result(observation, reward, done):
        class Result:
            def __init__(self, obs, r, d):
                self.observation = obs
                self.reward = r
                self.done = d
        return Result(observation, reward, done)

    @property
    def state(self):
        return self._state

    @property
    def total_candidates(self):
        return len(self._candidates)

    @property
    def action_history(self):
        return self._action_history

    def get_session_summary(self) -> Dict:
        """
        Full episode stats.
        FIX 5 — normalized_score divides by actual candidate count.
        """
        if not self._action_history:
            return {"error": "No actions taken yet."}

        total = len(self._action_history)
        correct = sum(
            1 for a in self._action_history
            if a["decision"] == a["ground_truth"]
        )
        by_type = {"shortlist": 0, "reject": 0, "hold": 0}
        for a in self._action_history:
            by_type[a["decision"]] = by_type.get(a["decision"], 0) + 1

        return {
            "episode_id":        self._state.episode_id,
            "difficulty":        self.difficulty.value,
            "total_candidates":  total,
            "correct_decisions": correct,
            "accuracy":          round(correct / total, 3),
            "total_reward":      round(self._score, 3),
            "normalized_score":  round(self._score / total, 3),  # FIX 5
            "average_reward":    round(self._score / total, 3),
            "decisions_by_type": by_type,
            "per_candidate": [
                {
                    "candidate_id":  a["candidate_id"],
                    "decision":      a["decision"],
                    "ground_truth":  a["ground_truth"],
                    "quality_score": a["quality_score"],
                    "is_borderline": a["is_borderline"],
                    "reward":        a["reward"],
                    "correct":       a["decision"] == a["ground_truth"],
                }
                for a in self._action_history
            ],
        }
