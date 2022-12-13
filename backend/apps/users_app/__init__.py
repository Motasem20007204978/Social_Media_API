from prometheus_client import Counter


name = "django_http_requests"
docs = "number of http requests received by django server"
REQUESTS_COUNTER = Counter(name=name, documentation=docs)
