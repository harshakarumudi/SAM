from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter based on client remote IP
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
