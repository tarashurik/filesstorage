# pull official base image
FROM python:3.8.10

#RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ENV PYTHONUNBUFFERED 1

# install system dependencies
#RUN apt-get update \
#  && apt-get -y install netcat gcc postgresql \
#  && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

# add app
#COPY . .

EXPOSE 8000
