from app.conf.environ import env


SEARCH_SIMILARITY_THRESHOLD = env("SEARCH_SIMILARITY_THRESHOLD", cast=float, default=0.25)
SEARCH_SHORT_QUERY_LENGTH = env("SEARCH_SHORT_QUERY_LENGTH", cast=int, default=2)
