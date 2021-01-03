# aiohttp_training
Test project to learn how to work with aiohttp framework

**How to get the code:**

git clone https://github.com/ArtyomKozyrev8/aiohttp_training.git

docker build -t aio_serv2 .

**How to run as a standalone application on local PC without Docker:**

python -m aiohttp.web -H localhost -P 8080 app:init_func

**How to run with Gunicorn (not work in Windows)**

gunicorn app:init_func_gunicorn --bind 0.0.0.0:9999 --worker-class aiohttp.GunicornWebWorker

**Run as independent app in Docker without Nginx:**

docker run -d --name aio_serv2 -p 9999:9999 aio_serv2

**Run with Nginx:** 

docker run -v aio_serv_v:/usr/src/app/static -v aio_serv_v2:/usr/src/app2/static --network=aio_net -d --name aio_serv2 aio_serv2

