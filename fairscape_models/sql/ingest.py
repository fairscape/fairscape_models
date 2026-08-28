from typing import Union, Optional
from fairscape_models.rocrate import ROCrateV1_2, ROCrateMetadataFileElem
from fairscape_models.software import Software
from fairscape_models.dataset import Dataset
from fairscape_models.computation import Computation
from fairscape_models.schema import Schema
from fairscape_models.fairscape_base import IdentifierValue
from fairscape_models.sql.conversion.construct import (
    ConvertROCrateToSQL,
    ConvertComputationToSQL,
    ConvertSoftwareToSQL,
    ConvertDatasetToSQL,
)
from fairscape_models.sql.conversion.author import (
    TransformAuthors
)
from fairscape_models.sql.utils import DetermineMetadataTypeSQL
from fairscape_models.sql.models import (
    MetadataTypeEnumSQL,
    ROCrateMetadataElemSQL,
    KeywordSQL,
    AuthorIdentifierSQL,
    AuthorSQL,
    IdentifiersSQL,
    MembershipSQL,
)
from fairscape_models.sql.errors import (
    NoSessionException
)

from logging import Logger
from sqlalchemy import select, insert
from sqlalchemy.orm import Session


class EntityIngestRequest():
    def __init__(
        self, 
        model: Union[ROCrateMetadataElemSQL, Software, Dataset, Computation],
        session: Session,
        writeLogger: Optional[Logger] = None
    ):
        self.model = model
        self.session = session
        self.metadataType = DetermineMetadataTypeSQL(model.metadataType)


    def _digest_keywords(self):
        pass


    def _digest_authors(self):
        pass


    def _digest_membership(self):
        pass


    def _digest_prov(self):
        pass


    def _digest_entity(self):
        match self.MetadataType:
            case MetadataTypeEnumSQL.ROCrateMetadaElem:
                pass
            case MetadataTypeEnumSQL.ROCrateMetadaElem:
                pass


    def write(self):
        entity = self._digest_entity()
        keywords = self._digest_keywords()
        authors = self._digest_authors()
        membership = self._digest_authors()
        prov = self._digest_prov() 

        # insert all rows with session

        pass




class ROCrateIngestRequest():
    def __init__(
        self, 
        model: Union[ROCrateV1_2],
        session: Optional[Session] = None,
        writeLogger: Optional[Logger] = None
    ):
        self.model = model
        self.session = session
        self.logger = writeLogger


    def _check_exists(self):
        """Check if ROCrate Already Exists"""
        crate_metadata = self.model.getCrateMetadata()

        if self.session:
            crate_query = select(IdentifiersSQL).filter_by(guid=crate_metadata.guid)
            crate_results = self.session.execute(crate_query)
            if len(crate_results.scalars().all()) >0:
                return True
            else:
                return False
        else:
            raise NoSessionException("No Session to Query")


    def _digest_authors(self) -> set[tuple[str, str|None]]:
        """ Create a set of all authors for a ROCrate
        """
        authorSet = set()
        for elem in self.model.metadataGraph:
            elemSQLType = DetermineMetadataTypeSQL(elem.metadataType)
            if isinstance(elem, ROCrateMetadataFileElem):
                continue
            match elemSQLType:
                case MetadataTypeEnumSQL.COMPUTATION:
                    authorSet.add((elem.runBy, None))
                case MetadataTypeEnumSQL.SCHEMA:
                    pass
                case _:
                    for outputElem in TransformAuthors(elem):
                        authorSet.add(outputElem)
        return authorSet


    def _check_authors(self, AuthorData: set[tuple[str, str|None]]) -> tuple[set[tuple[str, str|None]], dict[str, int]]:
        """ Check which authors in the ROCrate already exist in the database, 
            if they do get their row ids creating tuples of (<row_id>: int, <name>: str) and remove from AuthorData.
            Return these tuples and the modified AuthorData
        """
        remove_authors = []
        author_ids = {}
        if self.session:
            # TODO compare to _in(AuthorSQL.name=[author[0] for author in AuthorData] query

            # check if session is alive
            for author in AuthorData:
                single_author_query = select(AuthorSQL).filter_by(name=author[0])
                results = self.session.scalar(single_author_query)

                if results:
                    remove_authors.append(author)
                    author_ids[results.name] = results.id

            for existing_author in remove_authors:
                AuthorData.remove(existing_author)

            return AuthorData, author_ids
        else:
            raise NoSessionException("No Session Available to Query")


    def _write_authors(self, AuthorData: set[tuple[str, str| None]]) -> dict[str, int]:
        """ Write all author data to sql and return a list of tuples containing the row id and the author's name
        """

        author_insert_data = [AuthorSQL(**{"name": auth[0], "orcid": auth[1]}) for auth in AuthorData]
        self.session.add_all(
            author_insert_data 
        )
        self.session.flush()
        author_ids = {author_row.name: author_row.id for author_row in author_insert_data}
        return author_ids


    def _get_linked_authors(inputElem, AuthorIDs: dict[str, int])->list[dict[str, str | int]]:
        entity_author_ids = [ AuthorIDs[auth[0]] for auth in TransformAuthors(inputElem)]
        return [
            {
                "author_id": auth_id, 
                "identifier_guid": inputElem.guid
            } for auth_id in entity_author_ids
        ]


    def _write_identifier_authors(self, AuthorIDs: dict[str, int]):
        """ Insert Statement to Link GUID to Author row IDs
        """

        for metadataElem in self.model.metadataGraph:
            if isinstance(metadataElem, ROCrateMetadataFileElem):
                continue
            if isinstance(metadataElem, Schema):
                continue
            else:
                self.session.execute(
                    insert(AuthorIdentifierSQL),
                    self._get_linked_authors(metadataElem, AuthorIDs)
                )
                self.session.flush()


    def _digest_identifiers(self)-> set[tuple[str, MetadataTypeEnumSQL, str]]:
        """ Iterate over metadata graph and create identifiers for all elements
        """
        identifiers = set()

        for metadataElem in self.model.metadataGraph:
            if isinstance(metadataElem, ROCrateMetadataFileElem):
                continue
            
            metadataElemSQLType = DetermineMetadataTypeSQL(metadataElem.metadataType)
            identifiers.add((metadataElem.guid, metadataElemSQLType, metadataElem.name))

        return identifiers


    def _write_identifiers(self, Identifiers: set[tuple[str, MetadataTypeEnumSQL, str]]):
        self.session.execute(
            insert(IdentifiersSQL),
            [
                {
                    "guid": identifier_elem[0], 
                    "metadataType": identifier_elem[1], 
                    "name": identifier_elem[2]
                } for identifier_elem in Identifiers
            ]
        )
        self.session.flush()        


    def _digest_iterate_elements(self):
        """ Transform ROCrate Elements into SQLClasses 
        """
        metadataElements = []
        keywordElements = []

        for metadataElem in self.model.metadataGraph:
            elemSQLType = DetermineMetadataTypeSQL(metadataElem.metadataType)

            if isinstance(metadataElem, ROCrateMetadataFileElem):
                continue

            match elemSQLType:
                # TODO: Low Priority Types
                case MetadataTypeEnumSQL.MEDICAL_CONDITION:
                    pass
                case MetadataTypeEnumSQL.ORGANIZATION:
                    pass
                case MetadataTypeEnumSQL.ANNOTATION:
                    pass
                case MetadataTypeEnumSQL.CREATIVE_WORK:
                    pass

                # TODO: High Prio
                case MetadataTypeEnumSQL.SAMPLE:
                    pass
                case MetadataTypeEnumSQL.BIO_CHEM_ENTITY:
                    pass
                case MetadataTypeEnumSQL.EXPERIMENT:
                    pass
                case MetadataTypeEnumSQL.SCHEMA:
                    pass

                case MetadataTypeEnumSQL.ROCRATE:
                    metadataElements.append(ConvertROCrateToSQL(metadataElem))
                    keywordElements += [ KeywordSQL(guid=metadataElem.guid, keywordValue=keywordElem) for keywordElem in metadataElem.keywords]

                case MetadataTypeEnumSQL.DATASET:
                    metadataElements.append(ConvertDatasetToSQL(metadataElem))
                    keywordElements += [ KeywordSQL(guid=metadataElem.guid, keywordValue=keywordElem) for keywordElem in metadataElem.keywords]

                case MetadataTypeEnumSQL.SOFTWARE:
                    metadataElements.append(ConvertSoftwareToSQL(metadataElem))

                case MetadataTypeEnumSQL.COMPUTATION:
                    metadataElements.append(ConvertComputationToSQL(metadataElem))

        return metadataElements, keywordElements