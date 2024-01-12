import pytest
import tempfile

from fsdicts import *

def test_storage_creation():
	s = Storage(tempfile.mktemp())
	s.put(b"Hello")
	s.purge()
