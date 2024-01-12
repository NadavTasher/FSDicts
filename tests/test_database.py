import pytest
import tempfile

from fsdicts import *

def test_read_write():
	# Create database
	d = Database(tempfile.mktemp())
	
	# Write the Hello value
	d["Hello"] = "World"

	# Read the Hello value
	assert d["Hello"] == "World"

def test_write_recursive_dicts():
	# Create database
	d = Database(tempfile.mktemp())
	
	# Write the Hello value
	d["Hello"] = {
		"World": 42
	}

	# Read the Hello value
	assert d["Hello"] == dict(World=42)

	# Make sure the Hello value is a dictionary
	assert isinstance(d["Hello"], Dictionary)

def test_unuse_storage_usage():
	# Create database
	d = Database(tempfile.mktemp())
	
	# Write the Hello value
	d["Hello"] = {
		"World": {
			"Another": "Value"
		}
	}

	# Make sure the storage usage is NOT zero
	assert os.listdir(d._key_storage._path)

	# Clear the database
	d.clear()

	# Make sure the database is empty
	assert len(d) == 0
	
	# Make sure the storage usage is zero
	assert not os.listdir(d._key_storage._path)