from typing import Callable, Awaitable

import aiohttp_jinja2
import jinja2
from aiohttp import web

from edustudio.web import settings
from edustudio.web import handlers


Handler = Callable[[web.Request], Awaitable[web.Response]]


def setup_routes(app: web.Application) -> None:
    app.add_routes([
        web.get("/", handlers.handle_home),
        web.get("/students", handlers.create_student_list_handler()),
        web.get("/students/{student_id}", handlers.create_student_detail_handler()),
        web.get("/students/{student_id}/attendance", handlers.create_student_attendance_handler())
    ])


def create():
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(settings.TEMPLATES_DIR))
    app.router.add_static("/static", settings.STATIC_DIR)
    setup_routes(app)
    return app


if __name__ == '__main__':
    web.run_app(create(), port=3000)



