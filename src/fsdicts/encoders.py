import json

# Create default encoding
ENCODING = "utf-8"

# Create JSON encoder
JSON_ENCODE = lambda value: json.dumps(value).encode(ENCODING)
JSON_DECODE = lambda value: json.loads(value)

# Create Python encoder
PYTHON_ENCODE = lambda value: repr(value).encode(ENCODING)
PYTHON_DECODE = lambda value: eval(value)

# Create encoder tuples
JSON = (JSON_ENCODE, JSON_DECODE)
PYTHON = (PYTHON_ENCODE, PYTHON_DECODE)