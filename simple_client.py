"""
Simple HTTP Client for Resume Screening Environment.
No WebSocket required - uses pure HTTP requests.
"""

import requests
from typing import Optional


class AsyncSimpleResumeClient:
    """
    Async HTTP client that works with the FastAPI server.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.env_id = None
        self.current_observation = None
    
    async def reset(self):
        """Reset the environment via HTTP."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_reset)
    
    def _sync_reset(self):
        """Synchronous reset."""
        response = requests.post(f"{self.base_url}/reset")
        if response.status_code != 200:
            raise Exception(f"Reset failed: {response.text}")
        
        data = response.json()
        from models import ResumeObservation
        self.current_observation = ResumeObservation(**data["observation"])
        
        return type('Result', (), {
            'observation': self.current_observation,
            'reward': data.get("reward", 0.0),
            'done': data.get("done", False)
        })()
    
    async def step(self, action):
        """Execute a step via HTTP."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_step, action)
    
    def _sync_step(self, action):
        """Synchronous step."""
        response = requests.post(
            f"{self.base_url}/step",
            json={"decision": action.decision}
        )
        
        if response.status_code != 200:
            raise Exception(f"Step failed: {response.text}")
        
        data = response.json()
        
        if data.get("observation") and data["observation"].get("candidate_id"):
            from models import ResumeObservation
            self.current_observation = ResumeObservation(**data["observation"])
        
        return type('Result', (), {
            'observation': self.current_observation if data.get("observation") else None,
            'reward': data.get("reward", 0.0),
            'done': data.get("done", False)
        })()
    
    async def close(self):
        """Close the client."""
        pass
