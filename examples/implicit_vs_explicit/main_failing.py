from database import provide_connection, provide_engine
from service import QueryService

from flexdi import FlexGraph

graph = FlexGraph()

graph.bind(provide_engine)
graph.bind(provide_connection)


# Fails with:
#   flexdi.errors.ImplicitBindingError:
#     Requested a binding for <class 'service.QueryService'>
#     that was not explicitly marked for binding.
@graph.entrypoint
async def main(service: QueryService) -> None:
    print(await service.query())


if __name__ == "__main__":
    main()
