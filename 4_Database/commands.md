
## Запуск контейнера
```ps1
docker run -d --network compnet -e POSTGRES_PASSWORD=$env:DB_PASS -v pg_data:/var/lib/postgresql/data --name database postgres:18-alpine3.22
```