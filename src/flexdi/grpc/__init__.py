import typing as t

import grpc.aio
from grpc_interceptor import AsyncServerInterceptor

from flexdi import ApplicationScope
from flexdi._util import invoke_callable


class FlexInterceptor(AsyncServerInterceptor):
    def __init__(self, app_scope: ApplicationScope):
        self.app_scope = app_scope

    async def intercept(
        self,
        method: t.Callable[..., t.Any],
        request: t.Any,
        context: grpc.aio.ServicerContext[t.Any, t.Any],
        method_name: str,
    ) -> t.Any:
        async with self.app_scope.request_scope() as req_scope:
            method_args = await req_scope.resolve_args(
                method, request=request, context=context
            )
            return await invoke_callable(req_scope._store._stack, method, method_args)


__all__ = ["FlexInterceptor"]
