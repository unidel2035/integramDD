1. Требования к окружению
	- OC: Linux / Windows / macOS
	- Docker ≥ 20.10.0
	- Docker Compose: ≥ 1.29.0
	- 8000 порт должен быть свободен
2. Загрузка
```
git clone https://github.com/horhe-dvlp/integram.git
cd integram
```
3. Подготовка окружения
```
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=integram
export DB_USER=postgres
export DB_PASSWORD=postgres
```
4. Запуск в Docker
```
docker compose up --build
```
Или (в старом синтаксисе)
```
docker-compose up --build
```
5. Загрузка хранимых процедур в базу данных
```
cd ./.sql_to_load
./upload_methods.sh -u postgres -p postgres -d integram
cd ..
```
6. Проверка доступности
После запуска перейдите в браузере:
```
http://localhost:8000/docs
```
7. Аутентификация
Для тестирования защищённых методов API предусмотрен токен:
```
secret-token
```