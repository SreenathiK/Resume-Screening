"""
Inference script for Resume Screening Environment.
Prints structured output to stdout for validation.
"""

import asyncio
import os
import sys
import json
from typing import List, Optional

# Force stdout to be unbuffered
sys.stdout.reconfigure(line_buffering=True)

from simple_client import AsyncSimpleResumeClient as ResumeScreeningClient
from models import ResumeAction


async def main():
    """Main inference loop with structured output."""
    
    # Task configuration
    TASK_NAME = "resume-screening"
    BENCHMARK = "resume_screening_env"
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
    
    # Print START block - CRITICAL
    print(f"[START] task={TASK_NAME} env={BENCHMARK} model={MODEL_NAME}", flush=True)
    
    rewards = []
    steps_taken = 0
    success = False
    
    try:
        # Connect to environment
        env = ResumeScreeningClient(base_url=SERVER_URL)
        
        # Reset environment
        result = await env.reset()
        observation = result.observation
        
        # Process candidates
        for step in range(1, 11):  # Max 10 steps
            if result.done:
                break
            
            # Simple decision logic based on experience and role
            decision = "hold"  # default
            
            if observation.target_role == "junior":
                if observation.experience_years <= 2:
                    decision = "shortlist"
                elif observation.experience_years > 3:
                    decision = "reject"
                else:
                    decision = "hold"
                    
            elif observation.target_role == "mid":
                if 2 <= observation.experience_years <= 5:
                    decision = "shortlist"
                elif observation.experience_years < 2:
                    decision = "hold"
                else:
                    decision = "reject"
                    
            else:  # senior
                if observation.experience_years >= 5:
                    decision = "shortlist"
                elif observation.experience_years >= 3:
                    decision = "hold"
                else:
                    decision = "reject"
            
            # Execute action
            action = ResumeAction(decision=decision)
            result = await env.step(action)
            
            reward = result.reward if result.reward is not None else 0.0
            done = result.done
            error = None
            
            rewards.append(reward)
            steps_taken = step
            
            # Print STEP block - CRITICAL
            print(f"[STEP] step={step} action={decision} reward={reward:.2f} done={str(done).lower()} error={error}", flush=True)
            
            if not done and result.observation:
                observation = result.observation
            
            if done:
                break
        
        # Calculate score
        total_reward = sum(rewards) if rewards else 0.0
        max_possible = 10.0
        score = min(total_reward / max_possible, 1.0)
        success = score >= 0.7
        
    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        success = False
    
    finally:
        try:
            await env.close()
        except:
            pass
        
        # Print END block - CRITICAL
        rewards_str = ",".join(f"{r:.2f}" for r in rewards)
        print(f"[END] success={str(success).lower()} steps={steps_taken} score={score:.3f} rewards={rewards_str}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
