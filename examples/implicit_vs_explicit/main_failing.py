from database import provide_connection, provide_engine
from service import QueryService

from flexdi import FlexGraph

graph = FlexGraph()

graph.bind(provide_engine)
graph.bind(provide_connection)


# Oops, we didn't bind the QueryService!
@graph.entrypoint
async def main(service: QueryService) -> None:
    print(await service.query())


if __name__ == "__main__":
    main()
