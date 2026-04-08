"""
Resume Screening Environment Implementation.

Simulates a real-world resume screening system where AI agents evaluate candidates
for different job roles and make hiring decisions.
"""

from uuid import uuid4
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

try:
    from openenv.core.env_server.interfaces import Environment
except ImportError:
    Environment = object  # Dummy fallback
from openenv.core.env_server.types import State

try:
    from ..models import ResumeAction, ResumeObservation
except ImportError:
    from models import ResumeAction, ResumeObservation


class TaskDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ResumeScreeningEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS: bool = True
    
    def __init__(self, difficulty: TaskDifficulty = TaskDifficulty.EASY):
        self.difficulty = difficulty
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._current_candidate_idx = 0
        self._dataset = self._generate_dataset()
        self._action_history = []
        self._score = 0.0
        
    def _generate_dataset(self) -> List[Dict[str, Any]]:
        if self.difficulty == TaskDifficulty.EASY:
            return self._generate_easy_dataset()
        elif self.difficulty == TaskDifficulty.MEDIUM:
            return self._generate_medium_dataset()
        else:
            return self._generate_hard_dataset()
    
    def _generate_easy_dataset(self) -> List[Dict[str, Any]]:
        """Generate easy difficulty dataset with clear matches/non-matches."""
        return [            
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
                "skills": ["Python", "Java", "AWS", "Docker", "Kubernetes"],
                "projects": ["Large-scale distributed system", "Microservices architecture"],
                "certifications": ["AWS Certified"],
                "gap_years": 0.0,
                "ground_truth": "reject"
            },
            {
                "candidate_id": "MID_001",
                "target_role": "mid",
                "education": "BS Software Engineering",
                "experience_years": 3.5,
                "skills": ["Python", "JavaScript", "React", "Node.js", "MongoDB"],
                "projects": ["Real-time chat application", "API gateway"],
                "certifications": ["Scrum Master"],
                "gap_years": 0.0,
                "ground_truth": "shortlist"
            },
            {
                "candidate_id": "MID_002",
                "target_role": "mid",
                "education": "Bootcamp Graduate",
                "experience_years": 1.8,
                "skills": ["Python", "Flask", "SQL"],
                "projects": ["Blog platform", "Weather app"],
                "certifications": None,
                "gap_years": 0.5,
                "ground_truth": "hold"
            },
            {
                "candidate_id": "SENIOR_001",
                "target_role": "senior",
                "education": "MS Computer Science",
                "experience_years": 7.0,
                "skills": ["Python", "Java", "System Design", "AWS", "Leadership", "Kafka"],
                "projects": ["Led team of 5 for payment system", "Architected data pipeline"],
                "certifications": ["AWS Solutions Architect"],
                "gap_years": 0.0,
                "ground_truth": "shortlist"
            },
            {
                "candidate_id": "SENIOR_002",
                "target_role": "senior",
                "education": "BS Computer Science",
                "experience_years": 2.0,
                "skills": ["Python", "Django", "PostgreSQL"],
                "projects": ["CRUD application"],
                "certifications": None,
                "gap_years": 0.0,
                "ground_truth": "reject"
            }
        ]
    
    def _generate_medium_dataset(self) -> List[Dict[str, Any]]:
        return [
            {
                "candidate_id": "JUNIOR_003",
                "target_role": "junior",
                "education": "Self-taught",
                "experience_years": 0.5,
                "skills": ["Python", "HTML/CSS", "JavaScript"],
                "projects": ["Personal portfolio", "Todo app", "Calculator"],
                "certifications": None,
                "gap_years": 0.0,
                "ground_truth": "hold"
            },
            {
                "candidate_id": "MID_003",
                "target_role": "mid",
                "education": "BS Computer Science",
                "experience_years": 2.2,
                "skills": ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL"],
                "projects": ["Open source contributor (3 PRs)", "Built CI/CD pipeline"],
                "certifications": ["Google IT Automation"],
                "gap_years": 0.0,
                "ground_truth": "shortlist"
            },
            {
                "candidate_id": "SENIOR_003",
                "target_role": "senior",
                "education": "PhD Computer Science",
                "experience_years": 6.5,
                "skills": ["Python", "Research", "Machine Learning", "Pandas"],
                "projects": ["Published 5 papers", "Built ML models"],
                "certifications": None,
                "gap_years": 1.0,
                "ground_truth": "hold"
            }
        ]
    
    def _generate_hard_dataset(self) -> List[Dict[str, Any]]:
        return [
            {
                "candidate_id": "JUNIOR_004",
                "target_role": "junior",
                "education": "BS Comuter Scence",  
                "experience_years": 1.0,
                "skills": ["pythn", "javva", "gti", "sqlite"],
                "projects": ["projct1", "projct2"],
                "certifications": None,
                "gap_years": 1.5,
                "ground_truth": "hold"  
            },
            {
                "candidate_id": "MID_004",
                "target_role": "mid",
                "education": "", 
                "experience_years": 0.0,  
                "skills": ["JavaScript", "React"],
                "projects": [],  
                "certifications": None,
                "gap_years": 3.0,
                "ground_truth": "reject"
            },
            {
                "candidate_id": "SENIOR_004",
                "target_role": "senior",
                "education": "Some College",  
                "experience_years": 9.0,
                "skills": ["python", "leadrship", "scalablity"],  
                "projects": ["Did stuff", "Worked on things"],  
                "certifications": ["Unknown cert"],
                "gap_years": 2.5,
                "ground_truth": "hold"
            }
        ]
    
    def _compute_ground_truth(self, candidate: Dict[str, Any]) -> str:
        role = candidate["target_role"]
        experience = candidate["experience_years"]
        skills = candidate["skills"]
        projects = candidate["projects"]
        gap_years = candidate["gap_years"]
        if self.difficulty == TaskDifficulty.HARD:
            has_missing_info = (
                not candidate["education"] or 
                len(skills) < 2 or 
                len(projects) == 0
            )
            if has_missing_info:
                return "hold"
        if role == "junior":
            if 0 <= experience <= 2 and len(projects) >= 1:
                if gap_years <= 1.0:
                    return "shortlist"
                else:
                    return "hold"
            elif experience > 3:
                return "reject"
            else:
                return "hold"
                
        elif role == "mid":
            if 2 <= experience <= 5 and len(skills) >= 3:
                has_system_design = any(
                    skill.lower() in ["system design", "architecture", "scalability"]
                    for skill in skills
                )
                if has_system_design or experience >= 3:
                    return "shortlist"
                else:
                    return "hold"
            elif experience < 2:
                return "hold"
            else:
                return "reject"
                
        else:  
            if experience >= 5 and len(skills) >= 4:
                advanced_skills = ["system design", "scalability", "leadership", "architecture"]
                has_advanced = any(
                    any(adv in skill.lower() for adv in advanced_skills)
                    for skill in skills
                )
                if has_advanced and len(projects) >= 2:
                    return "shortlist"
                elif experience >= 7:
                    return "hold"
                else:
                    return "reject"
            elif 3 <= experience < 5:
                return "hold"
            else:
                return "reject"
    
    def _calculate_reward(
        self, 
        action: ResumeAction, 
        ground_truth: str,
        candidate: Dict[str, Any]
    ) -> float:
        
        decision = action.decision
        if self._action_history and self._action_history[-1].get("candidate_id") == candidate["candidate_id"]:
            return -0.1
        if decision == ground_truth:
            if decision == "shortlist" or decision == "reject":
                return 1.0
            elif decision == "hold":
                return 0.3
        else:
            if ground_truth in ["shortlist", "reject"] and decision == "hold":
                return -0.2
            else:
                return -0.5
        
        return 0.0
    
    def reset(self) -> ResumeObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._current_candidate_idx = 0
        self._action_history = []
        self._score = 0.0
        return self._get_current_observation()
    
    def step(self, action: ResumeAction) -> ResumeObservation:  
        if self._current_candidate_idx >= len(self._dataset):
            return ResumeObservation(
                candidate_id="",
                target_role="junior",
                education="",
                experience_years=0.0,
                skills=[],
                projects=[],
                certifications=None,
                gap_years=0.0,
                done=True,
                reward=self._score / max(len(self._dataset), 1),
                metadata={"total_score": self._score, "total_candidates": len(self._dataset)}
            )
        candidate = self._dataset[self._current_candidate_idx]
        ground_truth = candidate["ground_truth"]
        reward = self._calculate_reward(action, ground_truth, candidate)
        self._score += reward
        self._action_history.append({
            "candidate_id": candidate["candidate_id"],
            "decision": action.decision,
            "ground_truth": ground_truth,
            "reward": reward,
            "step": self._state.step_count
        })
        self._current_candidate_idx += 1
        self._state.step_count += 1
        done = self._current_candidate_idx >= len(self._dataset)
        if done:
            observation = ResumeObservation(
                candidate_id="",
                target_role="junior",
                education="",
                experience_years=0.0,
                skills=[],
                projects=[],
                certifications=None,
                gap_years=0.0,
                done=True,
                reward=reward,
                metadata={
                    "final_score": self._score,
                    "accuracy": self._score / len(self._dataset),
                    "total_candidates": len(self._dataset),
                    "action_history": self._action_history
                }
            )
        else:
            observation = self._get_current_observation()
            observation.reward = reward
        
        return observation
    
    def _get_current_observation(self) -> ResumeObservation:
        if self._current_candidate_idx >= len(self._dataset):
            return ResumeObservation(
                candidate_id="",
                target_role="junior",
                education="",
                experience_years=0.0,
                skills=[],
                projects=[],
                certifications=None,
                gap_years=0.0,
                done=True,
                reward=0.0
            )
        
        candidate = self._dataset[self._current_candidate_idx]
        
        # For hard difficulty, add noise to observations (typos already in data)
        return ResumeObservation(
            candidate_id=candidate["candidate_id"],
            target_role=candidate["target_role"],
            education=candidate["education"],
            experience_years=candidate["experience_years"],
            skills=candidate["skills"],
            projects=candidate["projects"],
            certifications=candidate.get("certifications"),
            gap_years=candidate["gap_years"],
            ground_truth_decision=candidate["ground_truth"] if self.difficulty == TaskDifficulty.EASY else None,
            done=False,
            reward=0.0
        )
    
    @property
    def state(self) -> State:
        return self._state
    
    def get_grader_score(self) -> float:
        """
        Get the deterministic grader score for the current episode.
        
        Returns:
            Score between 0.0 and 1.0 based on decision accuracy
        """
        if not self._action_history or len(self._dataset) == 0:
            return 0.0
        
        correct_decisions = sum(
            1 for action in self._action_history 
            if action["decision"] == action["ground_truth"]
        )
        
        return correct_decisions / len(self._action_history)
    
    def get_dataset(self) -> List[Dict[str, Any]]:
        return self._dataset
