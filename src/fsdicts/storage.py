import os
import hashlib
import binascii

class Storage(object):

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
				return path
			
			# Read the file from the path
			with open(path, "rb") as object:
				object_value = object.read()
			
			# Validate the hash by reading the object
			if hash == self._hash(object_value).hexdigest():
				return path
			
		# Create temporary path for writing
		temporary = path + "." + binascii.b2a_hex(os.urandom(4)).decode()

		# Write the object
		with open(temporary, "wb") as object:
			object.write(value)

		# Rename the temporary file
		os.rename(temporary, path)

		# Return the hash
		return path

	def release(self, link):
		# Check whether the path exists
		if not os.path.isfile(link):
			raise ValueError(link)
		
		# Read the link and create hash
		with open(link, "rb") as object:
			object_value = object.read()

		# Create object hash
		object_hash = self._hash(object_value).hexdigest()
		
		# Remove the link
		os.unlink(link)

		# Create object path
		path = os.path.join(self._path, object_hash)

		# Clean the path
		self.clean(path)
		
	def purge(self):
		# List all files in the storage and check the link count
		for hash in os.listdir(self._path):
			# Create the file path
			path = os.path.join(self._path, hash)

			# If path does not exist, skip
			if not os.path.isfile(path):
				continue

			# Clean the file
			self.clean(path)

	def clean(self, path):
		# Make sure the path exists
		if not os.path.isfile(path):
			raise ValueError(path)
		
		# If more then one link exists, skip
		if os.stat(path).st_nlink > 1:
			return
		
		# Remove the file
		os.remove(path)
