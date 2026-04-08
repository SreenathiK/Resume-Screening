"""
FastAPI application for the Resume Screening Environment.
"""

import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import ResumeAction, ResumeObservation

# Try to import environment, or use built-in
try:
    from my_env_environment import ResumeScreeningEnvironment
except ModuleNotFoundError:
    # Built-in environment if file doesn't exist
    class ResumeScreeningEnvironment:
        def __init__(self):
            self.candidates = [
                {"candidate_id": "JUNIOR_001", "target_role": "junior", "experience_years": 1.5,
                 "skills": ["Python", "Java"], "projects": ["Project A"], "education": "BS CS", "gap_years": 0},
                {"candidate_id": "SENIOR_001", "target_role": "senior", "experience_years": 7.0,
                 "skills": ["Python", "AWS"], "projects": ["Project B"], "education": "MS CS", "gap_years": 0},
            ]
            self.current_idx = 0
            self.total_reward = 0.0
        
        def reset(self):
            self.current_idx = 0
            self.total_reward = 0.0
            return self._get_observation()
        
        def step(self, action):
            if self.current_idx >= len(self.candidates):
                return self._get_observation(done=True)
            c = self.candidates[self.current_idx]
            reward = 1.0 if action.decision == "shortlist" else -0.5
            self.total_reward += reward
            self.current_idx += 1
            done = self.current_idx >= len(self.candidates)
            obs = self._get_observation(done=done)
            obs.reward = reward
            return type('Result', (), {'observation': obs, 'reward': reward, 'done': done})()
        
        def _get_observation(self, done=False):
            if done or self.current_idx >= len(self.candidates):
                return ResumeObservation(candidate_id="", target_role="", education="", experience_years=0.0, skills=[], projects=[], done=True, reward=self.total_reward)
            c = self.candidates[self.current_idx]
            return ResumeObservation(candidate_id=c["candidate_id"], target_role=c["target_role"], education=c["education"], experience_years=c["experience_years"], skills=c["skills"], projects=c["projects"], gap_years=c.get("gap_years", 0.0), done=False, reward=0.0)

# Create FastAPI app
app = FastAPI(title="Resume Screening Environment")

_env = None
def get_env():
    global _env
    if _env is None:
        _env = ResumeScreeningEnvironment()
    return _env

@app.post("/reset")
async def reset():
    env = get_env()
    obs = env.reset()
    return {"observation": obs.model_dump() if hasattr(obs, 'model_dump') else obs.dict(), "reward": 0.0, "done": False}

@app.post("/step")
async def step(request: Dict[str, Any]):
    env = get_env()
    if "action" in request and isinstance(request["action"], dict) and "value" in request["action"]:
        action_map = {1: "shortlist", 2: "reject", 3: "hold"}
        decision = action_map.get(request["action"]["value"], "hold")
    elif "decision" in request:
        decision = request["decision"]
    else:
        raise HTTPException(status_code=400, detail="Invalid format")
    
    action = ResumeAction(decision=decision)
    result = env.step(action)
    return {"observation": result.observation.model_dump() if hasattr(result.observation, 'model_dump') else result.observation.dict(), "reward": result.reward, "done": result.done}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# THIS IS THE FIX - add this at the bottom
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
