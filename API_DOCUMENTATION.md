# API Documentation - Integram DD

## Содержание
- [Обзор](#обзор)
- [Аутентификация](#аутентификация)
- [Базовый URL](#базовый-url)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Terms (Термины)](#terms-термины)
  - [Objects (Объекты)](#objects-объекты)
  - [Requisites (Реквизиты)](#requisites-реквизиты)
  - [References (Ссылки)](#references-ссылки)
  - [Video Streaming](#video-streaming)
- [Модели данных](#модели-данных)
- [Коды ошибок](#коды-ошибок)
- [Rate Limiting](#rate-limiting)
- [Версионирование](#версионирование)
- [Примеры использования](#примеры-использования)

---

## Обзор

Integram DD API - это RESTful API для управления метаданными, терминами, объектами и их связями. API построен на FastAPI и использует PostgreSQL в качестве базы данных.

**Основные возможности:**
- Управление метаданными и терминами
- CRUD операции с объектами
- Управление реквизитами и ссылками
- Потоковая передача видео для дронов
- Фильтрация и пагинация данных

**Технологический стек:**
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- Pydantic для валидации данных
- OpenCV для обработки видео

---

## Аутентификация

API использует **Bearer Token** аутентификацию через JWT токены.

### Формат токена

```
Authorization: Bearer <token>
```

### Пример для тестирования

Для тестирования используется токен:
```
secret-token
```

### Получение токена

```bash
# Пример запроса
curl -X GET "http://localhost:8000/health" \
  -H "Authorization: Bearer secret-token"
```

### Защищенные эндпоинты

Все эндпоинты, кроме следующих, требуют аутентификации:
- `/health`
- `/docs`
- `/openapi.json`
- `/redoc`

### Коды ошибок аутентификации

| Код | Описание |
|-----|----------|
| 401 | Отсутствует токен или токен невалидный |
| 403 | Токен не прошел проверку |

---

## Базовый URL

```
http://localhost:8000
```

Swagger UI доступен по адресу:
```
http://localhost:8000/docs
```

---

## Endpoints

### Health Check

#### GET `/health`

Проверка состояния сервиса и подключения к базе данных.

**Аутентификация:** Не требуется

**Параметры:** Нет

**Пример запроса:**

```bash
curl -X GET "http://localhost:8000/health"
```

**Пример ответа:**

```json
{
  "status": "ok",
  "db": "connected"
}
```

**Возможные значения:**

| Поле | Значения |
|------|----------|
| status | `ok`, `error` |
| db | `connected`, `unreachable` |

---

### Terms (Термины)

Термины представляют собой метаданные и типы объектов в системе.

#### GET `/{db_name}/terms`

Получить список всех терминов.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |

**Пример запроса:**

```bash
curl -X GET "http://localhost:8000/integram/terms" \
  -H "Authorization: Bearer secret-token"
```

**Пример ответа:**

```json
[
  {
    "id": 32,
    "val": "User",
    "base": 3
  },
  {
    "id": 100,
    "val": "Position",
    "base": 1
  }
]
```

---

#### GET `/{db_name}/terms/{term_id}`

Получить информацию о конкретном термине.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |
| term_id | integer | Да | ID термина (path) |

**Пример запроса:**

```bash
curl -X GET "http://localhost:8000/integram/terms/32" \
  -H "Authorization: Bearer secret-token"
```

**Пример ответа:**

```json
{
  "id": 32,
  "val": "User",
  "base": 3
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Успешно |
| 404 | Термин не найден |
| 500 | Ошибка базы данных |

---

#### GET `/{db_name}/metadata`

Получить метаданные всех терминов с реквизитами.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |

**Пример запроса:**

```bash
curl -X GET "http://localhost:8000/integram/metadata" \
  -H "Authorization: Bearer secret-token"
```

**Пример ответа:**

```json
[
  {
    "id": 32,
    "up": 1,
    "type": 3,
    "val": "User",
    "unique": 0,
    "mods": ["NOT NULL"],
    "reqs": [
      {
        "num": 1,
        "id": "100",
        "val": "Position",
        "type": "string",
        "mods": ["NOT NULL"]
      }
    ]
  }
]
```

---

#### GET `/{db_name}/metadata/{term_id}`

Получить метаданные конкретного термина.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |
| term_id | integer | Да | ID термина (path) |

**Пример запроса:**

```bash
curl -X GET "http://localhost:8000/integram/metadata/32" \
  -H "Authorization: Bearer secret-token"
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Успешно |
| 404 | Термин не найден |

---

#### POST `/{db_name}/terms`

Создать новый термин.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |

**Тело запроса:**

```json
{
  "val": "Employee",
  "t": 3,
  "ALIAS": "Сотрудник",
  "UNIQUE": 1
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| val | string | Да | Название термина |
| t | integer | Да | Базовый тип (ID родительского термина) |
| mods | object | Нет | Модификаторы (ALIAS, UNIQUE и т.д.) |

**Пример запроса:**

```bash
curl -X POST "http://localhost:8000/integram/terms" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "val": "Employee",
    "t": 3,
    "ALIAS": "Сотрудник"
  }'
```

**Пример ответа (успех):**

```json
{
  "id": 150,
  "t": 3,
  "val": "Employee"
}
```

**Пример ответа (с предупреждением):**

```json
{
  "id": 150,
  "t": 3,
  "val": "Employee",
  "warnings": "Term already exists"
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Термин создан или уже существует |
| 422 | Пустое значение (err_empty_val) |
| 500 | Ошибка базы данных |

---

#### PATCH `/{db_name}/terms/{term_id}`

Обновить термин.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |
| term_id | integer | Да | ID термина (path) |

**Тело запроса:**

```json
{
  "val": "Senior Employee",
  "t": 3,
  "NOT NULL": 1
}
```

**Пример запроса:**

```bash
curl -X PATCH "http://localhost:8000/integram/terms/150" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "val": "Senior Employee",
    "t": 3
  }'
```

**Пример ответа (успех):**

```json
{
  "id": 150,
  "t": 3,
  "val": "Senior Employee"
}
```

**Пример ответа (ошибка - имя занято):**

```json
{
  "id": 151,
  "errors": "Term name already exists"
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Успешно обновлено |
| 400 | Имя термина уже существует |
| 500 | Ошибка базы данных |

---

#### DELETE `/{db_name}/terms/{term_id}`

Удалить термин и все его вложенные термины.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |
| term_id | integer | Да | ID термина (path) |

**Пример запроса:**

```bash
curl -X DELETE "http://localhost:8000/integram/terms/150" \
  -H "Authorization: Bearer secret-token"
```

**Пример ответа:**

```json
{
  "id": 150,
  "deleted_count": 5
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Успешно удалено |
| 409 | Термин используется (err_term_is_in_use) |
| 500 | Ошибка базы данных |

---

### Objects (Объекты)

Объекты - это экземпляры терминов с конкретными значениями атрибутов.

#### POST `/{db_name}/objects`

Создать новый объект.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |

**Тело запроса:**

```json
{
  "id": 32,
  "up": 1,
  "attrs": {
    "t32": "John Doe",
    "t100": "Manager"
  }
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| id | integer | Да | ID типа объекта (термина) |
| up | integer | Да | ID родительского объекта (1 для корневых) |
| attrs | object | Да | Атрибуты объекта в формате `t{id}: value` |

**Пример запроса:**

```bash
curl -X POST "http://localhost:8000/integram/objects" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 32,
    "up": 1,
    "attrs": {
      "t32": "John Doe",
      "t100": "Manager"
    }
  }'
```

**Пример ответа:**

```json
{
  "id": 252,
  "up": 1,
  "t": 32,
  "val": "John Doe"
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Объект создан успешно |
| 400 | Некорректный тип или ссылка |
| 404 | Тип не найден |
| 409 | Значение не уникально |
| 422 | Пустое значение |
| 500 | Ошибка базы данных |

---

#### GET `/{db_name}/object/{object_id}`

Получить конкретный объект со всеми его реквизитами.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |
| object_id | integer | Да | ID объекта (path) |

**Пример запроса:**

```bash
curl -X GET "http://localhost:8000/integram/object/252" \
  -H "Authorization: Bearer secret-token"
```

**Пример ответа:**

```json
{
  "id": 252,
  "val": "John Doe",
  "t": 32,
  "up": 1,
  "typ_name": "User",
  "base_typ": 3,
  "reqs": {
    "100": {
      "type": "Position",
      "value": "Manager"
    },
    "307": {
      "type": "Department",
      "value": "359"
    }
  }
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Успешно |
| 404 | Объект не найден |
| 500 | Ошибка базы данных |

---

#### GET `/{db_name}/objects/{term_id}`

Получить все объекты определенного типа (термина) с поддержкой фильтрации и пагинации.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |
| term_id | integer | Да | ID типа объектов (path) |
| up | integer | Нет | ID родительского объекта (по умолчанию: 1) |
| limit | integer | Нет | Ограничение количества результатов (по умолчанию: 20) |
| offset | integer | Нет | Смещение для пагинации (по умолчанию: 0) |

**Фильтры:** Можно передавать динамические фильтры в query параметрах в формате `t{id}=value` или `{field_name}=value`.

**Пример запроса:**

```bash
# Базовый запрос
curl -X GET "http://localhost:8000/integram/objects/32?up=1&limit=10&offset=0" \
  -H "Authorization: Bearer secret-token"

# С фильтрацией
curl -X GET "http://localhost:8000/integram/objects/32?up=1&t100=Manager" \
  -H "Authorization: Bearer secret-token"
```

**Пример ответа:**

```json
{
  "t": 32,
  "name": "User",
  "base": 3,
  "header": [
    {
      "id": 100,
      "t": 100,
      "name": "Position",
      "base": 1,
      "ref": null,
      "is_table_req": false,
      "modifiers": ["NOT NULL"]
    }
  ],
  "objects": [
    {
      "id": 252,
      "up": 1,
      "val": "John Doe",
      "reqs": {
        "100": "Manager"
      }
    },
    {
      "id": 253,
      "up": 1,
      "val": "Jane Smith",
      "reqs": {
        "100": "Developer"
      }
    }
  ]
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Успешно |
| 404 | Термин не найден |
| 500 | Ошибка базы данных |

---

#### POST `/{db_name}/objects/graphql`

Альтернативный POST метод для получения объектов с телом запроса (вместо GET с query параметрами).

**Тело запроса:**

```json
{
  "term_id": 32,
  "up": 1,
  "limit": 10,
  "offset": 0,
  "filters": {
    "t100": "Manager"
  }
}
```

**Пример запроса:**

```bash
curl -X POST "http://localhost:8000/integram/objects/graphql" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "term_id": 32,
    "up": 1,
    "limit": 10,
    "filters": {
      "t100": "Manager"
    }
  }'
```

**Ответ:** Аналогичен GET `/{db_name}/objects/{term_id}`

---

#### PATCH `/{db_name}/objects/{object_id}`

Обновить атрибуты объекта.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |
| object_id | integer | Да | ID объекта (path) |

**Тело запроса:**

```json
{
  "t100": "Senior Manager",
  "t307": "360"
}
```

**Пример запроса:**

```bash
curl -X PATCH "http://localhost:8000/integram/objects/252" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "t100": "Senior Manager"
  }'
```

**Пример ответа:**

```json
{
  "id": 252,
  "val": "Senior Manager"
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Успешно обновлено |
| 400 | Некорректные данные |
| 500 | Ошибка базы данных |

---

#### DELETE `/{db_name}/objects/{object_id}`

Удалить объект и все его вложенные объекты.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |
| object_id | integer | Да | ID объекта (path) |

**Пример запроса:**

```bash
curl -X DELETE "http://localhost:8000/integram/objects/252" \
  -H "Authorization: Bearer secret-token"
```

**Пример ответа:**

```json
{
  "id": 252
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Успешно удалено |
| 400 | Объект является метаданными или на него есть ссылки |
| 404 | Объект не найден |
| 500 | Ошибка базы данных |

---

### Requisites (Реквизиты)

Реквизиты - это атрибуты/поля, добавляемые к терминам.

#### POST `/{db_name}/requisites`

Добавить реквизит к термину.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |

**Тело запроса:**

```json
{
  "id": 32,
  "t": 100,
  "unique": 1,
  "notnull": 1,
  "alias": "Position"
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| id | integer | Да | ID термина, к которому добавляется реквизит |
| t | integer | Да | ID типа реквизита |
| unique | integer | Нет | 1 если значение должно быть уникальным |
| notnull | integer | Нет | 1 если значение обязательное |
| alias | string | Нет | Псевдоним для поля |

**Пример запроса:**

```bash
curl -X POST "http://localhost:8000/integram/requisites" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 32,
    "t": 100,
    "notnull": 1
  }'
```

**Пример ответа:**

```json
{
  "id": 1001
}
```

**Пример ответа (с предупреждением):**

```json
{
  "id": 1001,
  "warnings": "Requisite already exists"
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Реквизит добавлен или уже существует |
| 400 | Некорректные данные |
| 404 | Термин не найден |
| 500 | Ошибка базы данных |

---

### References (Ссылки)

Ссылки создают объекты-указатели на термины.

#### POST `/{db_name}/references`

Создать ссылку на термин.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| db_name | string | Да | Имя базы данных (path) |

**Тело запроса:**

```json
{
  "id": 100
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| id | integer | Да | ID термина для создания ссылки |

**Пример запроса:**

```bash
curl -X POST "http://localhost:8000/integram/references" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 100
  }'
```

**Пример ответа:**

```json
{
  "id": 2001
}
```

**Пример ответа (с предупреждением):**

```json
{
  "id": 2001,
  "warnings": "Reference already exists"
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Ссылка создана или уже существует |
| 400 | Некорректные данные |
| 404 | Термин не найден |
| 500 | Ошибка базы данных |

---

### Video Streaming

API для потоковой передачи видео с дронов.

#### POST `/video/connect`

Подключиться к источнику видео дрона.

**Тело запроса:**

```json
{
  "drone_id": "user_drone_walksnail",
  "source_url": "rtsp://localhost:8554/drone_camera",
  "source_type": "rtsp"
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| drone_id | string | Да | Уникальный идентификатор дрона |
| source_url | string | Да | URL источника видео (RTSP/HTTP) |
| source_type | string | Нет | Тип источника: `rtsp`, `http`, `file` (по умолчанию: `rtsp`) |

**Пример запроса:**

```bash
curl -X POST "http://localhost:8000/video/connect" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "drone_id": "user_drone_walksnail",
    "source_url": "rtsp://localhost:8554/drone_camera",
    "source_type": "rtsp"
  }'
```

**Пример ответа (успех):**

```json
{
  "success": true,
  "drone_id": "user_drone_walksnail",
  "message": "Successfully connected to video source"
}
```

**Пример ответа (ошибка):**

```json
{
  "success": false,
  "drone_id": "user_drone_walksnail",
  "message": "Failed to connect to video source"
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Запрос обработан (проверьте поле `success`) |

---

#### POST `/video/disconnect/{drone_id}`

Отключиться от источника видео.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| drone_id | string | Да | Идентификатор дрона (path) |

**Пример запроса:**

```bash
curl -X POST "http://localhost:8000/video/disconnect/user_drone_walksnail" \
  -H "Authorization: Bearer secret-token"
```

**Пример ответа:**

```json
{
  "success": true,
  "drone_id": "user_drone_walksnail",
  "message": "Successfully disconnected video source"
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Успешно отключено |
| 404 | Дрон не подключен |

---

#### GET `/video/info/{drone_id}`

Получить информацию о видеопотоке дрона.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| drone_id | string | Да | Идентификатор дрона (path) |

**Пример запроса:**

```bash
curl -X GET "http://localhost:8000/video/info/user_drone_walksnail" \
  -H "Authorization: Bearer secret-token"
```

**Пример ответа:**

```json
{
  "drone_id": "user_drone_walksnail",
  "connected": true,
  "resolution": [1920, 1080],
  "fps": 60.0,
  "source_url": "rtsp://localhost:8554/drone_camera",
  "frame_count": 3542
}
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Успешно |
| 404 | Дрон не подключен |

---

#### GET `/video/stream/{drone_id}`

HTTP MJPEG видеопоток.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| drone_id | string | Да | Идентификатор дрона (path) |

**Пример запроса:**

```bash
curl -X GET "http://localhost:8000/video/stream/user_drone_walksnail" \
  -H "Authorization: Bearer secret-token"
```

**Формат ответа:** `multipart/x-mixed-replace; boundary=frame`

**Использование в HTML:**

```html
<img src="http://localhost:8000/video/stream/user_drone_walksnail" />
```

**Коды ответа:**

| Код | Описание |
|-----|----------|
| 200 | Поток доступен |
| 404 | Дрон не подключен |

---

#### WebSocket `/video/stream/ws/{drone_id}`

WebSocket видеопоток для более эффективной передачи.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| drone_id | string | Да | Идентификатор дрона (path) |

**Пример использования (JavaScript):**

```javascript
const ws = new WebSocket('ws://localhost:8000/video/stream/ws/user_drone_walksnail');

ws.onmessage = async (event) => {
  const blob = event.data;
  const imageUrl = URL.createObjectURL(blob);
  document.getElementById('video-frame').src = imageUrl;
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket connection closed');
};
```

---

## Модели данных

### Term (Термин)

```json
{
  "id": 32,
  "val": "User",
  "base": 3
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| id | integer | Уникальный идентификатор термина |
| val | string | Название термина |
| base | integer | Базовый тип термина |

---

### TermMetadata (Метаданные термина)

```json
{
  "id": 32,
  "up": 1,
  "type": 3,
  "val": "User",
  "unique": 0,
  "mods": ["NOT NULL"],
  "reqs": [
    {
      "num": 1,
      "id": "100",
      "val": "Position",
      "type": "string",
      "mods": ["NOT NULL", "UNIQUE"]
    }
  ]
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| id | integer | ID термина |
| up | integer | ID родительского термина |
| type | integer | Тип термина |
| val | string | Название |
| unique | integer | 0 или 1, уникальность |
| mods | array | Модификаторы термина |
| reqs | array | Список реквизитов |

**TermRequisite (Реквизит термина):**

| Поле | Тип | Описание |
|------|-----|----------|
| num | integer | Порядковый номер |
| id | string | ID реквизита |
| val | string | Название реквизита |
| type | string | Тип реквизита |
| mods | array | Модификаторы (`NOT NULL`, `UNIQUE`, `ORDER`, `MULTIPLE`) |
| ref_id | string | ID ссылки (если есть) |

---

### Object (Объект)

```json
{
  "id": 252,
  "up": 1,
  "t": 32,
  "val": "John Doe",
  "reqs": {
    "100": "Manager"
  }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| id | integer | Уникальный ID объекта |
| up | integer | ID родительского объекта |
| t | integer | ID типа (термина) |
| val | string | Основное значение объекта |
| reqs | object | Словарь реквизитов `{req_id: value}` |

---

### HealthStatus

```json
{
  "status": "ok",
  "db": "connected"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| status | string | Статус сервиса: `ok`, `error` |
| db | string | Статус БД: `connected`, `unreachable` |

---

## Коды ошибок

### HTTP Status Codes

| Код | Описание |
|-----|----------|
| 200 | Успешно |
| 400 | Некорректный запрос |
| 401 | Не авторизован |
| 403 | Доступ запрещен |
| 404 | Не найдено |
| 409 | Конфликт (дубликат, используется) |
| 422 | Невалидные данные |
| 500 | Внутренняя ошибка сервера |

### Коды ошибок базы данных

API использует специальные коды ошибок, возвращаемые из PostgreSQL процедур:

| Код | HTTP | Описание |
|-----|------|----------|
| `1` | 200 | Успешно |
| `warn_term_exists` | 200 | Термин уже существует |
| `warn_req_exists` | 200 | Реквизит уже существует |
| `warn_ref_exists` | 200 | Ссылка уже существует |
| `warn_record_exists` | 200 | Запись уже существует |
| `err_term_not_found` | 404 | Термин не найден |
| `err_req_not_found` | 404 | Реквизит не найден |
| `err_obj_not_found` | 404 | Объект не найден |
| `err_term_name_exists` | 409 | Имя термина уже занято |
| `err_non_unique_val` | 409 | Значение не уникально |
| `err_term_is_in_use` | 409 | Термин используется |
| `err_empty_val` | 422 | Пустое значение |
| `err_type_not_found` | 400 | Неверный тип |
| `err_invalid_ref` | 400 | Неверная ссылка |
| `err_is_metadata` | 400 | Объект является метаданными |
| `err_is_referenced` | 400 | На объект есть ссылки |
| `err_incorrect_term` | 400 | Неверный термин |

### Формат ошибки

```json
{
  "detail": "Term not found"
}
```

или

```json
{
  "id": 150,
  "errors": "Term name already exists"
}
```

---

## Rate Limiting

В текущей версии API **rate limiting не реализован**.

Рекомендации для production:
- Использовать nginx с модулем `limit_req`
- Или реализовать middleware на уровне FastAPI
- Рекомендуемые лимиты: 100 запросов в минуту для обычных операций

---

## Версионирование

**Текущая версия:** `0.1.0`

API версионируется в заголовке `openapi_schema`:

```json
{
  "title": "Integram API",
  "version": "0.1.0",
  "openapi_version": "3.1.0"
}
```

**Стратегия версионирования:**
- Версия указана в OpenAPI спецификации
- При breaking changes версия будет увеличиваться
- Возможно добавление версионирования в URL (например, `/v2/`) в будущем

---

## Примеры использования

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"
TOKEN = "secret-token"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Проверка здоровья
response = requests.get(f"{BASE_URL}/health")
print(response.json())
# {'status': 'ok', 'db': 'connected'}

# Получить все термины
response = requests.get(
    f"{BASE_URL}/integram/terms",
    headers=HEADERS
)
terms = response.json()
print(terms)

# Создать новый термин
new_term = {
    "val": "Employee",
    "t": 3,
    "ALIAS": "Сотрудник"
}
response = requests.post(
    f"{BASE_URL}/integram/terms",
    headers=HEADERS,
    json=new_term
)
created_term = response.json()
print(f"Created term with ID: {created_term['id']}")

# Создать объект
new_object = {
    "id": 32,
    "up": 1,
    "attrs": {
        "t32": "John Doe",
        "t100": "Manager"
    }
}
response = requests.post(
    f"{BASE_URL}/integram/objects",
    headers=HEADERS,
    json=new_object
)
created_object = response.json()
print(f"Created object: {created_object}")

# Получить объекты с фильтрацией
response = requests.get(
    f"{BASE_URL}/integram/objects/32",
    headers=HEADERS,
    params={
        "up": 1,
        "limit": 10,
        "t100": "Manager"
    }
)
objects = response.json()
print(f"Found {len(objects['objects'])} objects")

# Обновить объект
updates = {"t100": "Senior Manager"}
response = requests.patch(
    f"{BASE_URL}/integram/objects/252",
    headers=HEADERS,
    json=updates
)
print(response.json())

# Удалить объект
response = requests.delete(
    f"{BASE_URL}/integram/objects/252",
    headers=HEADERS
)
print(response.json())
```

---

### Python (httpx - async)

```python
import httpx
import asyncio

BASE_URL = "http://localhost:8000"
TOKEN = "secret-token"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

async def main():
    async with httpx.AsyncClient() as client:
        # Получить метаданные термина
        response = await client.get(
            f"{BASE_URL}/integram/metadata/32",
            headers=HEADERS
        )
        metadata = response.json()
        print(metadata)

        # Создать несколько объектов параллельно
        tasks = []
        for i in range(5):
            new_object = {
                "id": 32,
                "up": 1,
                "attrs": {
                    "t32": f"User {i}",
                    "t100": "Developer"
                }
            }
            task = client.post(
                f"{BASE_URL}/integram/objects",
                headers=HEADERS,
                json=new_object
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        for response in responses:
            print(response.json())

asyncio.run(main())
```

---

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000';
const TOKEN = 'secret-token';
const HEADERS = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// Получить термины
async function getTerms() {
  const response = await fetch(`${BASE_URL}/integram/terms`, {
    headers: HEADERS
  });
  const terms = await response.json();
  console.log(terms);
}

// Создать термин
async function createTerm() {
  const newTerm = {
    val: 'Employee',
    t: 3,
    ALIAS: 'Сотрудник'
  };

  const response = await fetch(`${BASE_URL}/integram/terms`, {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify(newTerm)
  });

  const result = await response.json();
  console.log('Created term:', result);
  return result;
}

// Создать объект
async function createObject() {
  const newObject = {
    id: 32,
    up: 1,
    attrs: {
      t32: 'John Doe',
      t100: 'Manager'
    }
  };

  const response = await fetch(`${BASE_URL}/integram/objects`, {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify(newObject)
  });

  const result = await response.json();
  console.log('Created object:', result);
  return result;
}

// Получить объекты с фильтрацией
async function getObjects(termId, filters = {}) {
  const params = new URLSearchParams({
    up: 1,
    limit: 10,
    ...filters
  });

  const response = await fetch(
    `${BASE_URL}/integram/objects/${termId}?${params}`,
    { headers: HEADERS }
  );

  const result = await response.json();
  console.log('Objects:', result);
  return result;
}

// Использование
(async () => {
  await getTerms();
  const term = await createTerm();
  const object = await createObject();
  await getObjects(32, { t100: 'Manager' });
})();
```

---

### Node.js (axios)

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';
const TOKEN = 'secret-token';

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Authorization': `Bearer ${TOKEN}`,
    'Content-Type': 'application/json'
  }
});

// Проверка здоровья
async function checkHealth() {
  try {
    const response = await axios.get(`${BASE_URL}/health`);
    console.log('Health:', response.data);
  } catch (error) {
    console.error('Error:', error.response?.data);
  }
}

// Получить термины
async function getTerms() {
  try {
    const response = await client.get('/integram/terms');
    console.log('Terms:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data);
    throw error;
  }
}

// Создать термин
async function createTerm(termData) {
  try {
    const response = await client.post('/integram/terms', termData);
    console.log('Created term:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data);
    throw error;
  }
}

// Создать объект
async function createObject(objectData) {
  try {
    const response = await client.post('/integram/objects', objectData);
    console.log('Created object:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data);
    throw error;
  }
}

// Получить объекты с фильтрацией
async function getObjects(termId, params = {}) {
  try {
    const response = await client.get(`/integram/objects/${termId}`, {
      params: { up: 1, limit: 10, ...params }
    });
    console.log('Objects:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data);
    throw error;
  }
}

// Использование
(async () => {
  await checkHealth();

  const terms = await getTerms();

  const newTerm = await createTerm({
    val: 'Employee',
    t: 3,
    ALIAS: 'Сотрудник'
  });

  const newObject = await createObject({
    id: 32,
    up: 1,
    attrs: {
      t32: 'John Doe',
      t100: 'Manager'
    }
  });

  const objects = await getObjects(32, { t100: 'Manager' });
})();
```

---

### cURL примеры

```bash
# Проверка здоровья (без токена)
curl -X GET "http://localhost:8000/health"

# Получить все термины
curl -X GET "http://localhost:8000/integram/terms" \
  -H "Authorization: Bearer secret-token"

# Создать термин
curl -X POST "http://localhost:8000/integram/terms" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "val": "Employee",
    "t": 3,
    "ALIAS": "Сотрудник"
  }'

# Получить метаданные термина
curl -X GET "http://localhost:8000/integram/metadata/32" \
  -H "Authorization: Bearer secret-token"

# Создать объект
curl -X POST "http://localhost:8000/integram/objects" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 32,
    "up": 1,
    "attrs": {
      "t32": "John Doe",
      "t100": "Manager"
    }
  }'

# Получить объект
curl -X GET "http://localhost:8000/integram/object/252" \
  -H "Authorization: Bearer secret-token"

# Получить объекты с фильтрацией
curl -X GET "http://localhost:8000/integram/objects/32?up=1&limit=10&t100=Manager" \
  -H "Authorization: Bearer secret-token"

# Обновить объект
curl -X PATCH "http://localhost:8000/integram/objects/252" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "t100": "Senior Manager"
  }'

# Удалить объект
curl -X DELETE "http://localhost:8000/integram/objects/252" \
  -H "Authorization: Bearer secret-token"

# Добавить реквизит
curl -X POST "http://localhost:8000/integram/requisites" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 32,
    "t": 100,
    "notnull": 1
  }'

# Создать ссылку
curl -X POST "http://localhost:8000/integram/references" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 100
  }'

# Видео: Подключиться к дрону
curl -X POST "http://localhost:8000/video/connect" \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "drone_id": "user_drone_walksnail",
    "source_url": "rtsp://localhost:8554/drone_camera",
    "source_type": "rtsp"
  }'

# Видео: Получить информацию о потоке
curl -X GET "http://localhost:8000/video/info/user_drone_walksnail" \
  -H "Authorization: Bearer secret-token"

# Видео: Отключиться
curl -X POST "http://localhost:8000/video/disconnect/user_drone_walksnail" \
  -H "Authorization: Bearer secret-token"
```

---

### Go

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
)

const (
    BaseURL = "http://localhost:8000"
    Token   = "secret-token"
)

type Term struct {
    ID   int    `json:"id"`
    Val  string `json:"val"`
    Base int    `json:"base"`
}

type TermCreate struct {
    Val   string `json:"val"`
    T     int    `json:"t"`
    Alias string `json:"ALIAS,omitempty"`
}

type ObjectCreate struct {
    ID    int                    `json:"id"`
    Up    int                    `json:"up"`
    Attrs map[string]interface{} `json:"attrs"`
}

func makeRequest(method, url string, body interface{}) (*http.Response, error) {
    var reqBody io.Reader
    if body != nil {
        jsonBody, err := json.Marshal(body)
        if err != nil {
            return nil, err
        }
        reqBody = bytes.NewBuffer(jsonBody)
    }

    req, err := http.NewRequest(method, url, reqBody)
    if err != nil {
        return nil, err
    }

    req.Header.Set("Authorization", "Bearer "+Token)
    req.Header.Set("Content-Type", "application/json")

    return http.DefaultClient.Do(req)
}

func getTerms() ([]Term, error) {
    resp, err := makeRequest("GET", BaseURL+"/integram/terms", nil)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var terms []Term
    if err := json.NewDecoder(resp.Body).Decode(&terms); err != nil {
        return nil, err
    }

    return terms, nil
}

func createTerm(termData TermCreate) (map[string]interface{}, error) {
    resp, err := makeRequest("POST", BaseURL+"/integram/terms", termData)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var result map[string]interface{}
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }

    return result, nil
}

func createObject(objectData ObjectCreate) (map[string]interface{}, error) {
    resp, err := makeRequest("POST", BaseURL+"/integram/objects", objectData)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var result map[string]interface{}
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }

    return result, nil
}

func main() {
    // Получить термины
    terms, err := getTerms()
    if err != nil {
        fmt.Printf("Error getting terms: %v\n", err)
        return
    }
    fmt.Printf("Terms: %+v\n", terms)

    // Создать термин
    newTerm := TermCreate{
        Val:   "Employee",
        T:     3,
        Alias: "Сотрудник",
    }
    createdTerm, err := createTerm(newTerm)
    if err != nil {
        fmt.Printf("Error creating term: %v\n", err)
        return
    }
    fmt.Printf("Created term: %+v\n", createdTerm)

    // Создать объект
    newObject := ObjectCreate{
        ID: 32,
        Up: 1,
        Attrs: map[string]interface{}{
            "t32":  "John Doe",
            "t100": "Manager",
        },
    }
    createdObject, err := createObject(newObject)
    if err != nil {
        fmt.Printf("Error creating object: %v\n", err)
        return
    }
    fmt.Printf("Created object: %+v\n", createdObject)
}
```

---

### PHP

```php
<?php

const BASE_URL = 'http://localhost:8000';
const TOKEN = 'secret-token';

function makeRequest($method, $endpoint, $data = null) {
    $url = BASE_URL . $endpoint;

    $options = [
        'http' => [
            'method' => $method,
            'header' => [
                'Authorization: Bearer ' . TOKEN,
                'Content-Type: application/json'
            ]
        ]
    ];

    if ($data !== null) {
        $options['http']['content'] = json_encode($data);
    }

    $context = stream_context_create($options);
    $response = file_get_contents($url, false, $context);

    return json_decode($response, true);
}

// Получить термины
function getTerms() {
    return makeRequest('GET', '/integram/terms');
}

// Создать термин
function createTerm($termData) {
    return makeRequest('POST', '/integram/terms', $termData);
}

// Создать объект
function createObject($objectData) {
    return makeRequest('POST', '/integram/objects', $objectData);
}

// Использование
try {
    // Получить термины
    $terms = getTerms();
    echo "Terms: " . json_encode($terms) . "\n";

    // Создать термин
    $newTerm = [
        'val' => 'Employee',
        't' => 3,
        'ALIAS' => 'Сотрудник'
    ];
    $createdTerm = createTerm($newTerm);
    echo "Created term: " . json_encode($createdTerm) . "\n";

    // Создать объект
    $newObject = [
        'id' => 32,
        'up' => 1,
        'attrs' => [
            't32' => 'John Doe',
            't100' => 'Manager'
        ]
    ];
    $createdObject = createObject($newObject);
    echo "Created object: " . json_encode($createdObject) . "\n";

} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
```

---

## Дополнительная информация

### Swagger UI

Интерактивная документация API доступна по адресу:
```
http://localhost:8000/docs
```

Там вы можете:
- Просматривать все эндпоинты
- Тестировать запросы напрямую из браузера
- Просматривать схемы данных
- Авторизоваться с Bearer токеном

### ReDoc

Альтернативная документация доступна по адресу:
```
http://localhost:8000/redoc
```

### Поддержка

Для вопросов и предложений:
- GitHub Issues: https://github.com/horhe-dvlp/integram/issues
- Email: support@integram.example.com (замените на реальный)

### Лицензия

Уточните лицензию проекта в файле LICENSE.

---

**Документация актуальна для версии API:** `0.1.0`
**Дата последнего обновления:** 2025-10-15
