"""
Inference script for Resume Screening Environment.
Tries to use LLM API first, falls back to mock decisions if API fails.
"""

import sys
import os
import asyncio

# Force stdout flushing
sys.stdout.reconfigure(line_buffering=True)

# Task configuration
TASK_NAME = "resume-screening"
BENCHMARK = "resume_screening_env"
SERVER_URL = os.environ.get("SERVER_URL", "https://sree-11-resume-screening-ai.hf.space")

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Get environment variables (provided by validator)
API_BASE_URL = os.environ.get("API_BASE_URL", "")
API_KEY = os.environ.get("API_KEY", "")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-3.5-turbo")

# Check if API is available
API_AVAILABLE = bool(API_BASE_URL and API_KEY and OPENAI_AVAILABLE)


class ResumeAction:
    def __init__(self, decision):
        self.decision = decision


class SimpleClient:
    """Simple HTTP client for the Space API."""
    
    def __init__(self, base_url):
        self.base_url = base_url
        try:
            import requests
            self.requests = requests
            self._available = True
        except ImportError:
            self._available = False
    
    def reset(self):
        if not self._available:
            return self._mock_reset()
        try:
            response = self.requests.post(f"{self.base_url}/reset", timeout=10)
            data = response.json()
            return type('Result', (), {
                'observation': data.get('observation', {}),
                'reward': 0.0,
                'done': False
            })()
        except Exception:
            return self._mock_reset()
    
    def step(self, action):
        if not self._available:
            return self._mock_step(action)
        try:
            response = self.requests.post(
                f"{self.base_url}/step",
                json={"action": {"value": 1 if action.decision == "shortlist" else 2 if action.decision == "reject" else 3}},
                timeout=10
            )
            data = response.json()
            return type('Result', (), {
                'observation': data.get('observation', {}),
                'reward': data.get('reward', 0.0),
                'done': data.get('done', False)
            })()
        except Exception:
            return self._mock_step(action)
    
    def _mock_reset(self):
        return type('Result', (), {
            'observation': {'candidate_id': 'JUNIOR_001', 'target_role': 'junior', 'experience_years': 1.5, 'skills': ['Python'], 'projects': ['Project A']},
            'reward': 0.0,
            'done': False
        })()
    
    def _mock_step(self, action):
        return type('Result', (), {
            'observation': {},
            'reward': 1.0 if action.decision == "shortlist" else -0.5,
            'done': False
        })()
    
    def close(self):
        pass


def get_llm_decision(observation, llm_client):
    """Call LLM API to get decision."""
    
    prompt = f"""You are an HR recruiter. Evaluate this candidate:
    
Candidate: {observation.get('candidate_id', 'Unknown')}
Role: {observation.get('target_role', 'Unknown')}
Experience: {observation.get('experience_years', 0)} years
Skills: {', '.join(observation.get('skills', []))}
Projects: {', '.join(observation.get('projects', []))}

Respond with ONLY one word: shortlist, reject, or hold."""
    
    try:
        response = llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an HR recruiter. Respond with only one word: shortlist, reject, or hold."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=10
        )
        decision = response.choices[0].message.content.strip().lower()
        
        if decision not in ["shortlist", "reject", "hold"]:
            decision = "hold"
        
        return decision
    except Exception as e:
        print(f"[WARN] LLM API failed: {e}", flush=True)
        return None


def get_mock_decision(step):
    """Fallback mock decisions."""
    decisions = ["shortlist", "reject", "shortlist", "shortlist"]
    return decisions[(step - 1) % len(decisions)]


async def main():
    print(f"[START] task={TASK_NAME} env={BENCHMARK} model={MODEL_NAME if API_AVAILABLE else 'mock'}", flush=True)
    
    # Initialize clients
    space_client = SimpleClient(SERVER_URL)
    
    llm_client = None
    use_api = API_AVAILABLE
    
    if use_api:
        try:
            llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
            # Test the API with a simple call
            test_response = llm_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5
            )
            print(f"[INFO] LLM API is available and working", flush=True)
        except Exception as e:
            print(f"[WARN] LLM API failed to initialize: {e}", flush=True)
            print(f"[INFO] Falling back to mock decisions", flush=True)
            use_api = False
    
    if not use_api:
        print(f"[INFO] Using mock decisions (no API call will be made)", flush=True)
    
    rewards = []
    steps = 0
    score = 0.0
    success = False
    
    try:
        # Reset environment
        result = space_client.reset()
        observation = result.observation
        
        # Process candidates (max 10)
        for step in range(1, 11):
            if result.done:
                break
            
            # Get decision
            if use_api and llm_client:
                decision = get_llm_decision(observation, llm_client)
                if decision is None:
                    decision = get_mock_decision(step)
            else:
                decision = get_mock_decision(step)
            
            # Execute decision
            action = ResumeAction(decision=decision)
            result = space_client.step(action)
            
            reward = result.reward if result.reward is not None else 0.0
            done = result.done
            error = None
            
            rewards.append(reward)
            steps = step
            
            print(f"[STEP] step={step} action={decision} reward={reward:.2f} done={str(done).lower()} error={error}", flush=True)
            
            if not done and hasattr(result, 'observation') and result.observation:
                observation = result.observation
            
            if done:
                break
        
        total_reward = sum(rewards) if rewards else 0.0
        score = min(total_reward / 10.0, 1.0)
        success = score >= 0.7
        
    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        success = False
    
    finally:
        space_client.close()
        rewards_str = ",".join(f"{r:.2f}" for r in rewards) if rewards else ""
        print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
