import re
from datetime import datetime
from string import Template
from collections import ChainMap
from typing import Callable
 # modified from: https://github.com/python/cpython/blob/ebc24d54bcf554403e9bf4b590d5c1f49e648e0d/Lib/string.py#L69
def prepare_template_pattern(cls:Template)->bytes:
	delim = re.escape(cls.delimiter)
	id = cls.idpattern
	argument_pattern = r'[ -~]*' # basically all ASCII. Alternatively, we could accept r"[!-'*-Z^-z\~|]*" for no braces and no brackets
	bid = cls.braceidpattern or cls.idpattern
	pattern = fr"""
	{delim}(?:
		(?P<escaped>{delim})  |   # Escape sequence of two delimiters
		(?P<named_with_arg>{id})
			(?:
				\((?P<argument>{argument_pattern})\)           |
				\{{(?P<argument_with_map>{argument_pattern})}}
			)				  |
		(?P<named>{id})       |   # delimiter and a Python identifier
		{{(?P<braced>{bid})}} |   # delimiter and a braced identifier # I would remove this, but it would break the other class methods. It would be better to make a new class without inheritance...
		(?P<invalid>)             # Other ill-formed delimiter exprs
	)
	"""
	return pattern.encode('utf-8')
_sentinel_dict={}
class NLP_Template(Template):
	pattern = prepare_template_pattern(Template) # in Template.__init_subclass__ it will compile this string.
	# unfortunately Template isn't quite accessible for modifying the pattern and converter
	# you have to reimplement the only functions you'd ever call instead of simply passing a new method (convert() is locally scoped...)
	def __init__(self, template:bytes):
		super().__init__(template)
		# because named = (mo.group(named) or mo.group(...)) is used several times in the source. I don't quite want to copy-paste the whole class
		# so to keep my changes minimal and clear, this is the  solution
		self.__get_named = lambda mo:mo.group('named') or mo.group('braced') or mo.group('named_with_arg')

	# given the mapping, return a delegate to handle the conversion.
	def __convert_delegate(self,mapping:ChainMap)-> Callable[[re.Match],bytes]:
		# modified from: https://github.com/python/cpython/blob/ebc24d54bcf554403e9bf4b590d5c1f49e648e0d/Lib/string.py#L110
		def convert(mo:re.Match)->bytes:
			named = self.__get_named(mo)
			# TODO: Two types of named groups.
			# named(argument:str) which takes arguments from the match object
			# named[argument:str, mapping] which takes args from the match object, but also the entire mapping:ChainMap and does its own dirty work with that.
			argument = mo.group('argument')
			argument_calls_for_map = mo.group('argument_with_map')
			if named is not None:
				try:
					val = mapping[named]
					if callable(val):
						if argument is not None:
							return (val(argument))
						if argument_calls_for_map is not None:
							return (val(argument_calls_for_map,mapping))
						return (val(named))
					return (val)
				except (KeyError,TypeError): return mo.group()
			if mo.group('escaped') is not None:
				return self.delimiter
			if mo.group('invalid') is not None:
				return mo.group()
			raise ValueError('Unrecognized named group in pattern',self.pattern)
		return convert

	def custom_safe_substitute(self, mapping=_sentinel_dict, /, **kws): # modified from: https://github.com/python/cpython/blob/ebc24d54bcf554403e9bf4b590d5c1f49e648e0d/Lib/string.py#L104
		if mapping is _sentinel_dict:
			mapping = kws
		elif kws:
			mapping = ChainMap(kws, mapping)
		
		return self.pattern.sub(self.__convert_delegate(mapping), self.template)
	
	def get_identifiers(self): #modified from: https://github.com/python/cpython/blob/ebc24d54bcf554403e9bf4b590d5c1f49e648e0d/Lib/string.py#L157
		ids = []
		for mo in self.pattern.finditer(self.template):
			named = self.__get_named(mo)
			if named is not None and named not in ids:
				ids.append(named)
			elif (named is None
				and mo.group('invalid') is None
				and mo.group('escaped') is None):
				raise ValueError('Unrecognized named group in pattern',
					self.pattern)
		return ids

# available_substitutions = {
# 	'time_now':datetime.now().__str__(),
# 	# todays date
# 	# date time from string
# 	# filename (pass)
# 	# file path
# 	# library meta data
# 	'project': lambda: 'gamma',
# 	'bin': lambda: '01 foobar',
# 	'category': lambda: '31 barfoo',
# 	'func':lambda x:f'>>{x}<<',
# 	'func2': lambda x,map: f'{x}'
# }

# template_str = r"""---
# Project: "$project"
# Category: "$category"
# Bin: "$bin"
# Creation: "$time_now"
# aliases: $func2{test}
# ---
# """
# foo = NLP_Template(template_str)
# print(foo.custom_safe_substitute(available_substitutions))