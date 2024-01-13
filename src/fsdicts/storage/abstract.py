class AbstractStorage(object):

    def __init__(self, path):
        raise NotImplementedError()
    
    def put(self, value):
        raise NotImplementedError()
    
    def read(self, identifier):
        raise NotImplementedError()
    
    def link(self, identifier, link):
        raise NotImplementedError()
    
    def unlink(self, link):
        raise NotImplementedError()
    
    def release(self, identifier):
        raise NotImplementedError()
    
    def purge(self):
        raise NotImplementedError()