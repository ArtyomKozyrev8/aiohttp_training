# aiohttp_training
Test project to learn how to work with aiohttp framework

**How to run as a standalone application:**

python -m aiohttp.web -H localhost -P 8080 app:init_func

**How to run with Gunicorn (not work in Windows)**

gunicorn app:init_func --bind 0.0.0.0:9999 --worker-class aiohttp.GunicornWebWorker

**How to run in Docker**

docker build -t aio_serv2 .

docker run -d --name aio_serv2 -p 9999:9999 aio_serv2

