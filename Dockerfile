# syntax=docker/dockerfile:1
FROM python:3.10-slim-bullseye
RUN apt-get update && apt-get upgrade -y
RUN apt-get install --fix-missing -y \
    libreoffice

WORKDIR /collab-docker
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN python -m flask --app flask-app init-db

CMD [ "python3", "-m" , "flask", "--app", "flask-app", "run", "--host=0.0.0.0"]

EXPOSE 5000


