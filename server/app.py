# server/app.py - Compatible with openenv

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Simple models (no openenv imports)
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
    done: bool = False
    reward: float = 0.0

# Simple environment
class ResumeScreeningEnvironment:
    def __init__(self):
        self.candidates = [
            {"id": "JUNIOR_001", "role": "junior", "exp": 1.5, "skills": ["Python"], "projects": ["Project A"], "truth": "shortlist"},
            {"id": "JUNIOR_002", "role": "junior", "exp": 8.0, "skills": ["Java"], "projects": ["Project B"], "truth": "reject"},
            {"id": "MID_001", "role": "mid", "exp": 3.5, "skills": ["Python", "React"], "projects": ["Project C"], "truth": "shortlist"},
            {"id": "SENIOR_001", "role": "senior", "exp": 7.0, "skills": ["Python", "AWS"], "projects": ["Project D"], "truth": "shortlist"},
        ]
        self.idx = 0
        self.reward_total = 0.0
    
    def reset(self):
        self.idx = 0
        self.reward_total = 0.0
        return self._get_obs()
    
    def step(self, action):
        if self.idx >= len(self.candidates):
            return self._get_obs(done=True)
        
        c = self.candidates[self.idx]
        reward = 1.0 if action.decision == c["truth"] else -0.5
        self.reward_total += reward
        self.idx += 1
        done = self.idx >= len(self.candidates)
        obs = self._get_obs(done=done)
        obs.reward = reward
        return type('Result', (), {'observation': obs, 'reward': reward, 'done': done})()
    
    def _get_obs(self, done=False):
        if done or self.idx >= len(self.candidates):
            return ResumeObservation(done=True, reward=self.reward_total)
        c = self.candidates[self.idx]
        return ResumeObservation(
            candidate_id=c["id"],
            target_role=c["role"],
            experience_years=c["exp"],
            skills=c["skills"],
            projects=c["projects"],
            ground_truth_decision=c["truth"]
        )

# Create app for openenv
try:
    from openenv.core.env_server.http_server import create_app
    app = create_app(
        ResumeScreeningEnvironment,
        ResumeAction,
        ResumeObservation,
        env_name="resume_screening_env",
        max_concurrent_envs=5,
    )
except ImportError:
    # Fallback if openenv not available
    app = FastAPI(title="Resume Screening Environment")
    env = ResumeScreeningEnvironment()
    
    @app.post("/reset")
    async def reset():
        obs = env.reset()
        return {"observation": obs.dict(), "reward": 0.0, "done": False}
    
    @app.post("/step")
    async def step(request: dict):
        action = ResumeAction(decision=request.get("decision", "hold"))
        result = env.step(action)
        return {"observation": result.observation.dict(), "reward": result.reward, "done": result.done}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}

# Required for openenv validate
def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
