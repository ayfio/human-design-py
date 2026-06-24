# Dockerfile
FROM python:3.11-slim

# Системные зависимости для компиляции pyswisseph и geocoding
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    swig \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копируем приложение
COPY chart.py .

# Railway автоматически задаёт PORT через переменную окружения
EXPOSE 8000

# Запуск FastAPI сервера
CMD ["uvicorn", "chart:app", "--host", "0.0.0.0", "--port", "8000"]
