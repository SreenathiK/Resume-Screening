from setuptools import setup

setup(
    name="resume-screening",
    version="1.0.0",
    description="Resume Screening Environment for AI agents",
    author="SreenathiK",
    install_requires=[
        "openai>=1.0.0",
        "requests>=2.31.0",
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.0.0",
        "httpx>=0.27.0",
    ],
)
