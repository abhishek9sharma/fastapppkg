FROM python:3.11-slim
EXPOSE 80
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN pip install --no-cache-dir -e .
CMD ["uvicorn", "fastapppkg.restapi.rootsvc:app", "--host", "0.0.0.0", "--port", "80"]
