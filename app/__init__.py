import asyncio
from functools import wraps
import os
from typing import Dict, Any

from aiohttp import web, WSMsgType
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp_session import setup, get_session
import aiohttp_jinja2
import jinja2


routes = web.RouteTableDef()  # helps to follow Flask style route decorators


def check_if_login(f):
    """Decorator to login"""
    @wraps(f)
    async def inner(request):
        session = await get_session(request)
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
            print('ws connection closed with exception %s' %
                  ws.exception())


@routes.get("/socket", name="socket")  # should be GET !!!
async def websocket_handler(req:  web.Request) -> web.WebSocketResponse:
    """Socket aiohttp handler"""
    ws = web.WebSocketResponse()
    await ws.prepare(req)

    t1 = asyncio.create_task(listen_to_socket(ws))
    t2 = asyncio.create_task(send_to_socket(ws))
    await t1, t2

    print('websocket connection closed')

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
    print(field.name)  # just to show what is happening
    print(await field.text(encoding="utf8"))

    field = await multipart_reader.next()
    print(field.name)
    print(field.filename)

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
    return web.json_response({"x": 1, "y": 2})


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

# Application factory patter


def init_func(argv=None) -> web.Application:
    """Application factory"""
    app = web.Application()

    secret_key = b'\xc9\x11\xf3^k\x00\n\xb4l\xd4\xb8\xd5\xaaEY\x91\xbd\xf9\xb2~\x87\xac\xd9u^pn\xe9Ty3Q'
    setup(app, EncryptedCookieStorage(secret_key, cookie_name="test_website"))  # create session concept

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("app/templates")) # setup jinja

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
    for resource in app.router.resources():
        print(resource)

    return app


if __name__ == '__main__':
    web.run_app(init_func())
