from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import grpc.aio

from flexdi import FlexGraph
from flexdi.grpc import FlexInterceptor

from .protos import hello_pb2 as hello
from .protos import hello_pb2_grpc as hello_grpc


class HelloPrefix:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix


class HelloServicer(hello_grpc.HelloServicer):
    async def SayHello(  # type: ignore[override]
        self,
        request: hello.HelloRequest,
        context: grpc.aio.ServicerContext[Any, Any],
        hello_prefix: HelloPrefix,
    ) -> hello.HelloReply:
        return hello.HelloReply(message=hello_prefix.prefix + request.name)


graph = FlexGraph()
graph.bind(HelloServicer, scope="application", eager=True)


@graph.bind
def provide_hello_prefix() -> HelloPrefix:
    return HelloPrefix("Hello ")


@asynccontextmanager
async def create_server() -> AsyncIterator[grpc.aio.Server]:
    async with graph.application_scope() as app_scope:
        server = grpc.aio.server(
            interceptors=[FlexInterceptor(app_scope)],
        )

        hello_grpc.add_HelloServicer_to_server(
            await app_scope.resolve(HelloServicer), server
        )

        server.add_insecure_port("localhost:50051")
        await server.start()
        try:
            yield server
        finally:
            await server.stop(grace=None)


async def run_server() -> None:
    async with create_server() as server:
        await server.wait_for_termination()
