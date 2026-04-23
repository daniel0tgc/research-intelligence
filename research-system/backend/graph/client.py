from contextlib import asynccontextmanager
from neo4j import AsyncGraphDatabase
from backend.config import settings

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _driver


@asynccontextmanager
async def get_session():
    driver = get_driver()
    async with driver.session() as session:
        yield session


async def close_driver() -> None:
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
