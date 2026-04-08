"""
FastAPI application for the Resume Screening Environment.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required. Install with: pip install openenv-core[core]"
    ) from e

try:
    from models import ResumeAction, ResumeObservation
    from server.my_env_environment import ResumeScreeningEnvironment
except ImportError:
    from ..models import ResumeAction, ResumeObservation
    from .my_env_environment import ResumeScreeningEnvironment

app = create_app(
    ResumeScreeningEnvironment,
    ResumeAction,
    ResumeObservation,
    env_name="resume_screening_env",
    max_concurrent_envs=5,
)

def main(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    
    print(f"\n{'='*60}")
    print(f"Resume Screening Environment Server")
    print(f"{'='*60}")
    print(f"Server running at: http://{host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"{'='*60}\n")
    
    uvicorn.run(app, host=host, port=port, reload=False, log_level="info")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
