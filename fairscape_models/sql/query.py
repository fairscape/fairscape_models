from fairscape_models.sql.models import (
    MetadataTypeEnumSQL,
    DatasetSQL,
    SoftwareSQL,
    ROCrateMetadataElemSQL,
    ComputationSQL,
    IdentifiersSQL,
    AuthorSQL,
    AuthorIdentifierSQL,
    MembershipSQL,
    KeywordSQL
)
from typing import Union, List

import sqlalchemy as sa

TYPE_LOOKUP = {
    MetadataTypeEnumSQL.DATASET: DatasetSQL,
    MetadataTypeEnumSQL.SOFTWARE: SoftwareSQL,
    MetadataTypeEnumSQL.ROCRATE: ROCrateMetadataElemSQL,
    MetadataTypeEnumSQL.COMPUTATION: ComputationSQL
}


class QueryByGUID():
    def __init__(self, guid: str):
        self.guid = guid

    def _query_type(self, session: sa.orm.Session) -> MetadataTypeEnumSQL:

        # query the identifier table to get the metadata type
        q = sa.select(IdentifiersSQL).filter_by(guid=self.guid)
        identifierResults = session.scalars(q).all()

        return identifierResults[0].metadataType

    def execute(self, session: sa.orm.Session):

        # lookup the root query
        rootEntityType = TYPE_LOOKUP[self._query_type(session)]
        rootEntityQuery = sa.select(rootEntityType).filter_by(guid=self.guid)

        rootEntityResults = session.scalars(rootEntityQuery).all()
    
        # get keywords
        queryKeywords = sa.select(KeywordSQL).filter_by(guid=self.guid)
        keywordResults = session.scalars(queryKeywords).all()

        # get authors via AuthorIdentifierSQL
        queryLinkedAuthors = sa.select(AuthorIdentifierSQL).filter_by(identifier_guid=self.guid)
        linkedAuthors = session.scalars(queryLinkedAuthors).all()

        # get authors
        authorIds = [ authorElem.author_id for authorElem in linkedAuthors]
        authorResults = []
        for authorIdElem in authorIds:
            queryAuthor = sa.select(AuthorSQL.name, AuthorSQL.orcid).filter_by(id= authorIdElem)
            authorResults += session.scalars(queryAuthor).all() 

        # get hasPart
        queryHasPart = sa.select(MembershipSQL).filter_by(parentGUID=self.guid)
        hasPartResults = session.scalars(queryHasPart).all()

        # isPartOf
        queryIsPartOf = sa.select(MembershipSQL).filter_by(childGUID=self.guid)
        isPartOfResults = session.scalars(queryIsPartOf).all()

        # TODO Provenance properties

        return QueryResponse(
            rootEntityResults, 
            keywordResults, 
            authorResults, 
            hasPartResults, 
            isPartOfResults
        )


class QueryResponse():

    def __init__(
        self, 
        rootEntity: Union[ROCrateMetadataElemSQL, SoftwareSQL, DatasetSQL, ComputationSQL],
        authorResults: List[AuthorSQL],
        keywordResults: List[KeywordSQL],
        hasPartResults: List[MembershipSQL],
        isPartOfResults: List[MembershipSQL]
        ):

        self.rootEntity = rootEntity
        self.authorResults = authorResults
        self.keywordResults = keywordResults
        self.hasPartResults = hasPartResults
        self.isPartOfResults = isPartOfResults
        self.metadata = None


    def _transform_authors(self):
        authorsList = []
        for elem in self.authorResults:
            if elem.orcid:
                authorsList.append({"@id": elem.orcid})
            else:
                authorsList.append(elem.name)
        return authorsList

    def _transform_root_entity(self):	
        metadata = self.rootEntityResults[0].__dict__.copy()
        del metadata['_sa_instance_state']
        del metadata['id']
        metadata['@id'] = metadata.pop("guid")
        metadata['@type'] = ["EVI:Dataset", "https://schema.org/Dataset"]
        self.metadata = metadata

    def transform(self):

        self._transform_root_entity()
        authorList = self._transform_authors()

        self.metadata = {
            **self.metadata,
            "author": authorList,
            "keywords": [ elem.keywordValue for elem in self.keywordResults],
            "hasPart": [ {"@id": elem.childGUID} for elem in self.hasPartResults],
            "isPartOf": [{"@id": elem.parentGUID} for elem in self.isPartOfResults]
        }
