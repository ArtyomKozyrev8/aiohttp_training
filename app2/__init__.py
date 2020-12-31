import asyncio
from functools import wraps
import os
from typing import Dict, Any

from aiohttp import web, WSMsgType
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp_session import setup, get_session
import aiohttp_jinja2
import jinja2
from aiohttp.web import RouteTableDef
import logging

routes = RouteTableDef()


@routes.get(path="/hello_2")
async def hello_world_2(req: web.Request) -> web.Response:
    session = await get_session(req)
    name = session.get("name", "None")
    surname = session.get("surname", "None")

    logging.info("hello world from app2")

    return web.json_response(
        {
            "answer": "Hello world from app # 2",
            "name": name,
            "surname": surname
        }
    )


@routes.get(path="/template")
@aiohttp_jinja2.template("main.html")
async def hello_world_2(req: web.Request) -> Dict[str, Any]:
    session = await get_session(req)
    name = session.get("name", "None")
    surname = session.get("surname", "None")
    return {"app": "App # 2", "name": name, "surname": surname}


async def init_func_2(args=None) -> web.Application:
    """Application factory"""
    app = web.Application()

    secret_key = b'\xc9\x11\xf3^k\x00\n\xb4l\xd4\xb8\xd5\xaaEY\x91\xbd\xf9\xb2~\x87\xac\xd9u^pn\xe9Ty3Q'
    setup(app, EncryptedCookieStorage(secret_key, cookie_name="test_website"))  # create session concept

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("app2/templates"))  # setup jinja

    app.add_routes(routes)
    # add static files handling
    # /static - all urls in templates will be like /static/filename
    # "app/static" - folder with files
    app.add_routes([web.static('/static', "app2/static")])

    return app
