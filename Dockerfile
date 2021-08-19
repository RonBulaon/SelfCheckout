FROM python:3.7-alpine
MAINTAINER Ron Bulaon  

ENV PYTHONUNBUFFERED 1
ENV PATH="/scripts:${PATH}"

RUN apk add ssmtp
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt


RUN mkdir /app 
COPY ./selfcheckout /app
WORKDIR /app
