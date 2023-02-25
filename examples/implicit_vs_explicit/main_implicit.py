from database import provide_connection, provide_engine
from service_implicit import QueryService

from flexdi import FlexGraph

graph = FlexGraph()

graph.bind(provide_engine)
graph.bind(provide_connection)


# QueryService is marked with `@implicitbinding` meaning that the
# graph will accept it and register it as a dependency when requested!
@graph.entrypoint
async def main(service: QueryService) -> None:
    print(await service.query())


if __name__ == "__main__":
    main()
