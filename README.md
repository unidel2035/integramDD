# IntegramDD

[![Auto Deploy](https://github.com/unidel2035/integramDD/actions/workflows/auto-deploy.yml/badge.svg)](https://github.com/unidel2035/integramDD/actions/workflows/auto-deploy.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-20.10+-2496ED.svg)](https://www.docker.com/)

## О проекте

### Видение

**Integram** – это фундамент, на котором построится будущее AI-автоматизации бизнеса.

В эпоху, когда искусственный интеллект вытесняет традиционную разработку и даже low-code платформы, возникает критический вопрос: **где всё это будет работать?** Integram даёт ответ – это надёжная, масштабируемая и гибкая платформа нового поколения для корпоративных систем.

### Проблема

**Excel – теневая экономика цифровизации**

73% критически важных операций малого бизнеса до сих пор ведутся в Excel. Это создаёт системные риски:
- **Ошибки ручного ввода** – данные вводятся вручную, без валидации
- **Хаос версий** – файлы разбросаны по почтам и компьютерам
- **Отсутствие аудита** – нет контроля версий и истории изменений
- **Проблемы с правами доступа** – невозможно тонко настроить доступ к данным
- **Нулевая масштабируемость** – то, что работает на 10 строках, рушится на 1000
- **Блокировка AI-внедрения** – разрозненные Excel-файлы невозможно интегрировать с ИИ

Low-code решения (Notion, Airtable) также не решают проблему масштаба:
- Ограничения по количеству записей (например, 50K в Airtable)
- Отсутствие enterprise-уровня RBAC
- Невозможность разграничения доступа на уровне строк и полей

### Решение

**IntegramDD** – это техническая платформа, реализующая видение Integram. Современная система управления данными с гибкой метаданных архитектурой на базе FastAPI и PostgreSQL, которая предоставляет:

#### Ключевые преимущества

1. **Запатентованная технология QDM**
   - Обработка 100+ миллионов записей
   - Поддержка 100+ одновременно работающих пользователей
   - На 40% меньше затрат ресурсов по сравнению с конкурентами

2. **Enterprise-уровень RBAC "из коробки"**
   - Разграничение доступа до уровня поля
   - Гибкая настройка прав для пользователей и ролей
   - Защита конфиденциальных данных

3. **Простота Excel + мощь бэкенда**
   - Знакомый интерфейс – не нужно переучивать пользователей
   - Полноценный масштабируемый бэкенд под капотом
   - Мгновенный переход от Excel к веб-приложению

#### Технические возможности

Система спроектирована для работы с иерархическими данными и поддерживает:
- **Динамическое определение типов объектов** (terms/metadata)
- **Гибкие атрибуты и реквизиты** объектов
- **Иерархические связи** между объектами
- **Расширенные возможности фильтрации** и поиска
- **Видеопотоки** для интеграции с дронами и IoT-устройствами
- **Аутентификацию и авторизацию** на основе токенов
- **RESTful API** для интеграции с внешними системами

## Примеры использования

### Кейс 1: Рекрутинговое агентство

**Проблема**: Тысячи резюме в Excel-файлах, ручное копирование, дубли, невозможность ограничить доступ к конфиденциальным данным (зарплатам).

**Решение**: Единое хранилище кандидатов в Integram с гибкими правами доступа. Каждый рекрутер видит только своих кандидатов, руководители – всю базу. Данные обновляются в реальном времени.

**Результат**:
- Операционная эффективность выросла за счёт отсутствия возни с файлами
- Полная защита от утечек – админ в один клик закрывает доступ уволенному сотруднику
- Нет потерь данных и дублей

### Кейс 2: Производственная компания

**Проблема**: Несколько заводов ежедневно присылают Excel-отчёты о выпуске. Менеджеры вручную сводят таблицы, тратя часы на копипаст.

**Решение**: Данные стекаются в Integram автоматически. Отчёт формируется в два клика, система сама рассылает таблицы нужным людям.

**Результат**:
- Ноль ручной работы, ноль ошибок
- Освободилось несколько часов труда каждый день
- Руководство получает актуальную картину в режиме реального времени

### Кейс 3: E-commerce бизнес

**Проблема**: Владелец 4 виртуальных магазинов управлял всеми процессами через Google Sheets. Масштабирование было невозможно из-за ограничений таблиц.

**Решение**: Переход на веб-приложение на базе Integram.

**Результат**: За год бизнес вырос с 4 до 39 магазинов, сейчас более 70 магазинов.

## Ключевые возможности

- **Гибкая система метаданных**: Динамическое создание и управление типами объектов (terms) с произвольными атрибутами
- **CRUD операции**: Полный набор операций для работы с объектами и метаданными
- **Иерархические данные**: Поддержка древовидных структур с родительско-дочерними связями
- **Расширенная фильтрация**: Гибкие запросы с поддержкой множественных условий фильтрации
- **Видеопотоки**: HTTP MJPEG и WebSocket потоковая передача для интеграции с дронами
- **Хранимые процедуры**: Интеграция с PostgreSQL для сложной бизнес-логики
- **Автоматическая документация API**: Интерактивная документация Swagger UI
- **Аутентификация**: Middleware для защиты эндпоинтов
- **Docker-ready**: Полностью контейнеризованное развертывание
- **CI/CD**: Автоматическое развертывание через GitHub Actions

## Быстрый старт

### Требования к окружению

- **ОС**: Linux / Windows / macOS
- **Docker**: ≥ 20.10.0
- **Docker Compose**: ≥ 1.29.0
- **Свободный порт**: 8000

### Установка и запуск

1. **Клонирование репозитория**
```bash
git clone https://github.com/unidel2035/integramDD.git
cd integramDD
```

2. **Настройка переменных окружения**
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=integram
export DB_USER=postgres
export DB_PASSWORD=postgres
```

3. **Запуск с помощью Docker Compose**
```bash
docker compose up --build
```

Или (старый синтаксис):
```bash
docker-compose up --build
```

4. **Загрузка хранимых процедур**
```bash
cd ./.sql_to_load
./upload_methods.sh -u postgres -p postgres -d integram
cd ..
```

5. **Проверка работоспособности**

Откройте в браузере:
```
http://localhost:8000/docs
```

### Аутентификация

Для тестирования защищенных методов API используйте токен:
```
secret-token
```

В Swagger UI нажмите кнопку "Authorize" и введите токен без префикса "Bearer".

## Примеры использования API

### Создание термина (типа объекта)

```bash
curl -X POST "http://localhost:8000/mydb/terms" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "val": "User",
    "t": 3,
    "mods": {"mods": {}}
  }'
```

### Получение всех метаданных

```bash
curl -X GET "http://localhost:8000/mydb/metadata" \
  -H "Authorization: Bearer secret-token"
```

### Создание объекта

```bash
curl -X POST "http://localhost:8000/mydb/objects" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 32,
    "up": 1,
    "attrs": {
      "t32": "John Doe",
      "t45": "john@example.com"
    }
  }'
```

### Получение объектов определенного типа с фильтрацией

```bash
curl -X GET "http://localhost:8000/mydb/objects/32?up=1&limit=10&offset=0" \
  -H "Authorization: Bearer secret-token"
```

### Подключение к видеопотоку дрона

```bash
curl -X POST "http://localhost:8000/video/connect" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "drone_id": "drone_001",
    "source_url": "rtsp://camera-stream-url"
  }'
```

### Получение видеопотока

HTTP MJPEG:
```
http://localhost:8000/video/stream/drone_001
```

WebSocket:
```
ws://localhost:8000/video/stream/ws/drone_001
```

## Структура API

### Эндпоинты

- **Health Check**: `GET /health` - Проверка работоспособности API
- **Terms (Metadata)**:
  - `GET /{db_name}/terms` - Получить все термины
  - `GET /{db_name}/terms/{term_id}` - Получить термин по ID
  - `POST /{db_name}/terms` - Создать новый термин
  - `PATCH /{db_name}/terms/{term_id}` - Обновить термин
  - `DELETE /{db_name}/terms/{term_id}` - Удалить термин
- **Metadata**:
  - `GET /{db_name}/metadata` - Получить все метаданные
  - `GET /{db_name}/metadata/{term_id}` - Получить метаданные термина
- **Objects**:
  - `GET /{db_name}/object/{object_id}` - Получить объект по ID
  - `GET /{db_name}/objects/{term_id}` - Получить объекты типа
  - `POST /{db_name}/objects` - Создать новый объект
  - `POST /{db_name}/objects/graphql` - GraphQL-подобный запрос объектов
  - `PATCH /{db_name}/objects/{object_id}` - Обновить объект
  - `DELETE /{db_name}/objects/{object_id}` - Удалить объект
- **Requisites**:
  - `GET /{db_name}/requisites/{term_id}` - Получить реквизиты типа
- **References**:
  - `GET /{db_name}/references/{requisite_id}` - Получить справочник реквизита
- **Video Streaming**:
  - `POST /video/connect` - Подключиться к видеоисточнику
  - `POST /video/disconnect/{drone_id}` - Отключиться от видеоисточника
  - `GET /video/info/{drone_id}` - Получить информацию о потоке
  - `GET /video/stream/{drone_id}` - HTTP MJPEG поток
  - `WS /video/stream/ws/{drone_id}` - WebSocket поток

## Архитектура

```
integramDD/
├── app/
│   ├── api/            # API endpoints
│   │   ├── health.py   # Health check endpoint
│   │   ├── terms.py    # Terms/metadata management
│   │   ├── objects.py  # Objects CRUD operations
│   │   ├── requisites.py  # Requisites queries
│   │   ├── references.py  # References queries
│   │   └── video/      # Video streaming module
│   ├── auth/           # Authentication logic
│   ├── db/             # Database connection and utilities
│   ├── middleware/     # Custom middleware (auth)
│   ├── models/         # Pydantic models
│   ├── services/       # Business logic services
│   ├── sql/            # SQL query templates
│   ├── main.py         # FastAPI application entry point
│   ├── logger.py       # Logging configuration
│   ├── settings.py     # Application settings
│   └── requirements.txt # Python dependencies
├── tests/              # Unit and integration tests
├── .sql_to_load/       # Stored procedures to upload
├── docker-compose.yml  # Docker services configuration
├── init-db.sql         # Database initialization script
└── README.md           # This file
```

## Разработка

### Установка зависимостей для разработки

```bash
cd app
pip install -r requirements.txt
```

### Запуск тестов

```bash
pytest tests/
```

### Локальный запуск без Docker

1. Убедитесь, что PostgreSQL запущен и доступен
2. Установите переменные окружения
3. Загрузите SQL схему и хранимые процедуры
4. Запустите приложение:

```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Развертывание

Проект настроен для автоматического развертывания через GitHub Actions. При push в ветку `main` запускается workflow, который:

1. Подключается к серверу по SSH
2. Обновляет код из репозитория
3. Пересобирает Docker образы
4. Перезапускает контейнеры
5. Загружает обновленные SQL процедуры

Для настройки развертывания необходимо добавить следующие secrets в GitHub:
- `SSH_PRIVATE_KEY`
- `SSH_HOST`
- `SSH_USER`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

## Технологии

- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) - современный, быстрый веб-фреймворк для создания API
- **Database**: [PostgreSQL 15](https://www.postgresql.org/) - мощная реляционная СУБД
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) - SQL toolkit и ORM
- **Validation**: [Pydantic 2.11](https://docs.pydantic.dev/) - валидация данных
- **Video Processing**: [OpenCV](https://opencv.org/) - обработка видеопотоков
- **Server**: [Uvicorn](https://www.uvicorn.org/) - ASGI сервер
- **Containerization**: [Docker](https://www.docker.com/) & Docker Compose
- **Testing**: [Pytest](https://pytest.org/) - фреймворк для тестирования
- **CI/CD**: [GitHub Actions](https://github.com/features/actions)

## Вклад в проект

Мы приветствуем вклад в развитие проекта! Если вы хотите помочь:

1. Форкните репозиторий
2. Создайте feature-ветку (`git checkout -b feature/AmazingFeature`)
3. Закоммитьте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Запушьте в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

Пожалуйста, убедитесь, что:
- Ваш код соответствует стилю проекта
- Все тесты проходят
- Документация обновлена при необходимости

## Roadmap

### Ближайшие планы (v0.2.0)
- [ ] **Enterprise RBAC**: Расширенная система прав доступа с разграничением до уровня поля
- [ ] **Excel-импорт**: Автоматический импорт данных из Excel и Google Sheets
- [ ] **Шаблоны приложений**: Готовые шаблоны для типовых бизнес-процессов
- [ ] **Расширенная фильтрация**: GraphQL-подобные запросы для сложных выборок
- [ ] **Кэширование**: Redis для оптимизации производительности

### Среднесрочные планы (v0.3.0)
- [ ] **AI-интеграция**: Автоматическая генерация структуры данных из Excel-файлов с помощью ИИ
- [ ] **Визуальный конструктор**: No-code интерфейс для создания приложений
- [ ] **Система уведомлений**: Email/SMS/Push уведомления о событиях
- [ ] **Интеграции**: Коннекторы к популярным сервисам (1С, SAP, Salesforce)
- [ ] **Мониторинг**: Prometheus, Grafana для отслеживания производительности
- [ ] **Миграции**: Alembic для управления версиями схемы данных

### Долгосрочные планы (v1.0.0)
- [ ] **AI-ассистент**: Интеллектуальный помощник для работы с данными
- [ ] **Мультитенантность**: Поддержка изолированных рабочих пространств
- [ ] **Аналитика и BI**: Встроенные инструменты для анализа и визуализации данных
- [ ] **Мобильные приложения**: Нативные клиенты для iOS и Android
- [ ] **Партнёрская экосистема**: API и инструменты для интеграторов
- [ ] **Масштабирование**: Поддержка кластеризации и горизонтального масштабирования

## FAQ

### Как изменить порт API?

Измените порт в `docker-compose.yml` в секции `backend`:
```yaml
ports:
  - "YOUR_PORT:8000"
```

### Как добавить новую базу данных?

1. Создайте новую таблицу в PostgreSQL с необходимой структурой
2. Загрузите SQL процедуры для новой БД
3. Используйте `{db_name}` в эндпоинтах API

### Как настроить логирование?

Настройки логирования находятся в `app/logger.py`. По умолчанию логи выводятся в stdout с уровнем INFO.

### Поддерживается ли HTTPS?

В production рекомендуется использовать reverse proxy (nginx, Traefik) с SSL/TLS сертификатами перед FastAPI приложением.

### Как масштабировать приложение?

Для масштабирования можно:
1. Увеличить количество workers в Uvicorn
2. Использовать load balancer (nginx, HAProxy)
3. Развернуть несколько инстансов через Docker Swarm или Kubernetes
4. Настроить репликацию PostgreSQL

## Связанные проекты

- [FastAPI](https://github.com/tiangolo/fastapi) - веб-фреймворк, на котором построен проект
- [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) - используемый ORM
- [Pydantic](https://github.com/pydantic/pydantic) - валидация данных

## Лицензия

Информация о лицензии будет добавлена позже.

## Контрибьюторы

Спасибо всем, кто вносит вклад в развитие проекта!

## Поддержка

Если у вас возникли вопросы или проблемы:
- Создайте [Issue](https://github.com/unidel2035/integramDD/issues) в GitHub
- Опишите проблему максимально подробно
- Приложите логи и примеры запросов, если возможно

---

**Создано с использованием FastAPI и PostgreSQL**
