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
				return hash
			
			# Read the file from the path
			with open(path, "rb") as object:
				object_value = object.read()
			
			# Validate the hash by reading the object
			if hash == self._hash(object_value).hexdigest():
				return hash

		# Write the object
		with open(path, "wb") as object:
			object.write(value)

		# Return the hash
		return hash

	def get(self, hash, validate=False):
		# Create the object path
		path = os.path.join(self._path, hash)

		# Check whether the path exists
		if not os.path.isfile(path):
			raise KeyError(hash)
		
		# Read the file from the path
		with open(path, "rb") as object:
			object_value = object.read()

		# Check the hash against the real calculation
		if validate and hash != self._hash(object_value).hexdigest():
			# Delete the bad object
			os.remove(path)

			# Raise the value error
			raise ValueError(hash)

		# Return the value
		return object_value

	def has(self, hash):
		# Create the object path
		path = os.path.join(self._path, hash)

		# Check whether the file exists
		return os.path.isfile(path)
	
	def use(self, hash, destination):
		# Create the object path
		path = os.path.join(self._path, hash)

		# Check whether the path exists
		if not os.path.isfile(path):
			raise KeyError(hash)
		
		# Make sure the destination does not exist
		if os.path.islink(destination):
			os.unlink(destination)

		# Create the link
		os.link(path, destination)
		
	def purge(self):
		# List all files in the storage and check the link count
		for hash in os.listdir(self._path):
			pass