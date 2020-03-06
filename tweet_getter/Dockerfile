FROM python:3.7
USER root

RUN apt-get update && \
    apt-get install -y locales && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm

RUN pip install --upgrade pip && \
    pip install --upgrade setuptools && \
    pip install requests-oauthlib  mysql.connector slackweb schedule

COPY ./src /home/
