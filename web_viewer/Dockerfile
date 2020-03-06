FROM php:7.3-apache
USER root

RUN apt-get update && \
    apt-get -y install locales && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm



RUN docker-php-ext-install pdo_mysql
RUN pecl install xdebug && docker-php-ext-enable xdebug