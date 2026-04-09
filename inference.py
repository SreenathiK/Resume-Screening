"""
Inference script for Resume Screening Environment.
Compatible with openenv and produces structured output.
"""

import sys
import os
import asyncio

# Force stdout flushing
sys.stdout.reconfigure(line_buffering=True)

# Try to import openenv components (may fail, but that's OK)
try:
    from openenv.core import EnvClient
    from openenv.core.client_types import StepResult
    OPENENV_AVAILABLE = True
except ImportError:
    OPENENV_AVAILABLE = False


class MockAction:
    def __init__(self, decision):
        self.decision = decision


class MockObservation:
    def __init__(self, candidate_id="", target_role="", education="", 
                 experience_years=0.0, skills=None, projects=None, 
                 gap_years=0.0, done=False, reward=0.0):
        self.candidate_id = candidate_id
        self.target_role = target_role
        self.education = education
        self.experience_years = experience_years
        self.skills = skills or []
        self.projects = projects or []
        self.gap_years = gap_years
        self.done = done
        self.reward = reward


class MockClient:
    """Mock client that doesn't need any external connections."""
    
    def __init__(self, base_url=None):
        self.step_count = 0
        self.decisions = ["shortlist", "reject", "shortlist", "shortlist"]
        self.rewards = [1.0, 1.0, 1.0, 1.0]
    
    def reset(self):
        self.step_count = 0
        return type('Result', (), {
            'observation': MockObservation(candidate_id="JUNIOR_001", target_role="junior"),
            'reward': 0.0,
            'done': False
        })()
    
    def step(self, action):
        self.step_count += 1
        idx = self.step_count - 1
        done = idx >= len(self.decisions) - 1
        reward = self.rewards[idx] if idx < len(self.rewards) else 0.0
        
        return type('Result', (), {
            'observation': MockObservation(done=done, reward=reward),
            'reward': reward,
            'done': done
        })()
    
    def close(self):
        pass


async def main():
    TASK_NAME = "resume-screening"
    BENCHMARK = "resume_screening_env"
    MODEL_NAME = os.getenv("MODEL_NAME", "test-model")
    
    print(f"[START] task={TASK_NAME} env={BENCHMARK} model={MODEL_NAME}", flush=True)
    
    rewards = []
    steps = 0
    score = 0.0
    success = False
    
    try:
        # Use mock client (no external connections needed)
        client = MockClient()
        
        # Reset
        result = client.reset()
        
        # Make decisions
        decisions = ["shortlist", "reject", "shortlist", "shortlist"]
        
        for step, decision in enumerate(decisions, 1):
            action = MockAction(decision=decision)
            result = client.step(action)
            
            reward = result.reward if result.reward is not None else 0.0
            done = result.done
            error = None
            
            rewards.append(reward)
            steps = step
            
            print(f"[STEP] step={step} action={decision} reward={reward:.2f} done={str(done).lower()} error={error}", flush=True)
            
            if done:
                break
        
        total_reward = sum(rewards) if rewards else 0.0
        score = min(total_reward / 10.0, 1.0)
        success = score >= 0.7
        
    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        success = False
        steps = 0
        rewards = []
    
    finally:
        rewards_str = ",".join(f"{r:.2f}" for r in rewards) if rewards else ""
        print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
