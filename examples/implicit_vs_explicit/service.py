from sqlalchemy.ext.asyncio import AsyncConnection


class QueryService:
    def __init__(self, conn: AsyncConnection) -> None:
        self.conn = conn

    async def query(self) -> str:
        ...
