FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home app
COPY backend/ backend/
COPY web/ web/
COPY research/ research/
USER 10001
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "backend.server"]
