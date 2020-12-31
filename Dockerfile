FROM python:3.9-alpine

WORKDIR /usr/src

RUN apk add --no-cache tzdata

ENV TZ=Europe/Moscow

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN /usr/local/bin/python -m pip install --upgrade pip

# TO RUN C LIBS
RUN apk add gcc \
 musl-dev \
 libffi-dev \
 make \
 libressl-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a group and user
RUN addgroup -S appgroup && adduser -S the_user -G appgroup

RUN chown -R the_user:appgroup /usr/src/app
RUN chmod 755 /usr/src/app

RUN chown -R the_user:appgroup /usr/src/uploads
RUN chmod 755 /usr/src/uploads

# Tell docker that all future commands should run as the appuser user
USER the_user

# do not try to open port less than 1000 with no sudo rights
# how to run WITHOUT GUNICORN command
#CMD python3 -m aiohttp.web -H 0.0.0.0 -P 9999 app:init_func

# how to run with GUNICORN:
CMD gunicorn app:init_func_gunicorn --bind 0.0.0.0:9999 --worker-class aiohttp.GunicornWebWorker