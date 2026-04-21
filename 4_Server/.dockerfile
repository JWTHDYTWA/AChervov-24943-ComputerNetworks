FROM python:3-slim
EXPOSE 8000

WORKDIR /home/server
COPY . .
RUN echo 'Acquire::Retries "32";' > /etc/apt/apt.conf.d/80-retries
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install-deps
RUN playwright install firefox

ENTRYPOINT ["uvicorn", "main:app"]
CMD ["--host", "0.0.0.0", "--port", "8000"]