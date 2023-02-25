import threading

from fastapi import FastAPI

from flexdi.fastapi import FastAPIGraph, FlexDepends

app = FastAPI()
graph = FastAPIGraph(app)


@graph.bind(eager=True)
class Foo:
    def __init__(self) -> None:
        self.thread_id = threading.get_ident()


@app.get("/sync")
def sync_endpoint(foo: Foo = FlexDepends(Foo)) -> list[int]:
    thread_id = threading.get_ident()
    return [foo.thread_id, thread_id]


@app.get("/async")
async def async_endpoint(foo: Foo = FlexDepends(Foo)) -> list[int]:
    thread_id = threading.get_ident()
    return [foo.thread_id, thread_id]
