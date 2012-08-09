class BaseModel(object):
	def move(self, **kwargs):
		raise NotImplementedError("Must define a 'move' method on the model being called")