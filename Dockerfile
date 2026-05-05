FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system swiftdeploy && adduser --system --ingroup swiftdeploy swiftdeploy

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

USER swiftdeploy

EXPOSE 3000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${APP_PORT:-3000}"]
