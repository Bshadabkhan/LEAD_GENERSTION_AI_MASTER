from crewai.tools import tool
from exa_py import Exa
import os

exa_api_key = os.getenv("EXA_API_KEY")

@tool("Exa Search")
def exa_search_tool(query: str) -> str:
    """Search and get contents using Exa's semantic search. 
    Useful for finding up-to-date information about companies and market research.
    
    Args:
        query: The search query to execute
        
    Returns:
        Formatted search results with titles, URLs, and highlights
    """
    exa = Exa(exa_api_key)

    response = exa.search_and_contents(
        query,
        type="neural",
        use_autoprompt=True,
        num_results=3,
        highlights=True
    )

    parsedResult = '\n'.join([
        f'Title: {eachResult.title}\n'
        f'URL: {eachResult.url}\n'
        f'Highlights: {"".join(eachResult.highlights)}\n'
        for idx, eachResult in enumerate(response.results)
    ])
    
    return parsedResult