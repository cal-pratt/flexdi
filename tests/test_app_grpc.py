import grpc.aio
import pytest

from .test_app import app_grpc
from .test_app.protos import hello_pb2 as hello
from .test_app.protos import hello_pb2_grpc as hello_grpc


@pytest.mark.asyncio
async def test_standard_command() -> None:
    async with app_grpc.create_server():
        async with grpc.aio.insecure_channel("localhost:50051") as channel:
            stub = hello_grpc.HelloStub(channel)
            val: hello.HelloReply = await stub.SayHello(hello.HelloRequest(name="foo"))
            assert val.message == "Hello foo"


@pytest.mark.asyncio
async def test_override_command() -> None:
    with app_grpc.graph.override():
        app_grpc.graph.bind_instance(app_grpc.HelloPrefix("Override "))
        async with app_grpc.create_server():
            async with grpc.aio.insecure_channel("localhost:50051") as channel:
                stub = hello_grpc.HelloStub(channel)
                val: hello.HelloReply = await stub.SayHello(
                    hello.HelloRequest(name="foo")
                )
                assert val.message == "Override foo"
