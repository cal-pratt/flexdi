import threading

from flask import Flask, Response, jsonify

from flexdi.flask import FlaskGraph

app = Flask(__name__)
graph = FlaskGraph(app)


@graph.bind
class Foo:
    def __init__(self) -> None:
        self.thread_id = threading.get_ident()


@app.get("/sync")
def sync_endpoint(foo: Foo) -> Response:
    thread_id = threading.get_ident()
    return jsonify([foo.thread_id, thread_id])


@app.get("/async")
async def async_endpoint(foo: Foo) -> Response:
    thread_id = threading.get_ident()
    return jsonify([foo.thread_id, thread_id])
