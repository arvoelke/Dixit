FROM python:3
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8888
VOLUME ["/app/static/cards/dixit"]
ENTRYPOINT ["python", "server.py"]

