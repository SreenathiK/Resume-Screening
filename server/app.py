# server/app.py - Complete with main function

from fastapi import FastAPI, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import uuid

class ResumeAction(BaseModel):
    decision: str

class ResumeObservation(BaseModel):
    candidate_id: str = ""
    target_role: str = ""
    education: str = ""
    experience_years: float = 0.0
    skills: List[str] = []
    projects: List[str] = []
    certifications: Optional[List[str]] = None
    gap_years: float = 0.0
    ground_truth_decision: Optional[str] = None
    done: bool = False
    reward: float = 0.0

CANDIDATES = {
    "easy": [
        {"id": "JUNIOR_001", "role": "junior", "exp": 1.5, "skills": ["Python", "Java"], "projects": ["E-commerce"], "truth": "shortlist"},
        {"id": "JUNIOR_002", "role": "junior", "exp": 8.0, "skills": ["AWS", "Docker"], "projects": ["Cloud infra"], "truth": "reject"},
        {"id": "MID_001", "role": "mid", "exp": 3.5, "skills": ["Python", "React"], "projects": ["API Gateway"], "truth": "shortlist"},
        {"id": "SENIOR_001", "role": "senior", "exp": 7.0, "skills": ["System Design", "AWS"], "projects": ["Led team"], "truth": "shortlist"},
    ],
    "medium": [
        {"id": "MID_AMBIGUOUS_001", "role": "mid", "exp": 2.2, "skills": ["Python"], "projects": ["Small app"], "truth": "hold"},
        {"id": "JUNIOR_BORDER_001", "role": "junior", "exp": 2.5, "skills": ["Java", "Spring"], "projects": ["CRUD API"], "truth": "hold"},
        {"id": "SENIOR_PARTIAL_001", "role": "senior", "exp": 5.0, "skills": ["Python", "SQL"], "projects": ["Data pipeline"], "truth": "hold"},
        {"id": "MID_CAREER_CHANGE", "role": "mid", "exp": 1.0, "skills": ["JavaScript", "React"], "projects": ["Portfolio"], "truth": "hold"},
    ],
    "hard": [
        {"id": "NOISY_001", "role": "junior", "exp": 1.0, "skills": ["pythn", "javva"], "projects": ["proj"], "truth": "hold"},
        {"id": "MISSING_DATA", "role": "mid", "exp": 0, "skills": [], "projects": [], "truth": "reject"},
        {"id": "GAP_YEARS", "role": "senior", "exp": 10.0, "skills": ["Leadership"], "projects": ["Unknown"], "gap": 3.0, "truth": "hold"},
        {"id": "INCONSISTENT", "role": "junior", "exp": 5.0, "skills": ["Basic"], "projects": [], "truth": "reject"},
    ],
}


class ResumeScreeningEnvironment:
    def __init__(self, difficulty="easy"):
        self.difficulty = difficulty
        self.candidates = CANDIDATES.get(difficulty, CANDIDATES["easy"]).copy()
        self.idx = 0
        self.total_reward = 0.0
    
    def reset(self, difficulty=None):
        if difficulty:
            self.difficulty = difficulty
            self.candidates = CANDIDATES.get(difficulty, CANDIDATES["easy"]).copy()
        self.idx = 0
        self.total_reward = 0.0
        return self._get_obs()
    
    def step(self, action):
        if self.idx >= len(self.candidates):
            return self._get_obs(done=True)
        
        c = self.candidates[self.idx]
        truth = c.get("truth", "shortlist")
        
        if action.decision == truth:
            reward = 1.0
        elif action.decision == "hold":
            reward = 0.3
        else:
            reward = -0.5
        
        self.total_reward += reward
        self.idx += 1
        done = self.idx >= len(self.candidates)
        obs = self._get_obs(done=done)
        obs.reward = reward
        return obs
    
    def _get_obs(self, done=False):
        if done or self.idx >= len(self.candidates):
            return ResumeObservation(done=True, reward=self.total_reward)
        c = self.candidates[self.idx]
        return ResumeObservation(
            candidate_id=c["id"],
            target_role=c["role"],
            education=c.get("education", "Unknown"),
            experience_years=c.get("exp", 0.0),
            skills=c.get("skills", []),
            projects=c.get("projects", []),
            gap_years=c.get("gap", 0.0),
            ground_truth_decision=c.get("truth"),
            done=False,
            reward=0.0
        )


app = FastAPI(title="Resume Screening Environment")

environments = {}


@app.post("/reset")
async def reset(request: Dict[str, Any] = None):
    """Reset the environment with optional difficulty."""
    if request is None:
        request = {}
    
    difficulty = request.get("difficulty", "easy")
    session_id = str(uuid.uuid4())
    
    env = ResumeScreeningEnvironment(difficulty=difficulty)
    environments[session_id] = env
    
    obs = env.reset()
    return {
        "observation": obs.model_dump(),
        "reward": 0.0,
        "done": False,
        "session_id": session_id
    }


@app.post("/step")
async def step(request: Dict[str, Any]):
    """Execute a step."""
    session_id = request.get("session_id")
    if not session_id or session_id not in environments:
        raise HTTPException(status_code=404, detail="Session not found. Call /reset first.")
    
    env = environments[session_id]
    
    if "action" in request and isinstance(request["action"], dict) and "value" in request["action"]:
        action_map = {1: "shortlist", 2: "reject", 3: "hold"}
        decision = action_map.get(request["action"]["value"], "hold")
    elif "decision" in request:
        decision = request["decision"]
    else:
        raise HTTPException(status_code=400, detail="Invalid format")
    
    action = ResumeAction(decision=decision)
    result = env.step(action)
    
    return {
        "observation": result.model_dump(),
        "reward": result.reward,
        "done": result.done
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/")
async def root():
    return {
        "message": "Resume Screening Environment",
        "difficulty_levels": ["easy", "medium", "hard"],
        "endpoints": {
            "reset": "POST /reset with {\"difficulty\": \"easy\"}",
            "step": "POST /step with {\"action\": {\"value\": 1}}",
            "health": "GET /health"
        }
    }
def main():
    """Entry point for openenv."""
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7860)


if __name__ == "__main__":
    main()
