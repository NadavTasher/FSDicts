import os
import hashlib

class ObjectStorage(object):

	def __init__(self, path, hash=hashlib.md5):
		# Intialize the path and hash
		self._path = path
		self._hash = hash

		# Create the path if needed
		if not os.path.exists(self._path):
			os.makedirs(self._path)

	def put(self, value, validate=True):
		# Create the value hash
		hash = self._hash(value).hexdigest()

		# Create the object path
		path = os.path.join(self._path, hash)

		# Check whether the path exists
		if os.path.isfile(path):
			# Check if validation should be skipped
			if not validate:
				return
			
			# Read the file from the path
			with open(path, "rb") as object:
				# Validate the hash by reading the object
				if hash == self._hash(object.read()).hexdigest():
					return

		# TODO write object

	def get(self, hash, validate=False):
		# Create the object path
		path = os.path.join(self._path, hash)

		# Check whether the path exists
		if not os.path.isfile(path):
			raise KeyError(hash)
		
		# Read the file from the path
		with open(path, "rb") as object:
			value = object.read()

		# Check the hash against the real calculation
		if validate and hash != self._hash(value).hexdigest():
			# Delete the bad object
			os.remove(path)

			# Raise the value error
			raise ValueError(hash)

		# Return the value
		return value

	def has(self, hash):
		# Create the object path
		path = os.path.join(self._path, hash)

		# Check whether the file exists
		return os.path.isfile(path)

	def has_object_by_value(self, value):
		pass

	def purge_stale_objects(self):
		pass