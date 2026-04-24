import sys
import asyncio

from fastmcp import FastMCP
from loguru import logger

from .config import get_settings
from .vais import VaisError, call_vais

settings = get_settings()

logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


mcp = FastMCP(
    name="Vertex AI Search MCP",
    description="Vertex AI Search MCP server",
    log_level=settings.LOG_LEVEL,
)


@mcp.tool()
async def search_vais(
    search_query: str,
) -> dict:
    logger.info(f"Received search request with query: '{search_query}'")
    if not search_query:
        logger.warning("Search query is empty.")
        return {"response": "No search query provided"}

    try:
        # 複数ユーザの同時リクエスト時にイベントループがブロックされないように、
        # 同期関数である call_vais を別スレッドにオフロードして実行します。
        response_data = await asyncio.to_thread(
            call_vais,
            search_query=search_query,
            google_cloud_project_id=settings.GOOGLE_CLOUD_PROJECT_ID,
            impersonate_service_account=settings.IMPERSONATE_SERVICE_ACCOUNT,
            vais_engine_id=settings.VAIS_ENGINE_ID,
            vais_location=settings.VAIS_LOCATION,
            page_size=settings.PAGE_SIZE,
            max_extractive_segment_count=settings.MAX_EXTRACTIVE_SEGMENT_COUNT,
        )
        logger.info(f"Search request successful, returning {len(response_data)} items.")
        return {"response": response_data}
    except VaisError as e:
        logger.error(f"Error processing search request: {e}")
        return {"error": str(e), "status_code": 500}


def main():
    logger.info("Starting FastMCP server.")
    if settings.MCP_TRANSPORT == "sse":
        logger.info(f"Starting in SSE mode on {settings.MCP_HOST}:{settings.MCP_PORT}")
        mcp.run(transport="sse", host=settings.MCP_HOST, port=settings.MCP_PORT)
    else:
        logger.info("Starting in stdio mode")
        mcp.run()


if __name__ == "__main__":
    main()