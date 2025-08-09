# Pytest configuration for this repo
# Ignore incomplete or WIP test files from collection
collect_ignore = [
    "test_mcp_server.py",  # WIP/incomplete
]

# Suppress deprecation noise from FastMCP bearer provider during tests
import warnings
warnings.filterwarnings(
    "ignore",
    message=r"The `fastmcp\.server\.auth\.providers\.bearer` module is deprecated.*",
    category=DeprecationWarning,
)
