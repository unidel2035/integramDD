# Changelog

Все значимые изменения в проекте IntegramDD будут задокументированы в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/),
и проект придерживается [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

### Added
- Документация изменений проекта (CHANGELOG.md)

## [0.1.0] - 2025-10-14

### Added
- Видео-стриминг API для интеграции с дронами (video streaming endpoints)
- GraphQL endpoint для получения объектов терминов с POST методом
- Динамические SQL запросы с поддержкой reference-up соединений
- Rate limiting и DDoS защита для всех API endpoints
- Middleware для ограничения размера запросов
- Комплексные тесты для rate limiting и безопасности
- Диаграмма архитектуры сервиса IdeaV
- Документация по концепции и плану разработки
- Документация по методам API
- Аудит документации проекта
- Endpoint для получения всех метаданных терминов
- CRUD операции для терминов
- Аутентификация через Bearer token
- Кастомизация OpenAPI схемы с описанием безопасности
- CI/CD workflows для автоматического и ручного деплоя
- Endpoints для создания и получения объектов с логированием
- Утилиты для обработки метаданных и реквизитов
- Фильтрация объектов терминов
- Health check функциональность
- Настройка базы данных PostgreSQL
- Начальная реализация FastAPI приложения

### Changed
- Улучшена обработка missing fields в функции `_build_reqs_map`
- Оптимизирован процесс очистки Docker в deployment workflow
- Обновлен auto-deploy workflow для сброса рабочего дерева в remote состояние
- Изменен тип атрибута 'name' в HeaderField с str на Any
- Упрощена функция `get_term_objects` с удалением неиспользуемых SQL запросов
- Улучшена обработка JSON ответов
- Обновлены endpoint paths для терминов
- Улучшена обработка уникальных ограничений в term builder
- Улучшена JSON сериализация для поля mods
- Обновлены переменные окружения PostgreSQL для использования динамических значений
- Улучшена обработка ошибок в deployment скрипте

### Fixed
- Восстановлен queries router из ветки feature-queries
- Исправлено присвоение ключей в `_build_reqs_map` для обработки None имен полей
- Исправлена обработка отсутствующих field references в `_build_reqs_map`
- Улучшена логика получения полей в функции `_build_reqs_map`
- Улучшена обработка ошибок для неизвестных field IDs
- Исправлен атрибут warning в ответе `patch_object`
- Исправлено сопоставление ключей в val_dict для функции `get_term_objects`
- Удален лишний параметр parent_id в SQL запросе
- Восстановлен файл .gitignore
- Исправлена команда export для DB_NAME в deployment скрипте
- Исправлена опечатка в команде export для DB_NAME
- Улучшен deployment скрипт для ожидания готовности PostgreSQL
- Удалена избыточная команда docker compose pull
- Удалены избыточные объявления переменных окружения
- Обновлены переменные окружения для использования secrets

### Security
- Добавлена защита от DDoS атак
- Реализован rate limiting для всех endpoints
- Добавлен Bearer token authentication

## [0.0.1] - 2025-05-15

### Added
- Начальная версия проекта
- Базовая структура FastAPI приложения
- Интеграция с PostgreSQL базой данных
- API endpoints для работы с терминами
- Токен-based аутентификация
- Docker и Docker Compose конфигурация
- Инициализация базы данных
- README с инструкциями по установке

[Unreleased]: https://github.com/unidel2035/integramDD/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/unidel2035/integramDD/releases/tag/v0.1.0
[0.0.1]: https://github.com/unidel2035/integramDD/releases/tag/v0.0.1
