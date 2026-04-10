"""Resume Screening Environment Client."""

from typing import Dict, Optional, Literal

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State
from models import ResumeAction, ResumeObservation


class ResumeScreeningClient(
    EnvClient[ResumeAction, ResumeObservation, State]
):
    """
    Client for the Resume Screening Environment.

    This client maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.
    Each client instance has its own dedicated environment session on the server.

    The environment simulates a real-world resume screening system where the agent
    evaluates candidates for different job roles (Junior, Mid, Senior Engineer).

    Example:
        >>> # Connect to a running server
        >>> with ResumeScreeningClient(base_url="http://localhost:8000") as client:
        ...     result = client.reset()
        ...     print(f"Candidate: {result.observation.candidate_id}")
        ...     print(f"Role: {result.observation.target_role}")
        ...     print(f"Experience: {result.observation.experience_years} years")
        ...
        ...     # Make a decision
        ...     result = client.step(ResumeAction(decision="shortlist"))
        ...     print(f"Reward: {result.reward}")

    Example with different difficulty:
        >>> # Create client with medium difficulty
        >>> client = ResumeScreeningClient.from_docker_image(
        ...     "resume-screening-env:latest",
        ...     env_kwargs={"difficulty": "medium"}
        ... )
        >>> try:
        ...     result = client.reset()
        ...     # Process candidates...
        ... finally:
        ...     client.close()

    Example with manual server:
        >>> # Start server first: uvicorn server.app:app --port 8000
        >>> client = ResumeScreeningClient(base_url="http://localhost:8000")
        >>> result = client.reset()
        >>> print(f"First candidate: {result.observation.candidate_id}")
    """

    def _step_payload(self, action: ResumeAction) -> Dict:
        """
        Convert ResumeAction to JSON payload for step message.

        Args:
            action: ResumeAction instance with screening decision

        Returns:
            Dictionary representation suitable for JSON encoding
        """
        return {
            "decision": action.decision,  
        }

    def _parse_result(self, payload: Dict) -> StepResult[ResumeObservation]:
        """
        Parse server response into StepResult[ResumeObservation].

        Args:
            payload: JSON response data from server

        Returns:
            StepResult with ResumeObservation
        """
        obs_data = payload.get("observation", {})
        
        observation = ResumeObservation(
            candidate_id=obs_data.get("candidate_id", ""),
            target_role=obs_data.get("target_role", "junior"),
            education=obs_data.get("education", ""),
            experience_years=obs_data.get("experience_years", 0.0),
            skills=obs_data.get("skills", []),
            projects=obs_data.get("projects", []),
            certifications=obs_data.get("certifications"),
            gap_years=obs_data.get("gap_years", 0.0),
            ground_truth_decision=obs_data.get("ground_truth_decision"),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
    def get_current_candidate_info(self) -> Dict:
        """
        Get information about the current candidate being evaluated.
        
        Returns:
            Dictionary with candidate information
        """
        if not self._current_observation:
            return {"error": "No current observation. Call reset() first."}
        
        obs = self._current_observation
        return {
            "candidate_id": obs.candidate_id,
            "target_role": obs.target_role,
            "experience_years": obs.experience_years,
            "skills_count": len(obs.skills),
            "projects_count": len(obs.projects),
            "gap_years": obs.gap_years,
        }

    def shortlist(self) -> StepResult[ResumeObservation]:
        """
        Convenience method to shortlist the current candidate.
        
        Returns:
            StepResult with the next observation
        """
        return self.step(ResumeAction(decision="shortlist"))
    
    def reject(self) -> StepResult[ResumeObservation]:
        """
        Convenience method to reject the current candidate.
        
        Returns:
            StepResult with the next observation
        """
        return self.step(ResumeAction(decision="reject"))
    
    def hold(self) -> StepResult[ResumeObservation]:
        """
        Convenience method to put the current candidate on hold.
        
        Returns:
            StepResult with the next observation
        """
        return self.step(ResumeAction(decision="hold"))


class SimpleResumeScreeningClient(ResumeScreeningClient):
    """
    Simplified client for the Resume Screening Environment with helper methods.
    
    This extends the base client with additional convenience methods for
    common operations like batch processing and statistics tracking.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the client with tracking variables."""
        super().__init__(*args, **kwargs)
        self.decision_history = []
        self.total_reward = 0.0
    
    def reset_with_tracking(self):
        """Reset environment and clear tracking variables."""
        self.decision_history = []
        self.total_reward = 0.0
        return self.reset()
    
    def step_with_tracking(self, action: ResumeAction) -> StepResult[ResumeObservation]:
    # Capture BEFORE stepping
    current_candidate_id = (
        self._current_observation.candidate_id 
        if self._current_observation else "unknown"
    )
    current_ground_truth = (
        self._current_observation.ground_truth_decision
        if self._current_observation else None
    )
    
    result = self.step(action)
    
    self.decision_history.append({
        "candidate_id": current_candidate_id,  
        "decision": action.decision,
        "reward": result.reward,
        "ground_truth": current_ground_truth,    
    })
    
    if result.reward is not None:
        self.total_reward += result.reward
    
    return result
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the screening session.
        
        Returns:
            Dictionary with statistics
        """
        if not self.decision_history:
            return {"error": "No decisions made yet"}
        
        total_decisions = len(self.decision_history)
        correct_decisions = sum(
            1 for d in self.decision_history 
            if d.get("ground_truth") and d["decision"] == d["ground_truth"]
        )
        
        return {
            "total_decisions": total_decisions,
            "correct_decisions": correct_decisions,
            "accuracy": correct_decisions / total_decisions if total_decisions > 0 else 0.0,
            "total_reward": self.total_reward,
            "average_reward": self.total_reward / total_decisions if total_decisions > 0 else 0.0,
            "decisions_by_type": {
                "shortlist": sum(1 for d in self.decision_history if d["decision"] == "shortlist"),
                "reject": sum(1 for d in self.decision_history if d["decision"] == "reject"),
                "hold": sum(1 for d in self.decision_history if d["decision"] == "hold"),
            }
        }
