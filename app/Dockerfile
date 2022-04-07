FROM python:3.8.10-slim-buster

WORKDIR /usr/src

ENV PYTHONUNBUFFERED 1

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
