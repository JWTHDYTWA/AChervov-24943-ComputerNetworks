
## Start server
```ps1
docker run -d --network compnet --name server -e DB_PASS=$env:DB_PASS -p 8000:8000 jwth32/scraper
```