FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# копируем весь проект
COPY . .

# создаём папку для базы, если нет
RUN mkdir -p /app/data

ENV BOT_TOKEN=""

CMD ["python", "main.py"]
