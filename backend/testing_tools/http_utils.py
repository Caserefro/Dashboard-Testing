import os
from typing import Dict, Any, Optional

def resolve_ssl_verify(payload: Optional[Dict[str, Any]] = None) -> bool:
    """
    Standardized helper for bypassing corporate SSL proxies in testing tools.
    Reads from the optional execution payload or the machine environment.
    """
    if payload is None:
        payload = {}
        
    # Payload explicit takes precedence over environment variable
    if "ssl_verify" in payload:
        return bool(payload["ssl_verify"])
    if "sslVerify" in payload:
        return bool(payload["sslVerify"])
        
    env_override = os.environ.get("ATLAS_SSL_VERIFY")
    if env_override is not None:
        return env_override.lower() in ("true", "1", "yes")
        
    return True
