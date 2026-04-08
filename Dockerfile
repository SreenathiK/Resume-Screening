FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user

WORKDIR /home/user/app

RUN pip install --no-cache-dir \
    openenv-core[core] \
    fastapi \
    uvicorn \
    pydantic \
    groq \
    openai \
    requests

COPY --chown=user . .

ENV PYTHONPATH="/home/user/app:$PYTHONPATH"
ENV RESUME_DIFFICULTY="easy"

EXPOSE 7860

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]