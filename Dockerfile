# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
ARG DEPLOY_URL=http://localhost:8000/
ENV DEPLOY_URL $DEPLOY_URL

COPY . .

RUN FLASK_APP=shortenme/app.py python -m flask init-db

ENTRYPOINT ["./gunicorn.sh"]