# server/app.py - Complete version without openenv

from fastapi import FastAPI, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import uuid

# Define models directly in app.py to avoid imports
class ResumeAction(BaseModel):
    decision: str  # "shortlist", "reject", or "hold"

class ResumeObservation(BaseModel):
    candidate_id: str
    target_role: str
    education: str
    experience_years: float
    skills: List[str]
    projects: List[str]
    certifications: Optional[List[str]] = None
    gap_years: float = 0.0
    ground_truth_decision: Optional[str] = None
    done: bool = False
    reward: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


# Simple environment class
class ResumeScreeningEnvironment:
    def __init__(self):
        self.candidates = [
            {
                "candidate_id": "JUNIOR_001",
                "target_role": "junior",
                "education": "BS Computer Science",
                "experience_years": 1.5,
                "skills": ["Python", "Java", "Git", "SQL"],
                "projects": ["E-commerce website", "Task management app"],
                "certifications": None,
                "gap_years": 0.0,
                "ground_truth": "shortlist"
            },
            {
                "candidate_id": "JUNIOR_002",
                "target_role": "junior",
                "education": "MS Computer Science",
                "experience_years": 8.0,
                "skills": ["Python", "Java", "AWS", "Docker"],
                "projects": ["Large-scale system", "Microservices"],
                "certifications": None,
                "gap_years": 0.0,
                "ground_truth": "reject"
            },
            {
                "candidate_id": "MID_001",
                "target_role": "mid",
                "education": "BS Software Engineering",
                "experience_years": 3.5,
                "skills": ["Python", "JavaScript", "React", "Node.js"],
                "projects": ["Real-time chat app", "API gateway"],
                "certifications": None,
                "gap_years": 0.0,
                "ground_truth": "shortlist"
            },
            {
                "candidate_id": "SENIOR_001",
                "target_role": "senior",
                "education": "MS Computer Science",
                "experience_years": 7.0,
                "skills": ["Python", "System Design", "AWS", "Leadership"],
                "projects": ["Led team of 5", "Architected pipeline"],
                "certifications": None,
                "gap_years": 0.0,
                "ground_truth": "shortlist"
            }
        ]
        self.current_idx = 0
        self.total_reward = 0.0
        self.action_history = []
    
    def reset(self):
        self.current_idx = 0
        self.total_reward = 0.0
        self.action_history = []
        return self._get_observation()
    
    def step(self, action):
        if self.current_idx >= len(self.candidates):
            return self._get_observation(done=True)
        
        candidate = self.candidates[self.current_idx]
        ground_truth = candidate.get("ground_truth", "shortlist")
        
        # Calculate reward
        if action.decision == ground_truth:
            reward = 1.0
        elif action.decision == "hold":
            reward = 0.3
        else:
            reward = -0.5
        
        self.total_reward += reward
        self.current_idx += 1
        done = self.current_idx >= len(self.candidates)
        
        obs = self._get_observation(done=done)
        obs.reward = reward
        
        # Return a result object
        class Result:
            def __init__(self, observation, reward, done):
                self.observation = observation
                self.reward = reward
                self.done = done
        
        return Result(obs, reward, done)
    
    def _get_observation(self, done=False):
        if done or self.current_idx >= len(self.candidates):
            return ResumeObservation(
                candidate_id="",
                target_role="",
                education="",
                experience_years=0.0,
                skills=[],
                projects=[],
                done=True,
                reward=self.total_reward
            )
        
        c = self.candidates[self.current_idx]
        return ResumeObservation(
            candidate_id=c["candidate_id"],
            target_role=c["target_role"],
            education=c["education"],
            experience_years=c["experience_years"],
            skills=c["skills"],
            projects=c["projects"],
            certifications=c.get("certifications"),
            gap_years=c.get("gap_years", 0.0),
            ground_truth_decision=c.get("ground_truth"),
            done=False,
            reward=0.0
        )
    
    @property
    def state(self):
        return {"episode_id": str(uuid.uuid4()), "step_count": self.current_idx}


# Create FastAPI app
app = FastAPI(title="Resume Screening Environment")

# Initialize environment
_env = None

def get_env():
    global _env
    if _env is None:
        _env = ResumeScreeningEnvironment()
    return _env


@app.post("/reset")
async def reset():
    """Reset the environment."""
    env = get_env()
    obs = env.reset()
    return {
        "observation": obs.model_dump(),
        "reward": 0.0,
        "done": False
    }


@app.post("/step")
async def step(request: Dict[str, Any]):
    """Execute a step - accepts both formats."""
    env = get_env()
    
    # Handle both input formats
    decision = None
    
    # Format 1: {"action": {"value": 1}}
    if "action" in request and isinstance(request["action"], dict) and "value" in request["action"]:
        action_map = {1: "shortlist", 2: "reject", 3: "hold"}
        decision = action_map.get(request["action"]["value"])
        if not decision:
            raise HTTPException(status_code=400, detail=f"Invalid action value: {request['action']['value']}")
    
    # Format 2: {"decision": "shortlist"}
    elif "decision" in request:
        decision = request["decision"]
        if decision not in ["shortlist", "reject", "hold"]:
            raise HTTPException(status_code=400, detail=f"Invalid decision: {decision}")
    
    else:
        raise HTTPException(
            status_code=400, 
            detail="Invalid format. Use {'action': {'value': 1}} or {'decision': 'shortlist'}"
        )
    
    # Execute step
    action = ResumeAction(decision=decision)
    result = env.step(action)
    
    return {
        "observation": result.observation.model_dump(),
        "reward": result.reward,
        "done": result.done
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Resume Screening Environment",
        "docs": "/docs",
        "endpoints": {
            "reset": {"method": "POST", "path": "/reset"},
            "step": {"method": "POST", "path": "/step", "formats": [
                {"action": {"value": 1}},
                {"decision": "shortlist"}
            ]},
            "health": {"method": "GET", "path": "/health"}
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
