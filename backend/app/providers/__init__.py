import asyncio

from .ai_provider import ModelResponse, AIProvider, AIRegistry
from .llamacpp.llamacpp_provider import LlamacppProvider, LlamacppEmbedProvider
from .image_gen import SDCppProvider
from .web_search_provider import WebSearchProvider, WebSearchRegistry, DDGSWebSearch
from .web_fetch_provider import (
    WebFetchResponse,
    WebFetchProvider,
    WebFetchRegistry,
    TrafilaturaWebFetch
)
from .tool_provider import (
    Tool,
    ToolRegistry,
    RagTool,
    SummarizeTool,
    WebSearchTool,
    WebFetchTool,
    ImageGenTool
)
from .tts import *
from .stt import *
from .mcp_provider import MCPClientProvider, MCPClientRegistry

async def bootstrap():
    # AI Registry
    ai_registry = AIRegistry()

    ai_registry.register(
        LlamacppProvider()
    )
    ai_registry.register(
        LlamacppEmbedProvider()
    )
    ai_registry.register(
        SDCppProvider()
    )

    # TTS Registry
    tts_registry = TTSRegistry()

    tts_registry.register(
        KittenttsProvider()
    )

    # STT Registry
    stt_registry = STTRegistry()

    stt_registry.register(
        WhispercppProvider()
    )

    # Web Search Engine Register
    search_registry = WebSearchRegistry()

    search_registry.register(
        DDGSWebSearch()
    )

    # Web Fetch Engine Register
    fetch_registry = WebFetchRegistry()

    fetch_registry.register(
        TrafilaturaWebFetch()
    )

    # Tool Resgistry
    tool_registry = ToolRegistry()

    tool_registry.register(
        RagTool()
    )
    tool_registry.register(
        SummarizeTool()
    )
    tool_registry.register(
        WebSearchTool()
    )
    tool_registry.register(
        WebFetchTool()
    )
    tool_registry.register(
        ImageGenTool()
    )

    # MCP Client Register
    await MCPClientRegistry().warmup()

asyncio.run(bootstrap())
