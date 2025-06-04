
from typing import Dict, Callable, Any, List


_CRAWLER_REGISTRY: Dict[str, Callable[[], Any]] = {}

def register_crawler(name: str) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
    """
    Decorator to register a crawler function with a given name.
    
    Args:
        name: The name to register the crawler function under.
        
    Returns:
        A decorator function that registers the crawler function.
        
    Raises:
        ValueError: If a crawler with the given name already exists.
    """
    def decorator(fn: Callable[[], Any]) -> Callable[[], Any]:
        if name in _CRAWLER_REGISTRY:
            raise ValueError(f"Crawler with name {name} already exists")
        _CRAWLER_REGISTRY[name] = fn
        return fn
    return decorator

def get_crawler(name: str) -> Callable[[], Any]:
    """
    Get a crawler function by name.
    
    Args:
        name: The name of the crawler function to get.
        
    Returns:
        The crawler function registered under the given name.
        
    Raises:
        ValueError: If no crawler with the given name exists.
    """
    if name not in _CRAWLER_REGISTRY:
        raise ValueError(f"Crawler {name} not found. Available crawlers: {list(_CRAWLER_REGISTRY.keys())}")
    return _CRAWLER_REGISTRY[name]

def get_crawlers() -> Dict[str, Callable[[], Any]]:
    """
    Get all registered crawler functions.
    
    Returns:
        A dictionary mapping crawler names to crawler functions.
    """
    return _CRAWLER_REGISTRY