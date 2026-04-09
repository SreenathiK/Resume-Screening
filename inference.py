"""
Inference script for Resume Screening Environment.
MUST use the provided API_BASE_URL and API_KEY - NO FALLBACKS!
"""

import asyncio
import os
import sys

sys.stdout.reconfigure(line_buffering=True)

try:
    from openai import OpenAI
except ImportError:
    print("[ERROR] openai not installed. Please run: pip install openai", flush=True)
    sys.exit(1)

# MUST use THEIR environment variables - no defaults!
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

# They will fail validation if these are missing
if not API_KEY or not API_BASE_URL:
    print("[ERROR] Missing API_KEY or API_BASE_URL", flush=True)
    sys.exit(1)

TASK_NAME = os.getenv("TASK_NAME", "resume-screening")
BENCHMARK = os.getenv("BENCHMARK", "resume_screening_env")
SERVER_URL = os.getenv("SERVER_URL", "https://sree-11-resume-screening-ai.hf.space")
MAX_STEPS = 10
TEMPERATURE = 0.3
MAX_TOKENS = 50

print(f"[INFO] Using API_BASE_URL: {API_BASE_URL}", flush=True)
print(f"[INFO] Using MODEL: {MODEL_NAME}", flush=True)

# Initialize client with THEIR proxy
client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)


class ResumeAction:
    def __init__(self, decision):
        self.decision = decision


class ResumeClient:
    def __init__(self, base_url):
        self.base_url = base_url
        import requests
        self.requests = requests
    
    def reset(self):
        response = self.requests.post(f"{self.base_url}/reset")
        data = response.json()
        return type('Result', (), {
            'observation': data.get('observation', {}),
            'reward': 0.0,
            'done': False
        })()
    
    def step(self, action):
        response = self.requests.post(
            f"{self.base_url}/step",
            json={"action": {"value": 1 if action.decision == "shortlist" else 2 if action.decision == "reject" else 3}}
        )
        data = response.json()
        return type('Result', (), {
            'observation': data.get('observation', {}),
            'reward': data.get('reward', 0.0),
            'done': data.get('done', False)
        })()
    
    def close(self):
        pass


def get_llm_decision(observation):
    """Call LLM API - MUST happen for each step."""
    
    prompt = f"""You are an HR recruiter. Evaluate this candidate:

Candidate: {observation.get('candidate_id', 'Unknown')}
Role: {observation.get('target_role', 'Unknown')}
Experience: {observation.get('experience_years', 0)} years
Skills: {', '.join(observation.get('skills', []))}
Projects: {', '.join(observation.get('projects', []))}

Respond with ONLY one word: shortlist, reject, or hold."""
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are an HR recruiter. Respond with only one word: shortlist, reject, or hold."},
            {"role": "user", "content": prompt}
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    decision = response.choices[0].message.content.strip().lower()
    
    if decision not in ["shortlist", "reject", "hold"]:
        decision = "hold"
    
    return decision


async def main():
    print(f"[START] task={TASK_NAME} env={BENCHMARK} model={MODEL_NAME}", flush=True)
    
    env_client = ResumeClient(SERVER_URL)
    rewards = []
    steps_taken = 0
    score = 0.0
    success = False
    
    try:
        result = env_client.reset()
        observation = result.observation
        
        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break
            
            # MUST call API for each decision
            decision = get_llm_decision(observation)
            
            action = ResumeAction(decision=decision)
            result = env_client.step(action)
            
            reward = result.reward if result.reward is not None else 0.0
            done = result.done
            
            rewards.append(reward)
            steps_taken = step
            
            print(f"[STEP] step={step} action={decision} reward={reward:.2f} done={str(done).lower()} error=null", flush=True)
            
            if not done and hasattr(result, 'observation') and result.observation:
                observation = result.observation
            
            if done:
                break
        
        total_reward = sum(rewards) if rewards else 0.0
        score = min(total_reward / MAX_STEPS, 1.0)
        success = score >= 0.7
        
    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        success = False
    
    finally:
        env_client.close()
        rewards_str = ",".join(f"{r:.2f}" for r in rewards)
        print(f"[END] success={str(success).lower()} steps={steps_taken} score={score:.3f} rewards={rewards_str}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
