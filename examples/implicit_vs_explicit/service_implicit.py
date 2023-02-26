from sqlalchemy.ext.asyncio import AsyncConnection

from flexdi import implicitbinding


@implicitbinding
class QueryService:
    def __init__(self, conn: AsyncConnection) -> None:
        self.conn = conn

    async def query(self) -> str:
        ...
