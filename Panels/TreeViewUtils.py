from JD__utils import DEBUG_PREFIX
from enum import Flag,auto
from typing import List
# def treeStorePrintRow(store,tPath,tIter):
#	print('\t' * (tPath.get_depth()-1), store[tIter][:], sep="")

class ModelTraverseFlags(Flag):
	# behavior
	EARLY_RETURN = auto() # in the find_matching_entity delegate, return TRUE OR FALSE when entities are checked
	# return types
	RET_PATH = auto() # do NOT use with RET_ITER
	RET_ITER = auto() # do NOT use with RET_PATH
	RET_TUPLE = RET_PATH | RET_ITER # if set, return a Tuple[Gtk.TreePath,Gtk.TreeIter] disregards RET_PATH
# Given a set of flags, a TreeModelForeachFunc callback is created
def __create_find_function(found:List, flags:ModelTraverseFlags):
	append_func = found.append

	if (ModelTraverseFlags.RET_TUPLE in flags):
		append_delegate = lambda path,iter: append_func((path,iter))
	elif (ModelTraverseFlags.RET_ITER in flags):
		append_delegate = lambda path,iter: append_func(iter)
	elif (ModelTraverseFlags.RET_PATH in flags):
		append_delegate = lambda path,iter: append_func(path)
	
	if (ModelTraverseFlags.EARLY_RETURN in flags):
		def find(model,path,iter,entity):
			if model[iter][1] == entity:
				append_delegate(path,iter)
				return True
			return False
	else:
		def find(model,path,iter,entity):
			if model[iter][1] == entity:
				append_delegate(path,iter)
			return False
	return find
# returns a list of entities from the model
# the ModelTraversalFlags defines how the callback will behave.
def get_entites_from_model(model, entity, flags:ModelTraverseFlags) -> List:
	found:List = []
	model.foreach(__create_find_function(found,flags),entity)
	return found