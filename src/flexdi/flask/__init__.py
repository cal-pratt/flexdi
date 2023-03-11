from contextlib import AsyncExitStack

from flask import Flask, Response, g, request

from flexdi import FlexGraph


class FlaskGraph(FlexGraph):
    def __init__(self, app: Flask) -> None:
        super().__init__()

        @app.before_request
        async def create_scopes() -> None:
            g._flexdi_stack = stack = AsyncExitStack()

            if request.endpoint not in app.view_functions:
                return

            app_scope = self.application_scope()
            await app_scope.open()
            stack.push_async_callback(app_scope.close)

            req_scope = app_scope.request_scope()
            await req_scope.open()
            stack.push_async_callback(req_scope.close)

            request.view_args = await self.resolve_args(
                app.view_functions[request.endpoint], **(request.view_args or {})
            )

        @app.after_request
        async def destroy_scopes(response: Response) -> Response:
            await g._flexdi_stack.aclose()
            return response


__all__ = ["FlaskGraph"]
