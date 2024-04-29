# syntax=docker/dockerfile:1
FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get upgrade -y
RUN apt-get install --fix-missing -y \
    libpcre3 libpcre3-dev \
    libreoffice libatlas-base-dev gfortran nginx supervisor

RUN pip3 install uwsgi

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt 

RUN useradd --no-create-home nginx

RUN rm /etc/nginx/sites-enabled/default
RUN rm -r /root/.cache

COPY server-conf/nginx.conf /etc/nginx/
COPY server-conf/flask-site-nginx.conf /etc/nginx/conf.d/
#COPY server-conf/default-sites /etc/nginx/sites-available/default
COPY server-conf/uwsgi.ini /etc/uwsgi/
COPY server-conf/supervisord.conf /etc/

COPY /app /app
WORKDIR /app

RUN python -m flask --app collabinator init-db

#CMD [ "python3", "-m" , "flask", "--app", "flask-app", "run", "--host=0.0.0.0"]
CMD ["/usr/bin/supervisord"]

EXPOSE 8082


