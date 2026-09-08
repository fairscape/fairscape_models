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

from fairscape_models.dataset import Dataset
from fairscape_models.software import Software
from fairscape_models.computation import Computation
from fairscape_models.rocrate import ROCrateMetadataElem
from typing import Union, List

import sqlalchemy as sa

TYPE_LOOKUP = {
    MetadataTypeEnumSQL.DATASET: DatasetSQL,
    MetadataTypeEnumSQL.SOFTWARE: SoftwareSQL,
    MetadataTypeEnumSQL.ROCRATE: ROCrateMetadataElemSQL,
    MetadataTypeEnumSQL.COMPUTATION: ComputationSQL
}

SERIALIZE_TYPE = {
    DatasetSQL: Dataset,
    SoftwareSQL: Software,
    ROCrateMetadataElemSQL: ROCrateMetadataElem,
    ComputationSQL: Computation
}

METADATA_TYPE_PROPERTY = {
    DatasetSQL: ["https://w3id.org/EVI#Dataset", "https://schema.org/Dataset"],
    SoftwareSQL: ["https://w3id.org/EVI#Software"],
    ROCrateMetadataElemSQL: ["https://schema.org/Dataset", "https://w3id.org/EVI#ROCrate"],
    ComputationSQL: ["http://www.w3.org/ns/prov#Activity", "https://w3id.org/EVI#Computation"]
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
            rootEntity=rootEntityResults[0], 
            keywordResults=keywordResults, 
            authorResults=authorResults, 
            hasPartResults=hasPartResults, 
            isPartOfResults=isPartOfResults
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
        self.metadata = {}


    def _transform_root_entity(self):	
        metadata = self.rootEntity.__dict__.copy()
        del metadata['_sa_instance_state']
        del metadata['id']
        metadata['@id'] = metadata.pop("guid")
        metadata['@type'] = METADATA_TYPE_PROPERTY[type(self.rootEntity)]

        self.metadata = metadata

    def _convert_metadata_computation(self):
        """ Convert Metadata Specifically for Computation
        """
        # TODO check that author results are not null
        self.metadata["runBy"] = self.authorResults[0]
        self.metadata["dateCreated"] = self.metadata["dateCreated"]

        # usedSoftware must be converted to list
        self.metadata["usedSoftware"] = [ {"@id": self.metadata['usedSoftware']}]

    def _convert_metadata(self):
        """ Convert Metadata from SQL Results into Dictionary to be Serialized into Pydantic
        """

        self._transform_root_entity()

        if isinstance(self.rootEntity, ComputationSQL):
            self._convert_metadata_computation()

        self.metadata = {
            **self.metadata,
            "author": self.authorResults, 
            "keywords": [ elem.keywordValue for elem in self.keywordResults],
            "hasPart": [ {"@id": elem.childGUID} for elem in self.hasPartResults],
            "isPartOf": [{"@id": elem.parentGUID} for elem in self.isPartOfResults]
        }

    def _convert_to_pydantic(self):
        return SERIALIZE_TYPE[type(self.rootEntity)].model_validate(self.metadata)

    def transform(self):
        self._convert_metadata()
        return self._convert_to_pydantic()