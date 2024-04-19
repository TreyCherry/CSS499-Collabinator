
# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget

WORKDIR /collab-docker

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN git clone https://github.com/TreyCherry/CSS499-Collabinator.git

RUN python -m flask --app CSS499-Collabinator init-db

# CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
CMD [ "python3", "-m" , "flask", "--app", "CSS499-Collabinator", "run", "--host=0.0.0.0"]
#CMD [ "python3", "-m" , "flask", "--app", "CSS499-Collabinator", "run"]



