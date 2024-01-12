import os

from fsdicts.storage import Storage
from fsdicts.encoders import JSON
from fsdicts.dictionary import Dictionary

class Database(Dictionary):

	def __init__(self, path, encoder=JSON):
		# Create the directory
		if not os.path.exists(path):
			os.makedirs(path)

		# Initialize the storage object
		key_storage = Storage(os.path.join(path, "keys"))
		value_storage = Storage(os.path.join(path, "values"))

		# Initialize the keystore with objects path and a rainbow table
		super(Database, self).__init__(os.path.join(path, "structure"), (key_storage, value_storage), encoder)
