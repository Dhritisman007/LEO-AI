import httpx

def web_search(query: str) -> dict:
    """Search the web using DuckDuckGo (free, no API key needed)."""
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }
        response = httpx.get(url, params=params, timeout=10)
        data = response.json()

        results = []

        # Abstract (main answer)
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", ""),
                "snippet": data.get("Abstract", ""),
                "url": data.get("AbstractURL", ""),
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:4]:
            if "Text" in topic:
                results.append({
                    "title": topic.get("Text", "")[:60],
                    "snippet": topic.get("Text", ""),
                    "url": topic.get("FirstURL", ""),
                })

        if not results:
            return {"success": False, "error": "No results found", "query": query}

        return {"success": True, "query": query, "results": results}

    except Exception as e:
        return {"success": False, "error": str(e)}
