#FROM python:3.9
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9
EXPOSE 80
EXPOSE 5000
COPY ./ /app
WORKDIR /app
RUN pip install requests
RUN python -m pip install -e . 
CMD ["uvicorn", "fastapppkg.restapi.rootsvc:app", "--host", "0.0.0.0", "--port", "80", "--reload"]