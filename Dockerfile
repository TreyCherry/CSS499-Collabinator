# syntax=docker/dockerfile:1
FROM python:3.10-slim-bullseye
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    libreoffice

WORKDIR /collab-docker
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

#RUN git clone https://github.com/TreyCherry/CSS499-Collabinator.git
COPY . .

RUN python -m flask --app CSS499-Collabinator init-db

CMD [ "python3", "-m" , "flask", "--app", "CSS499-Collabinator", "run", "--host=0.0.0.0"]



