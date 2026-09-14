from fairscape_models.fairscape_base import IdentifierValue
from fairscape_models.computation import Computation
from typing import Tuple, Set, List
import re


# Converting fairscape_models author property into data formats For writing into SQL

def extractAuthor(author: str | IdentifierValue) -> Tuple[str, str | None]:
	if isinstance(author, str):
		# TODO deal with string of list of authors
		return (author, None)
	if isinstance(author, IdentifierValue):
		return (author.name, author.guid)	

def TransformAuthors(inputModel) -> Set[Tuple[str, str | None]]:
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


def ConvertAuthorsSQL(inputModel) -> List[dict]:
	authorList = []
	for elem in TransformAuthors(inputModel):
		if elem[1]:
			authorList.append({"@id": elem[1], "name": elem[0]})
		else:
			authorList.append({"name": elem[0]})
	return authorList