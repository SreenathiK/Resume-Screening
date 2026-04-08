# server/my_env_environment.py - No openenv dependency

from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import uuid

class TaskDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

@dataclass
class State:
    episode_id: str
    step_count: int

class ResumeScreeningEnvironment:
    """Resume screening environment without openenv dependency."""
    
    def __init__(self, difficulty: TaskDifficulty = TaskDifficulty.EASY):
        self.difficulty = difficulty
        self._state = State(episode_id=str(uuid.uuid4()), step_count=0)
        self._reset_count = 0
        self._current_candidate_idx = 0
        self._score = 0.0
        self._action_history = []
        
        # Sample candidates
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
    
    def reset(self):
        """Reset the environment."""
        self._state = State(episode_id=str(uuid.uuid4()), step_count=0)
        self._current_candidate_idx = 0
        self._score = 0.0
        self._action_history = []
        return self._get_observation()
    
    def step(self, action):
        """Execute a step."""
        from models import ResumeObservation
        
        self._state.step_count += 1
        
        if self._current_candidate_idx >= len(self.candidates):
            return self._get_observation(done=True)
        
        candidate = self.candidates[self._current_candidate_idx]
        ground_truth = candidate.get("ground_truth", "shortlist")
        
        # Calculate reward
        if action.decision == ground_truth:
            reward = 1.0
        elif action.decision == "hold":
            reward = 0.3
        else:
            reward = -0.5
        
        self._score += reward
        
        self._action_history.append({
            "candidate_id": candidate["candidate_id"],
            "decision": action.decision,
            "ground_truth": ground_truth,
            "reward": reward
        })
        
        self._current_candidate_idx += 1
        done = self._current_candidate_idx >= len(self.candidates)
        
        observation = self._get_observation(done=done)
        observation.reward = reward
        
        # Return a result object
        class Result:
            def __init__(self, observation, reward, done):
                self.observation = observation
                self.reward = reward
                self.done = done
        
        return Result(observation, reward, done)
    
    def _get_observation(self, done=False):
        """Get current observation."""
        from models import ResumeObservation
        
        if done or self._current_candidate_idx >= len(self.candidates):
            return ResumeObservation(
                candidate_id="",
                target_role="",
                education="",
                experience_years=0.0,
                skills=[],
                projects=[],
                done=True,
                reward=self._score
            )
        
        c = self.candidates[self._current_candidate_idx]
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
        return self._state
