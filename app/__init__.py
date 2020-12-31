import asyncio
import logging
from functools import wraps
import os
from typing import Dict, Any
from aiohttp import web, WSMsgType
from aiohttp import WSCloseCode
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp_session import setup, get_session
import aiohttp_jinja2
import jinja2
import weakref
from random import randint

from app2 import init_func_2


routes = web.RouteTableDef()  # helps to follow Flask style route decorators


@routes.get("/react_random_num")
async def react_random_num_call(request: web.Request) -> web.Response:
    resp = web.json_response({"res": f"Result from Aiohttp : {randint(1, 100)}"})
    # add header to response to use with react app
    resp.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return resp

########################################################################################################################

# signal example


async def on_prepare(request, response):
    # can change headers even in websocket messages and stream responses
    response.headers['My-Header'] = 'value_here'


########################################################################################################################

# middleware with arg


def middleware_factory(text):
    @web.middleware
    async def sample_middleware(request, handler):
        resp = await handler(request)
        logging.info(text)
        return resp
    return sample_middleware


########################################################################################################################

# Customized error handler if error number is 401

@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
    except web.HTTPException as ex:
        if ex.status != 401:
            raise
        return web.json_response({"error": "not really authorised"}, status=401)
    return response


########################################################################################################################

# Just random middleware example


@web.middleware
async def middleware1(request, handler):
    logging.info('Middleware 1 called')
    response = await handler(request)
    logging.info('Middleware 1 finished')
    return response


@web.middleware
async def middleware2(request, handler):
    logging.info('Middleware 2 called')
    response = await handler(request)
    logging.info('Middleware 2 finished')
    return response

########################################################################################################################


def check_if_login(f):
    """Decorator to login"""
    @wraps(f)
    async def inner(request):
        session = await get_session(request)
        # request['my_private_key'] = "data"
        # request-life-long storage (above line) can be in further used in inner function
        # the same can be done with response object
        if not (session.get("name", None) and session.get("surname", None)):
            raise web.HTTPUnauthorized()
        else:
            return await f(request)
    return inner


########################################################################################################################

# SOCKET PLAY BLOCK

@routes.get("/socket_page", name="socket_page")
@aiohttp_jinja2.template("socket.html")
@check_if_login
async def socket_page(req: web.Request) -> Dict[str, Any]:
    """just template for the socket example"""
    return {}


async def send_to_socket(ws: web.WebSocketResponse):
    """helper func which send messages to socket"""
    for i in range(100):
        if ws.closed:
            break
        await ws.send_str("I am super socket server!!")
        await asyncio.sleep(1.5)


async def listen_to_socket(ws: web.WebSocketResponse):
    """helper func which Listen messages to socket"""
    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                await ws.send_str(msg.data + '/answer')
        elif msg.type == WSMsgType.ERROR:
            logging.info('ws connection closed with exception %s' %
                  ws.exception())


@routes.get("/socket", name="socket")  # should be GET !!!
async def websocket_handler(req:  web.Request) -> web.WebSocketResponse:
    """Socket aiohttp handler"""
    ws = web.WebSocketResponse()
    req.app['websockets'].add(ws)  # add websocket to WeakSet in order to close ws from signal
    await ws.prepare(req)

    t1 = asyncio.create_task(listen_to_socket(ws))
    t2 = asyncio.create_task(send_to_socket(ws))
    await t1, t2

    logging.info('websocket connection closed')

    return ws

########################################################################################################################

# UPLOAD FILES BLOCK


@routes.get("/upload_page", name="upload_page")
@aiohttp_jinja2.template("upload.html")
@check_if_login
async def upload_page(req: web.Request) -> Dict[str, Any]:
    """just template for the upload file example"""
    return {}


@routes.post("/store/m4a", name="upload_action")
@check_if_login
async def upload_page(req: web.Request) -> web.Response:
    """Illustrates how we can upload a file"""
    multipart_reader = await req.multipart()  # we get MultipartReader

    field = await multipart_reader.next()
    logging.info(field.name)  # just to show what is happening
    logging.info(await field.text(encoding="utf8"))

    field = await multipart_reader.next()
    logging.info(field.name)
    logging.info(field.filename)

    size = 0
    with open(os.path.join(os.getcwd(), "uploads", field.filename), 'wb') as f:
        while True:
            chunk = await field.read_chunk()  # 8192 bytes by default.
            if not chunk:
                break
            size += len(chunk)
            f.write(chunk)

    return web.Response(text='{} sized of {} successfully stored'.format(field.filename, size))

########################################################################################################################


@routes.get("/j_auth", name="json_auth")
@check_if_login
async def json_auth_endpoint(req: web.Request) -> web.Response:
    """Authorized return json endpoint"""
    session = await get_session(req)
    name = session.get("name")
    surname = session.get("surname")

    return web.json_response({"name": name, "surname": surname})


async def return_json(req: web.Request) -> web.Response:
    """Return json"""
    c = req.app.get("imaginary_connector", None)
    return web.json_response({"x": 1, "y": 2, "imaginary_connector": c})


@aiohttp_jinja2.template("main.html")
async def show_main_page_template(req: web.Request) -> Dict[str, Any]:
    """Main page with auth"""
    session = await get_session(req)
    name = session.get("name")
    surname = session.get("surname")
    return {"name": name, "surname": surname}


async def try_to_login(req: web.Request) -> web.Response:
    """
    ATTENTION to save session do not use raise !!!!
    USE RETURN INSTEAD ! Otherwise changes session (cookie) will not be saved!
    :param req: request object
    :return: response object
    """
    data = await req.post()   # how to work with simple not multipart post
    session = await get_session(req)
    session["name"] = data.get("name")
    session["surname"] = data.get("surname")
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # !!! IMPORTANT PART NOT EXPLAINED IN DOCS !!!
    if session.get("name") and session.get("surname"):
        # if you just raise error, cookie wil not be updated, since all action will be on server side
        # return error to update user cookie file and explain where to redirect
        return web.HTTPSeeOther(location=req.app.router['json_auth'].url_for())
    else:
        return web.HTTPSeeOther(location=req.app.router['main_template'].url_for())


async def index(req: web.Request) -> web.Response:
    """Simple route"""
    session = await get_session(req)
    session.clear()
    return web.Response(text="Hello My!")


async def regex_route(req: web.Request) -> web.Response:
    """URL with variable parts"""
    text = (
        f"Hello custom url! X1: {req.match_info['x1']}"
        f" X2: {req.match_info['x2']}"
    )
    return web.Response(text=text)


async def redirect_route(req: web.Request) -> web.Response:
    """Redirect if POST method"""
    if req.method == "GET":
        return web.Response(text="redirect route")
    else:
        # how to build url
        raise web.HTTPSeeOther(location=req.app.router["reg"].url_for(x1="222", x2="1111").with_query({"a": "abc"}))

########################################################################################################################


async def on_shutdown(app):
    """The signal makes websockets to close as soon as signal received, otherwise can run much longer"""
    for ws in set(app['websockets']):
        logging.info(ws)
        await ws.close(code=WSCloseCode.GOING_AWAY, message='Server shutdown')


########################################################################################################################

async def do_work() -> None:
    """some background task"""
    while True:
        logging.info("Do work!")
        await asyncio.sleep(30)


async def background_worker(app) -> None:
    """this happens on start signal"""
    app["back_task"] = asyncio.create_task(do_work())


async def stop_background_worker(app) -> None:
    """this happens when app stops"""
    try:
        app["back_task"].cancel()
        await app["back_task"]
    except asyncio.CancelledError:
        logging.info("Goodbye background Task due to Cancel!")
    finally:
        logging.info("Goodbye background Task!")

########################################################################################################################

# Application factory pattern


async def init_func(args=None) -> web.Application:
    """Application factory for standalone run"""
    app = web.Application(middlewares=[error_middleware, middleware_factory("zorro!"), middleware1, middleware2])

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s || %(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
        force=True  # key element to supress other logs
    )

    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    app.on_startup.append(background_worker)

    app.on_cleanup.append(stop_background_worker)

    # added another app (subapp)
    app2 = await init_func_2()
    app.add_subapp(prefix="/app2/", subapp=app2)

    app.on_response_prepare.append(on_prepare)  # signal added

    app["imaginary_connector"] = "the_imaginary_connector"  # context "global" vars (see use case in return_json func)

    secret_key = b'\xc9\x11\xf3^k\x00\n\xb4l\xd4\xb8\xd5\xaaEY\x91\xbd\xf9\xb2~\x87\xac\xd9u^pn\xe9Ty3Q'
    setup(app, EncryptedCookieStorage(secret_key, cookie_name="test_website"))  # create session concept

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("app/templates"))  # setup jinja

    app.add_routes(routes)
    app.add_routes(
        [
            web.get("/j", return_json, name="return_json"),
            web.get("/re", redirect_route, name="redirect"),
            web.post("/re", redirect_route, name="redirect"),
            web.get("/reg/{x1}/{x2:\d+}", regex_route, name="reg"),  # {} - variable part, :\d+ - regex
            web.get("/main", show_main_page_template, name="main_template"),
            web.post("/main", try_to_login, name="try_to_login"),
            web.get("/", index, name="index")
        ]
    )
    # add static files handling
    # /static - all urls in templates will be like /static/filename
    # "app/static" - folder with files
    app.add_routes([web.static('/static', "app/static")])
    for resource in app.router.resources():
        logging.info(resource)

    # place to store sockets globally in the process
    # pay attention that if we have several process workers (e.g. in Gunicorn)
    # each process will have it's own app['websockets']
    app['websockets'] = weakref.WeakSet()
    app.on_shutdown.append(on_shutdown)

    return app


async def init_func_gunicorn():
    """is used to run aiohttp with gunicorn as middleware"""
    app = init_func()
    return app


if __name__ == '__main__':
    web.run_app(init_func())
