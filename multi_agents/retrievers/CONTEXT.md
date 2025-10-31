# Custom Retrievers - Feature Documentation

## Purpose

Custom search retriever implementations that integrate with gpt-researcher to provide optimized web search capabilities. Primary focus on BRAVE Search integration with fallback support for other providers.

## Retriever Architecture

### Base Retriever Interface
```python
class BaseRetriever(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Execute search query

        Returns:
            List of search results with:
            - url: str
            - title: str
            - description: str
            - content: str (optional)
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Return retriever name for logging"""
        pass
```

## BRAVE Search Integration

### Custom BRAVE Retriever (`retrievers/brave_retriever.py`)
**Purpose**: Optimized BRAVE Search API integration

**Configuration**:
```python
# Environment variables
BRAVE_API_KEY=your_brave_api_key
RETRIEVER=custom
RETRIEVER_ENDPOINT=https://brave-local-provider.local

# Code configuration
retriever = BraveRetriever(
    api_key=os.getenv("BRAVE_API_KEY"),
    max_results=10,
    safe_search="moderate"
)
```

**API Integration**:
```python
class BraveRetriever(BaseRetriever):
    API_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"

    async def search(self, query: str, max_results: int = 10):
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                self.API_ENDPOINT,
                params={
                    "q": query,
                    "count": max_results,
                    "safesearch": "moderate"
                },
                headers={
                    "X-Subscription-Token": self.api_key,
                    "Accept": "application/json"
                }
            )
            data = await response.json()
            return self._parse_results(data)

    def _parse_results(self, data: Dict) -> List[Dict]:
        """Convert BRAVE API response to standard format"""
        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "url": item["url"],
                "title": item["title"],
                "description": item.get("description", ""),
                "published_date": item.get("age"),
                "relevance_score": item.get("meta_url", {}).get("score")
            })
        return results
```

### Integration with gpt-researcher

**Setup Pattern**:
```python
# In main.py or multi_agents/main.py
if os.getenv('PRIMARY_SEARCH_PROVIDER') == 'brave':
    from simple_brave_retriever import setup_simple_brave_retriever
    setup_simple_brave_retriever()
```

**Registration**:
```python
def setup_simple_brave_retriever():
    """Register BRAVE retriever with gpt-researcher"""
    from gpt_researcher.retrievers import register_retriever

    register_retriever('brave', BraveRetriever)
```

## Retriever Features

### 1. Result Filtering
```python
def filter_results(
    results: List[Dict],
    min_relevance: float = 0.5,
    exclude_domains: List[str] = None
) -> List[Dict]:
    """Filter search results by relevance and domain"""
    filtered = []
    for result in results:
        # Relevance filtering
        if result.get("relevance_score", 1.0) < min_relevance:
            continue

        # Domain filtering
        domain = urlparse(result["url"]).netloc
        if exclude_domains and domain in exclude_domains:
            continue

        filtered.append(result)

    return filtered
```

### 2. Result Ranking
```python
def rank_results(results: List[Dict]) -> List[Dict]:
    """Re-rank results by multiple factors"""
    def score(result):
        factors = [
            result.get("relevance_score", 0.5),
            recency_score(result.get("published_date")),
            domain_authority_score(result["url"])
        ]
        return sum(factors) / len(factors)

    return sorted(results, key=score, reverse=True)
```

### 3. Content Extraction
```python
async def extract_content(url: str) -> Optional[str]:
    """Extract main content from URL"""
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(url, timeout=30)
            html = await response.text()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')

            # Extract main content
            content = extract_main_text(soup)

            return content
    except Exception as e:
        logger.error(f"Content extraction failed for {url}: {e}")
        return None
```

### 4. Caching
```python
class CachedRetriever(BaseRetriever):
    """Retriever with result caching"""

    def __init__(self, retriever: BaseRetriever, cache_ttl: int = 3600):
        self.retriever = retriever
        self.cache = {}
        self.cache_ttl = cache_ttl

    async def search(self, query: str, max_results: int = 10):
        cache_key = f"{query}:{max_results}"

        # Check cache
        if cache_key in self.cache:
            cached_time, results = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return results

        # Cache miss - execute search
        results = await self.retriever.search(query, max_results)

        # Update cache
        self.cache[cache_key] = (time.time(), results)

        return results
```

## Development Patterns

### Adding New Retriever
1. **Implement BaseRetriever**:
   ```python
   class NewRetriever(BaseRetriever):
       async def search(self, query, max_results):
           # Implementation
           pass

       def get_source_name(self):
           return "new_retriever"
   ```

2. **Register with gpt-researcher**:
   ```python
   from gpt_researcher.retrievers import register_retriever
   register_retriever('new', NewRetriever)
   ```

3. **Configure Environment**:
   ```bash
   PRIMARY_SEARCH_PROVIDER=new
   NEW_API_KEY=your_key
   ```

### Testing Retrievers
```python
async def test_retriever():
    retriever = BraveRetriever(api_key="test_key")

    results = await retriever.search("AI trends", max_results=5)

    assert len(results) <= 5
    assert all("url" in r for r in results)
    assert all("title" in r for r in results)
```

## Performance Considerations

### Latency
- **BRAVE Search**: ~300ms average
- **Tavily**: ~400ms average
- **Google**: ~500ms average
- **Caching**: < 10ms for cache hits

### Rate Limits
- **BRAVE**: 15,000 queries/month (free tier)
- **Tavily**: Varies by plan
- **Google**: 100 queries/day (free tier)

### Optimization Strategies
1. **Parallel Queries**: Use `asyncio.gather()` for multiple sections
2. **Result Caching**: Cache results for repeated queries
3. **Batch Processing**: Group similar queries when possible
4. **Failover**: Automatic switch to fallback provider on rate limit

## Common Issues

### Issue: API Key Invalid
**Symptom**: 401 Unauthorized errors
**Solution**: Verify API key in `.env` file
```bash
# Check configuration
python main.py --config

# Verify API key format
echo $BRAVE_API_KEY
```

### Issue: Rate Limit Exceeded
**Symptom**: 429 Too Many Requests
**Solution**: Configure failover provider
```bash
PRIMARY_SEARCH_PROVIDER=brave
FALLBACK_SEARCH_PROVIDER=tavily
SEARCH_STRATEGY=fallback_on_error
```

### Issue: Slow Search Performance
**Symptom**: Search takes > 5 seconds
**Solution**:
- Reduce max_results
- Enable caching
- Use faster provider (BRAVE recommended)

## Cross-References

- **[Provider System](/multi_agents/providers/CONTEXT.md)** - Provider abstraction
- **[Multi-Agent System](/multi_agents/CONTEXT.md)** - Retriever usage
- **[BRAVE Search Integration](/docs/MULTI_AGENT_BRAVE_SEARCH_INTEGRATION.md)** - Detailed BRAVE setup

---

*For retriever implementation details, see `retrievers/brave_retriever.py`. For gpt-researcher integration, see `simple_brave_retriever.py`.*
