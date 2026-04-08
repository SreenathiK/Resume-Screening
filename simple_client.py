"""
Simple HTTP Client for Resume Screening Environment.
No WebSocket, no aiohttp - uses only requests.
"""

import requests
from typing import Optional


class ResumeScreeningClient:
    """
    Simple HTTP client that works with the FastAPI server.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.env_id = None
        self.current_observation = None
    
    def reset(self):
        """Reset the environment via HTTP."""
        response = requests.post(f"{self.base_url}/reset")
        if response.status_code != 200:
            raise Exception(f"Reset failed: {response.text}")
        
        data = response.json()
        self.env_id = data.get("env_id")
        from models import ResumeObservation
        self.current_observation = ResumeObservation(**data["observation"])
        
        return type('Result', (), {
            'observation': self.current_observation,
            'reward': data.get("reward", 0.0),
            'done': data.get("done", False)
        })()
    
    def step(self, action):
        """Execute a step via HTTP."""
        if not self.env_id:
            raise Exception("Must call reset() first")
        
        response = requests.post(
            f"{self.base_url}/step",
            json={"decision": action.decision, "env_id": self.env_id}
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
    
    def close(self):
        """Close the client."""
        pass
class AsyncResumeScreeningClient:
    """
    Async wrapper for the HTTP client.
    Uses threading to make sync calls async.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self._client = ResumeScreeningClient(base_url)
    
    async def reset(self):
        """Async reset."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._client.reset)
    
    async def step(self, action):
        """Async step."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._client.step, action)
    
    async def close(self):
        """Async close."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._client.close)
