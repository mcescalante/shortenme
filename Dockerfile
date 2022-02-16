# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN FLASK_APP=shortenme/app.py python -m flask init-db

ENTRYPOINT ["./gunicorn.sh"]