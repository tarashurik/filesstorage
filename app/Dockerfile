FROM python:3.8.10-slim-buster

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src

COPY requirements.txt ./
RUN pip install -r requirements.txt

EXPOSE 8000
