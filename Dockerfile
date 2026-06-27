FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Системные зависимости для pyswisseph
USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Переключаемся обратно на vscode пользователя
USER vscode

# Рабочая директория
WORKDIR /workspaces/human-design-py

# Устанавливаем Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Порты
EXPOSE 7860 8000

# Команда по умолчанию
CMD ["python", "app_gradio.py"]
