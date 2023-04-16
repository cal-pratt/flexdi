import sys

from flexdi import FlexGraph

graph = FlexGraph()


@graph.bind
class ApiClient:
    def foo(self) -> str:
        return "foo"


@graph.entrypoint
def main(client: ApiClient) -> None:
    print(client.foo())


if __name__ == "__main__":
    sys.exit(main())
