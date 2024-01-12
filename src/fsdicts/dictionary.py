import os
import hashlib
import binascii

from fsdicts.mapping import AdvancedMutableMapping, Mapping
from fsdicts.encoders import JSON

# Default encoding for text
ENCODING = "utf-8"

# Create key and value prefixes
PREFIX_KEY = "key-"
PREFIX_VALUE = "value-"

class Dictionary(AdvancedMutableMapping):

	def __init__(self, path, storage, encoder=JSON):
		# Make sure path exists
		if not os.path.exists(path):
			os.makedirs(path)

		# Set internal variables
		self._path = path
		self._encode, self._decode = encoder
		self._key_storage, self._value_storage = storage
		
	def _create_paths(self, key):
		# Hash the key using hashlib
		checksum = hashlib.md5(self._encode(key)).hexdigest()

		# Create both paths
		return os.path.join(self._path, PREFIX_KEY + checksum), os.path.join(self._path, PREFIX_VALUE + checksum)

	def __getitem__(self, key):
		# Make sure key exists
		if key not in self:
			raise KeyError(key)

		# Resolve key and value paths
		_, value_path = self._create_paths(key)

		# Check if object is a simple object
		if os.path.isdir(value_path):
			# Create a keystore from the path
			return Dictionary(value_path, (self._key_storage, self._value_storage), (self._encode, self._decode))

		# Read the object value
		with open(value_path, "rb") as object:
			value = object.read()

		# Decode the value
		return self._decode(value)

	def __setitem__(self, key, value):
		# Delete the old value
		if key in self:
			del self[key]

		# Create the key and value paths
		key_path, value_path = self._create_paths(key)
		
		# Encode the key
		encoded_key = self._encode(key)

		# Store the key in the object storage
		key_hash = self._key_storage.put(encoded_key)

		# Link the key to the translation
		self._key_storage.use(key_hash, key_path)

		# Check if value is a dictionary
		if isinstance(value, Mapping):
			# Create the sub-dictionary
			dictionary = Dictionary(value_path, (self._key_storage, self._value_storage), (self._decode, self._encode))

			# Update the dictionary with the values
			dictionary.update(value)

			# Return - nothing more to do
			return
		
		# Encode the value
		encoded_value = self._encode(value)

		# Store the value in the object storage
		value_hash = self._value_storage.put(encoded_value)

		# Link the value to the translation
		self._value_storage.use(value_hash, value_path)

	def __delitem__(self, key):
		# Make sure key exists
		if key not in self:
			raise KeyError(key)

		# Resolve key and value paths
		key_path, value_path = self._create_paths(key)

		# Un-use the key object
		self._key_storage.unuse(key_path)

		# If the value is a dictionary, clear the dictionary
		if os.path.isdir(value_path):
			# Create the dictionary
			dictionary = Dictionary(value_path, (self._key_storage, self._value_storage), (self._encode, self._decode))

			# Clear the dictionary
			dictionary.clear()

			# Delete the directory - should be empty
			os.rmdir(value_path)

			# Return - nothing more to do
			return
		
		# Un-use the value object
		self._value_storage.unuse(value_path)

	def __contains__(self, key):
		# Resolve key and value paths
		key_path, value_path = self._create_paths(key)

		# Check if paths exist
		return os.path.exists(key_path) and os.path.exists(value_path)

	def __iter__(self):
		# List all of the items in the path
		for name in os.listdir(self._path):
			# Make sure name starts with key prefix
			if not name.startswith(PREFIX_KEY):
				continue

			# Read the key contents
			with open(os.path.join(self._path, name), "rb") as object:
				encoded_key = object.read()

			# Decode the key and yield
			yield self._decode(encoded_key)

	def __len__(self):
		# Count all non-temporary names
		return len([name for name in os.listdir(self._path) if name.startswith(PREFIX_KEY)])


