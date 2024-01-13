import pytest
import datetime

from fsdicts import *


@pytest.mark.parametrize("encoder", [PYTHON, JSON])
@pytest.mark.parametrize("value", ["Hello", 10, True, None, {"Hello": "World"}, ["Hello", "World"]])
def test_generic_encode_decode(encoder, value):
    # Untuple encoder
    encode, decode = encoder

    # Try encoding the value
    encoded_value = encode(value)

    # Make sure the encoded value is of type bytes
    assert isinstance(encoded_value, bytes)

    # Decode the value
    decoded_value = decode(encoded_value)

    # Make sure the decoded value equals the original value
    assert decoded_value == value


@pytest.mark.parametrize("value", [b"Hello", "World", ("Hello", "World"), datetime.datetime.now()])
def test_python_encode_decode(value):
    test_generic_encode_decode(PYTHON, value)
