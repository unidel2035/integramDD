# Используем минимальный Python-образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app


COPY ./requirements.txt* ./

# Устанавливаем зависимости
RUN pip install --upgrade pip \
    && (test -f requirements.txt && pip install -r requirements.txt)

# Копируем весь исходный код
COPY . .

# Открываем порт
EXPOSE 8000

# Команда запуска без --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
