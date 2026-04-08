"""
Inference script for Resume Screening Environment.
Prints structured output to stdout for validation.
"""

import asyncio
import os
import sys
import textwrap
from typing import List, Optional

sys.stdout.reconfigure(line_buffering=True)

from openai import OpenAI

from simple_client import AsyncSimpleResumeClient as ResumeScreeningClient
from models import ResumeAction, ResumeObservation

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
HF_TOKEN = os.getenv("HF_TOKEN")

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")

TASK_NAME = os.getenv("TASK_NAME", "resume-screening")
BENCHMARK = os.getenv("BENCHMARK", "resume_screening_env")
MAX_STEPS = 10
TEMPERATURE = 0.3
MAX_TOKENS = 200

SUCCESS_SCORE_THRESHOLD = 0.7
MAX_REWARD_PER_STEP = 1.0
MAX_TOTAL_REWARD = MAX_STEPS * MAX_REWARD_PER_STEP

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an expert HR recruiter screening candidates for software engineering roles.
    
    Your task: Evaluate each candidate and decide to SHORTLIST, REJECT, or HOLD.
    
    ROLE REQUIREMENTS:
    - Junior Engineer: 0-2 years experience, basic programming skills, projects matter
    - Mid-level Engineer: 2-5 years experience, strong technical skills, system design exposure
    - Senior Engineer: 5+ years experience, advanced skills (system design, scalability, leadership)
    
    DECISION GUIDELINES:
    - SHORTLIST: Candidate clearly meets or exceeds requirements
    - REJECT: Candidate clearly doesn't meet requirements
    - HOLD: Candidate is borderline or needs further review
    
    Respond with EXACTLY one word: shortlist, reject, or hold.
    No explanations, no punctuation, just the decision.
    """
).strip()


def log_start(task: str, env: str, model: str) -> None:
    """Log the start of an episode - MUST print to stdout."""
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """Log each step of the episode - MUST print to stdout."""
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """Log the end of an episode - MUST print to stdout."""
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


def build_user_prompt(
    step: int,
    candidate_id: str,
    target_role: str,
    education: str,
    experience_years: float,
    skills: List[str],
    projects: List[str],
    certifications: Optional[List[str]],
    gap_years: float,
    last_reward: float,
    history: List[str]
) -> str:
    """Build the user prompt for the LLM."""
    skills_str = ", ".join(skills[:5]) if skills else "None listed"
    projects_str = ", ".join(projects[:3]) if projects else "None listed"
    history_block = "\n".join(history[-4:]) if history else "No previous decisions"
    
    return textwrap.dedent(
        f"""
        Step {step} - Candidate {candidate_id}
        
        Target Role: {target_role.upper()} Engineer
        Education: {education}
        Experience: {experience_years} years
        Skills: {skills_str}
        Projects: {projects_str}
        Career Gap: {gap_years} years
        
        Last reward: {last_reward:.2f}
        
        Previous decisions:
        {history_block}
        
        Decision (shortlist/reject/hold):
        """
    ).strip()


def get_model_decision(
    client: OpenAI,
    step: int,
    observation: ResumeObservation,
    last_reward: float,
    history: List[str]
) -> str:
    """Get decision from the LLM."""
    user_prompt = build_user_prompt(
        step=step,
        candidate_id=observation.candidate_id,
        target_role=observation.target_role,
        education=observation.education,
        experience_years=observation.experience_years,
        skills=observation.skills,
        projects=observation.projects,
        certifications=observation.certifications,
        gap_years=observation.gap_years,
        last_reward=last_reward,
        history=history
    )
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        decision = (completion.choices[0].message.content or "").strip().lower()
        
        if decision not in ["shortlist", "reject", "hold"]:
            decision = "hold"
        
        return decision
    except Exception as exc:
        print(f"[DEBUG] Model error: {exc}", flush=True)
        return "hold"


async def main() -> None:
    """Main inference loop."""
    
    if not HF_TOKEN or HF_TOKEN == "dummy":
        print("[WARNING] HF_TOKEN not set. Using mock decisions for testing.", flush=True)
    
    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=HF_TOKEN or "dummy"
    )
    
    print(f"[INFO] Connecting to server at: {SERVER_URL}", flush=True)
    
    try:
        env = ResumeScreeningClient(base_url=SERVER_URL)
        result = await env.reset()
        print(f"[INFO] Connected successfully!", flush=True)
        print(f"[INFO] First candidate: {result.observation.candidate_id}", flush=True)        
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}", flush=True)
        print(f"[INFO] Make sure the server is running on {SERVER_URL}", flush=True)
        return
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)
    
    try:
        observation = result.observation
        last_reward = 0.0
        
        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break
            if HF_TOKEN and HF_TOKEN != "dummy":
                decision = get_model_decision(
                    client, step, observation, last_reward, history
                )
            else:
                mock_decisions = ["shortlist", "reject", "shortlist", "hold"]
                decision = mock_decisions[(step - 1) % len(mock_decisions)]
                print(f"[INFO] Mock decision: {decision}", flush=True)
            
            action = ResumeAction(decision=decision)
            result = await env.step(action)
            
            reward = result.reward if result.reward is not None else 0.0
            done = result.done
            
            rewards.append(reward)
            steps_taken = step
            last_reward = reward
            log_step(
                step=step,
                action=decision,
                reward=reward,
                done=done,
                error=None
            )
            
            history.append(f"Step {step}: {decision} -> reward {reward:+.2f}")
            
            if not done and result.observation:
                observation = result.observation
            
            if done:
                break
        total_reward = sum(rewards) if rewards else 0.0
        max_possible_reward = MAX_STEPS * MAX_REWARD_PER_STEP
        score = total_reward / max_possible_reward if max_possible_reward > 0 else 0.0
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD
        
    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        success = False
        
    finally:
        try:
            await env.close()
        except:
            pass
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    print("="*60, flush=True)
    print("Resume Screening Inference", flush=True)
    print("="*60, flush=True)
    asyncio.run(main())
