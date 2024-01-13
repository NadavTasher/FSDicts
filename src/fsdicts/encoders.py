import json

# Create default encoding
ENCODING = "utf-8"

# Create encoder tuples
JSON = (lambda value: json.dumps(value).encode(ENCODING), json.loads)
PYTHON = (lambda value: repr(value).encode(ENCODING), eval)