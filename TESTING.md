# Руководство по тестированию IntegramDD

## Содержание
- [Стратегия тестирования](#стратегия-тестирования)
- [Запуск тестов](#запуск-тестов)
- [Написание новых тестов](#написание-новых-тестов)
- [Покрытие кода](#покрытие-кода)
- [Тестирование API](#тестирование-api)
- [Моки и стабы](#моки-и-стабы)
- [Тестирование с базой данных](#тестирование-с-базой-данных)
- [CI/CD для тестов](#cicd-для-тестов)
- [Performance Testing](#performance-testing)
- [Примеры тестовых сценариев](#примеры-тестовых-сценариев)

---

## Стратегия тестирования

### Уровни тестирования

Проект использует многоуровневый подход к тестированию:

#### 1. Unit Tests (Модульные тесты)
- Тестируют отдельные функции и классы в изоляции
- Используют моки для внешних зависимостей (БД, внешние сервисы)
- Быстрые и надежные
- Примеры: `tests/api/video/test_service.py`

#### 2. Integration Tests (Интеграционные тесты)
- Тестируют взаимодействие между компонентами
- Используют реальный сервер приложения
- Могут требовать запущенной БД
- Примеры: `tests/test_object_api.py`, `tests/test_term_api.py`

#### 3. E2E Tests (End-to-End тесты)
- Тестируют полный пользовательский сценарий
- Требуют запущенного сервера на `http://localhost:8000`
- Отмечены декоратором `@pytest.mark.parametrize` с реальными данными
- Примеры: `test_post_object_real_server`, `test_create_term_real_server`

### Технологический стек

- **Фреймворк**: [pytest](https://docs.pytest.org/) 8.3.5
- **Async поддержка**: [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) 0.26.0
- **HTTP клиент**: [httpx](https://www.python-httpx.org/) 0.28.1
- **Моки**: `unittest.mock` (стандартная библиотека)
- **Тестовый клиент**: FastAPI `TestClient` и `AsyncClient`

---

## Запуск тестов

### Установка зависимостей

```bash
pip install -r app/requirements.txt
```

Основные тестовые зависимости:
- `pytest==8.3.5`
- `pytest-asyncio==0.26.0`
- `httpx==0.28.1`

### Базовые команды

#### Запуск всех тестов

```bash
pytest
```

#### Запуск конкретного файла

```bash
pytest tests/test_object_api.py
```

#### Запуск конкретного теста

```bash
pytest tests/test_object_api.py::test_post_object_mocked
```

#### Запуск тестов с подробным выводом

```bash
pytest -v
```

#### Запуск тестов с выводом print-statement'ов

```bash
pytest -s
```

#### Запуск только unit тестов (с моками)

```bash
pytest -k "mocked"
```

#### Запуск только интеграционных тестов (требуют live server)

```bash
# Сначала запустите сервер
docker compose up --build

# В другом терминале
pytest -k "real_server"
```

### Параметры запуска

| Параметр | Описание |
|----------|----------|
| `-v, --verbose` | Подробный вывод |
| `-s` | Показывать print statements |
| `-x` | Остановить после первой ошибки |
| `--tb=short` | Короткий traceback |
| `--tb=long` | Полный traceback |
| `-k EXPRESSION` | Запустить тесты, соответствующие выражению |
| `-m MARKER` | Запустить тесты с определенным маркером |
| `--collect-only` | Показать список тестов без запуска |
| `--lf` | Запустить только failed тесты |
| `--ff` | Сначала failed, потом остальные |

---

## Написание новых тестов

### Структура тестов

Тесты располагаются в директории `tests/` и повторяют структуру `app/`:

```
tests/
├── api/
│   └── video/
│       ├── __init__.py
│       ├── test_routes.py
│       └── test_service.py
├── test_object_api.py
└── test_term_api.py
```

### Базовый шаблон unit теста

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.api import your_module


@pytest.fixture
def auth_headers():
    """Фикстура для заголовков авторизации"""
    return {"Authorization": "Bearer secret-token"}


@pytest.mark.asyncio
async def test_your_endpoint(monkeypatch, auth_headers):
    """Описание теста"""
    # 1. Mock авторизации
    monkeypatch.setattr(
        your_module,
        "verify_token",
        AsyncMock(return_value={"user_id": 1, "role": "admin"})
    )

    # 2. Mock БД
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (123, "test_data")

    mock_conn = AsyncMock()
    mock_conn.__aenter__.return_value.execute.return_value = mock_result

    mock_engine = MagicMock()
    mock_engine.begin.return_value = mock_conn

    monkeypatch.setattr(your_module, "engine", mock_engine)

    # 3. Выполнение запроса
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/your-endpoint", headers=auth_headers)

    # 4. Проверки
    assert response.status_code == 200
    assert response.json()["id"] == 123
```

### Базовый шаблон интеграционного теста

```python
import pytest
from httpx import post as httpx_post


@pytest.mark.parametrize("payload", [
    {"field1": "value1", "field2": 123},
    {"field1": "value2", "field2": 456},
])
def test_endpoint_integration(payload):
    """Интеграционный тест (требует live server на localhost:8000)"""
    response = httpx_post(
        "http://localhost:8000/your-endpoint",
        headers={"Authorization": "Bearer secret-token"},
        json=payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["field1"] == payload["field1"]
```

### Тестирование синхронных эндпоинтов

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_sync_endpoint():
    """Тест для синхронного эндпоинта"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

---

## Покрытие кода

### Установка pytest-cov

```bash
pip install pytest-cov
```

### Запуск с измерением покрытия

```bash
# Базовый отчет в терминале
pytest --cov=app tests/

# Подробный отчет с пропущенными строками
pytest --cov=app --cov-report=term-missing tests/

# HTML отчет
pytest --cov=app --cov-report=html tests/
# Откройте htmlcov/index.html в браузере

# XML отчет (для CI)
pytest --cov=app --cov-report=xml tests/
```

### Конфигурация покрытия

Создайте файл `.coveragerc`:

```ini
[run]
source = app
omit =
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

### Минимальный порог покрытия

```bash
pytest --cov=app --cov-fail-under=80 tests/
```

---

## Тестирование API

### Fixtures для аутентификации

Проект использует Bearer token аутентификацию:

```python
@pytest.fixture
def auth_headers():
    """Возвращает заголовки авторизации для тестов"""
    return {"Authorization": "Bearer secret-token"}
```

Токен по умолчанию: `secret-token`

### Тестирование POST запросов

```python
@pytest.mark.asyncio
async def test_create_object(monkeypatch, auth_headers):
    # Setup mocks...

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "id": 110,
            "up": 1,
            "attrs": {"t110": "Test Name"}
        }
        response = await client.post(
            "/object",
            headers=auth_headers,
            json=payload
        )

    assert response.status_code == 200
    data = response.json()
    assert data["val"] == "Test Name"
```

### Тестирование GET запросов

```python
@pytest.mark.asyncio
async def test_get_term_by_id(monkeypatch, auth_headers):
    # Setup mocks...

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/term/64", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == 64
```

### Тестирование ошибок

```python
@pytest.mark.asyncio
async def test_get_term_not_found(monkeypatch, auth_headers):
    # Mock пустой результат из БД
    monkeypatch.setattr(terms, "engine", setup_engine_mock([]))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/term/999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Term 999 not found"
```

### Параметризованные тесты

```python
@pytest.mark.parametrize("payload,expected_status", [
    ({"val": "Valid", "t": 3, "mods": {}}, 200),
    ({"val": "Test'123", "t": 3, "mods": {"UNIQUE": ""}}, 200),
    ({"val": "Another", "t": 3, "mods": {"ALIAS": "alias"}}, 200),
])
def test_create_term_variations(payload, expected_status):
    response = httpx_post(
        "http://localhost:8000/term",
        headers={"Authorization": "Bearer secret-token"},
        json=payload
    )
    assert response.status_code == expected_status
```

---

## Моки и стабы

### Mocking авторизации

```python
from unittest.mock import AsyncMock

monkeypatch.setattr(
    your_module,
    "verify_token",
    AsyncMock(return_value={"user_id": 1, "role": "admin"})
)
```

### Mocking SQLAlchemy engine (BEGIN transaction)

Для операций INSERT/UPDATE/DELETE:

```python
from unittest.mock import AsyncMock, MagicMock

mock_result = MagicMock()
mock_result.fetchone.return_value = (123, "returned_value")

mock_conn = AsyncMock()
mock_conn.__aenter__.return_value.execute.return_value = mock_result

mock_engine = MagicMock()
mock_engine.begin.return_value = mock_conn

monkeypatch.setattr(your_module, "engine", mock_engine)
```

### Mocking SQLAlchemy engine (SELECT queries)

Для операций SELECT:

```python
def setup_engine_mock(return_value):
    """Создает мок SQLAlchemy engine с предопределенным результатом запроса.

    Args:
        return_value: Список словарей для возврата из запроса.

    Returns:
        MagicMock instance, эмулирующий async SQLAlchemy engine.
    """
    mock_engine = MagicMock()
    mock_conn = AsyncMock()
    mock_result = MagicMock()

    # Эмулируем цепочку: result.mappings().all() → возврат данных
    mock_result.mappings.return_value.all.return_value = return_value
    mock_conn.__aenter__.return_value.execute.return_value = mock_result
    mock_engine.connect.return_value = mock_conn

    return mock_engine

# Использование
MOCKED_DATA = [{"id": 64, "val": "Test", "t": 3}]
monkeypatch.setattr(your_module, "engine", setup_engine_mock(MOCKED_DATA))
```

### Mocking внешних сервисов

```python
@pytest.fixture
def mock_video_capture(monkeypatch):
    """Mock для cv2.VideoCapture"""
    mock_capture = MagicMock()
    mock_capture.isOpened.return_value = True
    mock_capture.read.return_value = (True, mock_frame_data)

    monkeypatch.setattr("cv2.VideoCapture", lambda x: mock_capture)
    return mock_capture
```

### Использование pytest.fixture

```python
@pytest.fixture
def video_service():
    """Фикстура для видео сервиса"""
    return VideoStreamService()


@pytest.mark.asyncio
async def test_with_fixture(video_service):
    result = await video_service.connect("test_drone", "rtsp://test.url")
    assert result is False
```

---

## Тестирование с базой данных

### Стратегия 1: Моки (рекомендуется для unit тестов)

Используйте моки для изоляции от БД (см. раздел "Моки и стабы").

**Преимущества:**
- Быстрые тесты
- Не требуют реальной БД
- Надежные и предсказуемые

**Недостатки:**
- Не проверяют реальные SQL запросы
- Могут пропустить проблемы с БД

### Стратегия 2: Тестовая БД (для интеграционных тестов)

#### Настройка тестовой БД в Docker

1. Создайте `docker-compose.test.yml`:

```yaml
version: '3.8'

services:
  test-db:
    image: postgres:15
    environment:
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
      POSTGRES_DB: test_integram
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data  # In-memory для скорости
```

2. Запустите тестовую БД:

```bash
docker compose -f docker-compose.test.yml up -d
```

3. Настройте переменные окружения для тестов:

```bash
export DB_HOST=localhost
export DB_PORT=5433
export DB_NAME=test_integram
export DB_USER=test_user
export DB_PASSWORD=test_pass
```

4. Создайте фикстуру для подготовки БД:

```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine():
    """Создает engine для тестовой БД"""
    engine = create_async_engine(
        "postgresql+asyncpg://test_user:test_pass@localhost:5433/test_integram"
    )

    # Инициализация схемы
    async with engine.begin() as conn:
        # Загрузите SQL схему здесь
        pass

    yield engine

    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_db(test_db_engine):
    """Очищает БД после каждого теста"""
    yield

    async with test_db_engine.begin() as conn:
        # Очистка таблиц
        await conn.execute(text("TRUNCATE TABLE your_table CASCADE"))
```

### Стратегия 3: In-memory БД

Для простых случаев можно использовать SQLite in-memory:

```python
@pytest.fixture
async def in_memory_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        # Создайте схему
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()
```

---

## CI/CD для тестов

### Текущая конфигурация

Проект использует GitHub Actions. Файлы конфигурации:
- `.github/workflows/auto-deploy.yml` - автоматический деплой
- `.github/workflows/manual-clean-deploy.yml` - ручной деплой

### Добавление тестов в CI

Создайте `.github/workflows/tests.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
          POSTGRES_DB: test_integram
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r app/requirements.txt
          pip install pytest-cov

      - name: Run tests
        env:
          DB_HOST: localhost
          DB_PORT: 5432
          DB_NAME: test_integram
          DB_USER: test_user
          DB_PASSWORD: test_pass
        run: |
          pytest --cov=app --cov-report=xml --cov-report=term-missing tests/

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
```

### Pre-commit hooks

Создайте `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

Установите:

```bash
pip install pre-commit
pre-commit install
```

### Локальная проверка перед коммитом

```bash
# Запустите все тесты
pytest

# Проверьте покрытие
pytest --cov=app --cov-fail-under=70 tests/

# Линтинг (если используется)
ruff check app/ tests/
```

---

## Performance Testing

### Базовый подход

Для performance testing используйте `pytest-benchmark`:

```bash
pip install pytest-benchmark
```

Пример теста:

```python
def test_performance_create_object(benchmark):
    """Тест производительности создания объекта"""

    def create_object():
        response = httpx_post(
            "http://localhost:8000/object",
            headers={"Authorization": "Bearer secret-token"},
            json={"id": 101, "up": 1, "attrs": {"t101": "Test"}}
        )
        return response

    result = benchmark(create_object)
    assert result.status_code == 200
```

Запуск:

```bash
pytest test_performance.py --benchmark-only
```

### Load Testing

Для нагрузочного тестирования рекомендуется использовать:

#### Locust

Создайте `locustfile.py`:

```python
from locust import HttpUser, task, between


class IntegramUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Выполняется при старте каждого пользователя"""
        self.headers = {"Authorization": "Bearer secret-token"}

    @task(3)
    def get_health(self):
        self.client.get("/health")

    @task(1)
    def create_term(self):
        self.client.post(
            "/term",
            headers=self.headers,
            json={"val": "LoadTest", "t": 3, "mods": {}}
        )
```

Запуск:

```bash
pip install locust
locust -f locustfile.py --host=http://localhost:8000
# Откройте http://localhost:8089
```

#### Apache Bench

Простой способ для быстрого теста:

```bash
# 1000 запросов, 10 одновременных
ab -n 1000 -c 10 http://localhost:8000/health
```

### Мониторинг производительности

```python
import time
import pytest


@pytest.fixture(autouse=True)
def log_test_time(request):
    """Логирует время выполнения каждого теста"""
    start = time.time()
    yield
    duration = time.time() - start
    print(f"\n{request.node.name}: {duration:.3f}s")
```

---

## Примеры тестовых сценариев

### Сценарий 1: CRUD для Terms

```python
@pytest.mark.asyncio
async def test_term_crud_scenario(monkeypatch, auth_headers):
    """Полный CRUD сценарий для термов"""

    # 1. CREATE
    monkeypatch.setattr(terms, "verify_token", AsyncMock(return_value={"user_id": 1, "role": "admin"}))

    # Mock для создания
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (100, "1")
    mock_conn = AsyncMock()
    mock_conn.__aenter__.return_value.execute.return_value = mock_result
    mock_engine = MagicMock()
    mock_engine.begin.return_value = mock_conn
    monkeypatch.setattr(terms, "engine", mock_engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Создание
        create_response = await client.post(
            "/term",
            headers=auth_headers,
            json={"val": "Test Term", "t": 3, "mods": {}}
        )
        assert create_response.status_code == 200
        term_id = create_response.json()["id"]

        # READ
        monkeypatch.setattr(terms, "engine", setup_engine_mock([
            {"id": term_id, "val": "Test Term", "t": 3}
        ]))

        get_response = await client.get(f"/term/{term_id}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["val"] == "Test Term"
```

### Сценарий 2: Авторизация

```python
@pytest.mark.asyncio
async def test_unauthorized_access():
    """Тест доступа без авторизации"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/term")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token():
    """Тест с невалидным токеном"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/term",
            headers={"Authorization": "Bearer invalid-token"}
        )

    assert response.status_code == 401
```

### Сценарий 3: Видео стриминг

```python
@pytest.mark.asyncio
async def test_video_streaming_lifecycle(video_service):
    """Полный lifecycle видео стрима"""
    drone_id = "test_drone_001"

    # 1. Проверка начального состояния
    assert not video_service.is_connected(drone_id)

    # 2. Подключение (с невалидным источником)
    result = await video_service.connect(drone_id, "invalid://source")
    assert result is False

    # 3. Проверка информации о несуществующем стриме
    info = video_service.get_info(drone_id)
    assert info is None

    # 4. Попытка получить фрейм без подключения
    frame = await video_service.get_frame(drone_id)
    assert frame is None

    # 5. Отключение несуществующего стрима
    result = await video_service.disconnect(drone_id)
    assert result is False
```

### Сценарий 4: Обработка ошибок

```python
@pytest.mark.asyncio
async def test_error_handling_scenario(monkeypatch, auth_headers):
    """Тест обработки различных ошибок"""

    # Имитация ошибки БД
    def raise_db_error(*args, **kwargs):
        raise Exception("Database connection failed")

    monkeypatch.setattr(terms, "verify_token", AsyncMock(return_value={"user_id": 1, "role": "admin"}))

    mock_engine = MagicMock()
    mock_engine.connect.side_effect = raise_db_error
    monkeypatch.setattr(terms, "engine", mock_engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/term", headers=auth_headers)

    assert response.status_code == 500
```

### Сценарий 5: Интеграционный тест (требует live server)

```python
def test_full_integration_scenario():
    """Полный интеграционный тест (требует запущенного сервера)"""
    base_url = "http://localhost:8000"
    headers = {"Authorization": "Bearer secret-token"}

    # 1. Проверка health
    health_response = httpx_post(f"{base_url}/health")
    assert health_response.status_code == 200

    # 2. Создание терма
    term_response = httpx_post(
        f"{base_url}/term",
        headers=headers,
        json={"val": "Integration Test", "t": 3, "mods": {}}
    )
    assert term_response.status_code == 200
    term_data = term_response.json()

    # 3. Создание объекта
    object_response = httpx_post(
        f"{base_url}/object",
        headers=headers,
        json={
            "id": 101,
            "up": 1,
            "attrs": {"t101": "Integration Object"}
        }
    )
    assert object_response.status_code == 200
    object_data = object_response.json()

    # 4. Проверка созданных данных
    assert term_data["val"] == "Integration Test"
    assert object_data["val"] == "Integration Object"
```

---

## Лучшие практики

### 1. Именование тестов

- Используйте префикс `test_`
- Описательные имена: `test_get_term_by_id_not_found`
- Включайте ожидаемое поведение в имя

### 2. Структура теста (AAA pattern)

```python
def test_example():
    # Arrange (подготовка)
    data = {"key": "value"}

    # Act (действие)
    result = process_data(data)

    # Assert (проверка)
    assert result["key"] == "value"
```

### 3. Изоляция тестов

- Каждый тест должен быть независимым
- Используйте фикстуры для setup/teardown
- Не полагайтесь на порядок выполнения

### 4. DRY (Don't Repeat Yourself)

- Выносите общий код в фикстуры
- Используйте `@pytest.mark.parametrize` для похожих тестов
- Создавайте helper функции

### 5. Тестируйте edge cases

- Пустые входные данные
- Некорректные типы данных
- Граничные значения
- Несуществующие ID

### 6. Асинхронные тесты

- Всегда используйте `@pytest.mark.asyncio` для async функций
- Используйте `AsyncClient` для async API тестов
- Правильно обрабатывайте async context managers

### 7. Понятные assert сообщения

```python
# Плохо
assert response.status_code == 200

# Хорошо
assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
```

---

## Troubleshooting

### Проблема: тесты не находятся

```bash
# Проверьте, что pytest может найти тесты
pytest --collect-only
```

Убедитесь, что:
- Файлы начинаются с `test_`
- Функции начинаются с `test_`
- В директориях есть `__init__.py`

### Проблема: ошибки импорта

```bash
# Добавьте корневую директорию в PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Проблема: async тесты не работают

Убедитесь, что:
- Установлен `pytest-asyncio`
- Используется декоратор `@pytest.mark.asyncio`
- В pytest.ini или pyproject.toml настроен asyncio mode

Создайте `pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
```

### Проблема: моки не работают

```python
# Проверьте путь для monkeypatch
# Используйте путь к модулю, где функция ИСПОЛЬЗУЕТСЯ, а не где определена

# Неправильно
monkeypatch.setattr("app.auth.auth.verify_token", mock)

# Правильно (если импортирована в app.api.terms)
monkeypatch.setattr("app.api.terms.verify_token", mock)
```

### Проблема: тесты висят

- Проверьте await для async функций
- Убедитесь, что async context managers закрываются
- Используйте timeout: `pytest --timeout=10`

---

## Полезные ссылки

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [HTTPX Documentation](https://www.python-httpx.org/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)

---

## Контакты и поддержка

При возникновении вопросов по тестированию:
1. Проверьте существующие тесты в `tests/`
2. Изучите данное руководство
3. Создайте issue в репозитории проекта

**Версия документа**: 1.0
**Последнее обновление**: 2025-10-15
