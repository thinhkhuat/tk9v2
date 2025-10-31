# Network Reliability Fixes for Deep Research MCP

## Problem Summary

The deep research system was experiencing critical network failures that interrupted research operations:

### Issues Identified
- **HTTPSConnectionPool timeout errors** with 4-second timeout (too short)
- **Connection reset by peer** errors indicating network instability  
- **Content too short or empty** responses from failed requests
- **Poor error handling** for connection failures

### Error Examples
```
Error! : HTTPSConnectionPool(host='www.washingtonpost.com', port=443): Read timed out. (read timeout=4)
Content too short or empty for https://www.washingtonpost.com/opinions/2025/08/01/trump-tarrifs-supreme-court-constitution/
Error! : ('Connection aborted.', ConnectionResetError(54, 'Connection reset by peer'))
Content too short or empty for https://www.nytimes.com/live/2025/08/29/us/trump-news
```

## Root Cause Analysis

Located the source of 4-second timeout in gpt-researcher package:

- `/opt/homebrew/lib/python3.11/site-packages/gpt_researcher/scraper/beautiful_soup/beautiful_soup.py:24`
- `/opt/homebrew/lib/python3.11/site-packages/gpt_researcher/scraper/tavily_extract/tavily_extract.py:44` 
- `/opt/homebrew/lib/python3.11/site-packages/gpt_researcher/scraper/firecrawl/firecrawl.py:67`

All contained: `self.session.get(self.link, timeout=4)`

## Solutions Implemented

### 1. Direct Source Code Patches

**File**: `direct_timeout_patch.py`

- **Automatically patches** gpt-researcher installation files
- **Changes timeout=4 to timeout=30** in all scraper modules
- **Adds retry logic** with exponential backoff
- **Creates backups** before making changes
- **Provides restoration** capability if needed

### 2. Runtime Network Enhancement

**File**: `network_reliability_patch.py`

- **Robust session creation** with connection pooling
- **Retry strategy** with exponential backoff
- **Enhanced error handling** for connection resets
- **Browser-like headers** to prevent blocking
- **Global session defaults** improvement

### 3. System Integration

**Modified**: `main.py`

- **Early integration** before gpt-researcher imports
- **Automatic patch application** on system startup
- **Fallback handling** for different import contexts
- **Error reporting** with manual fix instructions

## Technical Details

### Timeout Configuration
```python
# Before: timeout=4 (too short)
response = self.session.get(self.link, timeout=4)

# After: timeout=30 (reasonable)
response = self.session.get(self.link, timeout=30)
```

### Retry Logic
```python
retry_strategy = Retry(
    total=3,                    # 3 total retry attempts
    read=3,                     # 3 read retries
    connect=3,                  # 3 connection retries
    backoff_factor=1.5,         # Exponential backoff
    status_forcelist=[500, 502, 503, 504, 429, 408]  # Retry on these status codes
)
```

### Connection Pooling
```python
adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=10,        # Pool size
    pool_maxsize=20            # Max connections per pool
)
```

### Enhanced Headers
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    # ... additional headers to appear more browser-like
}
```

## Files Created/Modified

### New Files
- `network_reliability_patch.py` - Runtime network enhancements
- `direct_timeout_patch.py` - Direct source code patching
- `test_network_fix.py` - Comprehensive testing suite
- `NETWORK_RELIABILITY_FIXES.md` - This documentation

### Modified Files
- `main.py` - Integrated network patches into startup sequence

### Backup Files Created
- `/opt/homebrew/lib/python3.11/site-packages/gpt_researcher/scraper/beautiful_soup/beautiful_soup.py.timeout_patch_backup`
- `/opt/homebrew/lib/python3.11/site-packages/gpt_researcher/scraper/tavily_extract/tavily_extract.py.timeout_patch_backup`
- `/opt/homebrew/lib/python3.11/site-packages/gpt_researcher/scraper/firecrawl/firecrawl.py.timeout_patch_backup`

## Usage

### Automatic Application
The network reliability fixes are automatically applied when running:
```bash
python main.py
```

### Manual Application  
To apply patches manually:
```bash
python direct_timeout_patch.py
```

### Restoration
To restore original files:
```bash
python direct_timeout_patch.py --restore
```

### Testing
To test network improvements:
```bash
python test_network_fix.py
```

## Benefits Achieved

- ✅ **Increased timeout** from 4s to 30s (750% improvement)
- ✅ **Retry logic** with up to 3 attempts and exponential backoff
- ✅ **Connection pooling** for better resource management  
- ✅ **Enhanced error handling** for connection resets
- ✅ **Browser-like headers** to prevent blocking
- ✅ **Automatic backup/restore** capability
- ✅ **Comprehensive testing** suite
- ✅ **System integration** with fallback handling

## Monitoring

The system now provides detailed logging for network operations:
- Connection attempt tracking
- Retry logic execution
- Timeout and error reporting
- Patch application status

## Maintenance

### Updating gpt-researcher
If gpt-researcher is updated, re-run the patches:
```bash
python direct_timeout_patch.py
```

### Checking Patch Status
Verify timeout values:
```bash
grep -n "timeout=30" /opt/homebrew/lib/python3.11/site-packages/gpt_researcher/scraper/*/*.py
```

### Log Analysis
Monitor network issues in application logs:
- Look for "Attempting to fetch" messages
- Check retry attempt counts
- Review timeout and connection errors

## Performance Impact

- **Positive**: Reduced failed requests, more reliable data collection
- **Minimal**: Slight increase in request latency due to longer timeouts
- **Beneficial**: Connection pooling reduces overhead for multiple requests

## Security Considerations

- **Headers**: Enhanced to appear more like legitimate browser requests
- **Retry Logic**: Includes backoff to avoid overwhelming servers
- **Connection Pooling**: Proper resource management and connection reuse
- **Backup Strategy**: Original files preserved for easy restoration

## Future Improvements

Consider implementing:
- **Circuit breaker pattern** for failing endpoints
- **Request rate limiting** to be more respectful to target sites
- **Dynamic timeout adjustment** based on response times
- **Health monitoring** for network reliability metrics
- **Caching layer** to reduce duplicate requests

## Troubleshooting

### Common Issues

**Patches not applied:**
- Check file permissions on gpt-researcher installation
- Run with appropriate privileges
- Verify gpt-researcher installation path

**Import errors:**
- Ensure all files are in the correct directory
- Check Python path configuration
- Verify module dependencies

**Network still failing:**
- Check firewall/proxy settings
- Verify DNS resolution
- Test with different networks
- Review target site blocking policies

### Support

For issues or improvements, check:
1. Application logs for detailed error information
2. Test suite results: `python test_network_fix.py`
3. Manual patch application: `python direct_timeout_patch.py`
4. Backup restoration: `python direct_timeout_patch.py --restore`