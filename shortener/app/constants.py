# URL Generation
NANOSECONDS_MULTIPLIER = 1_000_000
SHORT_URL_LENGTH = 8

# Rate Limiting
CLEANUP_MAX_AGE_SECONDS = 3600
DIRECTORY_SEARCH_DEPTH = 10

# Trusted Proxy Networks
TRUSTED_PROXY_NETWORKS = [
    "127.0.0.0/8",  # localhost
    "10.0.0.0/8",  # private networks
    "172.16.0.0/12",  # private networks
    "192.168.0.0/16",  # private networks
    "169.254.0.0/16",  # link-local
]

# Cache Configuration
CACHE_TTL_SECONDS = 300  # 5 minutes

# gRPC Client Timeouts and Retries
GRPC_TIMEOUT_SECONDS = 5.0
GRPC_MAX_RETRIES = 3
GRPC_RETRY_DELAY_SECONDS = 1.0
GRPC_BACKOFF_MULTIPLIER = 2.0
