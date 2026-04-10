#!/usr/bin/env python3
"""
Inference script for Resume Screening Environment.
Runs 3 tasks: Easy, Medium, Hard difficulty levels.
"""

import subprocess
import sys
import os

# Auto-install missing packages
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from openai import OpenAI
except ImportError:
    print("[INFO] Installing openai...", flush=True)
    install_package("openai>=1.0.0")
    from openai import OpenAI

try:
    import requests
except ImportError:
    print("[INFO] Installing requests...", flush=True)
    install_package("requests>=2.31.0")
    import requests

import asyncio

sys.stdout.reconfigure(line_buffering=True)

# Environment variables
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
SERVER_URL = os.getenv("SERVER_URL", "https://sree-11-resume-screening-ai.hf.space")
MAX_STEPS = 10
TEMPERATURE = 0.3
MAX_TOKENS = 50

if not API_KEY or not API_BASE_URL:
    print("[ERROR] Missing API credentials", flush=True)
    sys.exit(1)

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)


class ResumeAction:
    def __init__(self, decision):
        self.decision = decision


class ResumeClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.requests = requests

    def reset(self, difficulty="EASY"):
        """Reset with difficulty level."""
        response = self.requests.post(
            f"{self.base_url}/reset",
            json={"difficulty": difficulty.lower()}
        )
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


async def run_task(task_name, difficulty):
    """Run a single task and return the score, rewards, and decisions."""
    print(f"[INFO] Running {task_name} ({difficulty})", flush=True)
    
    env_client = ResumeClient(SERVER_URL)
    rewards = []
    decisions = []  # Track decisions for each step
    steps_taken = 0
    
    try:
        # Pass difficulty to reset
        result = env_client.reset(difficulty=difficulty)
        observation = result.observation
        
        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break
            
            # Get decision from LLM
            decision = get_llm_decision(observation)
            decisions.append(decision)  # Store the decision
            
            # Execute action
            action = ResumeAction(decision=decision)
            result = env_client.step(action)
            
            reward = result.reward if result.reward is not None else 0.0
            done = result.done
            
            rewards.append(reward)
            steps_taken = step
            
            if done:
                break
            
            if not done and hasattr(result, 'observation') and result.observation:
                observation = result.observation
        
        total_reward = sum(rewards) if rewards else 0.0
        # Ensure score is strictly between 0 and 1 (not 0.0, not 1.0)
        score = max(0.001, min(0.999, total_reward / MAX_STEPS))
        return score, steps_taken, rewards, decisions
        
    except Exception as e:
        print(f"[ERROR] Task failed: {e}", flush=True)
        return 0.5, 0, [], []
    finally:
        env_client.close()


async def main():
    # Define 3 tasks with different difficulties
    tasks = [
        ("task=easy", "EASY"),
        ("task=medium", "MEDIUM"),
        ("task=hard", "HARD"),
    ]
    
    for task_name, difficulty in tasks:
        print(f"[START] {task_name} env=resume_screening_env model={MODEL_NAME}", flush=True)
        
        score, steps, rewards, decisions = await run_task(task_name, difficulty)
        
        # Print steps with actual decisions
        for i, (reward, decision) in enumerate(zip(rewards, decisions), 1):
            done_status = "true" if i == steps else "false"
            print(f"[STEP] step={i} action={decision} reward={reward:.2f} done={done_status} error=null", flush=True)
        
        # Ensure score is between 0 and 1 (not exactly 0 or 1)
        final_score = max(0.001, min(0.999, score))
        rewards_str = ",".join(f"{r:.2f}" for r in rewards)
        success_status = "true" if final_score > 0.5 else "false"
        print(f"[END] success={success_status} steps={steps} score={final_score:.3f} rewards={rewards_str}", flush=True)
        print("", flush=True)  # Empty line between tasks


if __name__ == "__main__":
    asyncio.run(main())
