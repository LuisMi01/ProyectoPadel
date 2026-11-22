"""Protección CSRF: las peticiones que cambian datos solo se aceptan desde la web.

La sesión va en una cookie que el navegador adjunta sola, así que otra web podría intentar
enviar un formulario a la API en nombre del usuario. Los navegadores mandan la cabecera
Origin en esas peticiones: si no es uno de CORS_ORIGINS, se rechaza con 403.
Las peticiones sin Origin (curl, tareas internas, tests) no llevan la cookie del navegador
del usuario y se dejan pasar.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

METODOS_SEGUROS = {"GET", "HEAD", "OPTIONS"}


class ComprobarOrigen(BaseHTTPMiddleware):
    def __init__(self, app, origenes_permitidos: list[str]) -> None:
        super().__init__(app)
        self.permitidos = {o.rstrip("/") for o in origenes_permitidos}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        origen = request.headers.get("origin")
        if (
            request.method not in METODOS_SEGUROS
            and origen is not None
            and origen.rstrip("/") not in self.permitidos
        ):
            return JSONResponse({"detail": "Origen no permitido"}, status_code=403)
        return await call_next(request)
