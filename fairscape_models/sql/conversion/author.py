from fairscape_models.fairscape_base import IdentifierValue
from fairscape_models.computation import Computation
import re


# Converting fairscape_models author property into data formats For writing into SQL

def extractAuthor(author):
	if isinstance(author, str):
		# TODO deal with string of list of authors
		return (author, None)
	if isinstance(author, IdentifierValue):
		return (author.name, author.guid)	

def TransformAuthors(inputModel):
	""" Convert fairscape_models pydantic element authors into list of SQL authors
	"""
	authorOutput = set()

	if isinstance(inputModel, Computation):
		authorOutput.add(extractAuthor(inputModel.runBy))

	else:
		if isinstance(inputModel.author, list):
			for auth in inputModel.author:
				authorOutput.add(extractAuthor(auth))
		else:
			authorList = re.split(r'[,&]', inputModel.author)
			if len(authorList) == 1:
				authorOutput.add(extractAuthor(inputModel.author))
			else:
				for auth in authorList:
					authorOutput.add((auth.lstrip(" "), None) )

	return authorOutput	