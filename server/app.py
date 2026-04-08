# server/app.py - Simple working version

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

# Models
class ResumeAction(BaseModel):
    decision: str

class ResumeObservation(BaseModel):
    candidate_id: str = ""
    target_role: str = ""
    education: str = ""
    experience_years: float = 0.0
    skills: List[str] = []
    projects: List[str] = []
    gap_years: float = 0.0
    done: bool = False
    reward: float = 0.0

# Create app
app = FastAPI(title="Resume Screening Environment")

# Simple environment
class Env:
    def __init__(self):
        self.candidates = [
            {"id": "JUNIOR_001", "role": "junior", "exp": 1.5, "truth": "shortlist"},
            {"id": "JUNIOR_002", "role": "junior", "exp": 8.0, "truth": "reject"},
            {"id": "MID_001", "role": "mid", "exp": 3.5, "truth": "shortlist"},
            {"id": "SENIOR_001", "role": "senior", "exp": 7.0, "truth": "shortlist"},
        ]
        self.idx = 0
        self.total_reward = 0.0
    
    def reset(self):
        self.idx = 0
        self.total_reward = 0.0
        return self._get_obs()
    
    def step(self, action):
        if self.idx >= len(self.candidates):
            return self._get_obs(done=True)
        
        c = self.candidates[self.idx]
        reward = 1.0 if action.decision == c["truth"] else -0.5
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
            experience_years=c["exp"],
            ground_truth_decision=c["truth"]
        )

env = Env()

# Endpoints
@app.get("/")
def root():
    return {"message": "Resume Screening Environment", "endpoints": ["/health", "/reset", "/step"]}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/reset")
def reset():
    obs = env.reset()
    return {"observation": obs.model_dump(), "reward": 0.0, "done": False}

@app.post("/step")
def step(action: ResumeAction):
    obs = env.step(action)
    return {"observation": obs.model_dump(), "reward": obs.reward, "done": obs.done}

# For openenv validation
def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
