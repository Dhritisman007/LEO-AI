from duckduckgo_search import DDGS


def web_search(query: str) -> dict:
    """Search the web using DuckDuckGo full text search."""
    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=5))

        if not raw_results:
            # Fallback: try a broader query
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query + " site:wikipedia.org OR site:espn.com OR site:bbc.com", max_results=5))

        if not raw_results:
            return {"success": False, "error": "No results found", "query": query}

        results = []
        for r in raw_results:
            results.append({
                "title": r.get("title", ""),
                "snippet": r.get("body", ""),
                "url": r.get("href", ""),
            })

        return {"success": True, "query": query, "results": results}

    except Exception as e:
        return {"success": False, "error": str(e), "query": query}
