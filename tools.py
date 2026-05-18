from ddgs import DDGS

def web_search(query: str) -> list[dict]:
    return DDGS().text(query, max_results=3)

