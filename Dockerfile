FROM python:3.9-alpine

WORKDIR /usr/src/app

RUN apk add --no-cache tzdata

ENV TZ=Europe/Moscow

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN /usr/local/bin/python -m pip install --upgrade pip

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a group and user
RUN addgroup -S appgroup && adduser -S the_user -G appgroup

RUN chown -R the_user:appgroup /usr/src/app
RUN chmod 755 /usr/src/app

# Tell docker that all future commands should run as the appuser user
USER the_user

CMD python3 -m aiohttp.web -H localhost -P 8080 app:init_func
