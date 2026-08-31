import enum
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Column, Enum, String
from typing import Optional

Base = declarative_base()

class MetadataTypeEnumSQL(enum.Enum):
	ROCRATE = "ROCRATE"
	SOFTWARE = "SOFTWARE"
	DATASET = "DATASET"
	COMPUTATION = "COMPUTATION"
	ANNOTATION = "ANNOTATION"
	EXPERIMENT = "EXPERIMENT"
	PATIENT = "PATIENT"
	CREATIVE_WORK = "CREATIVE_WORK"
	SAMPLE = "SAMPLE"
	SCHEMA = "SCHEMA"
	BIO_CHEM_ENTITY = "BIO_CHEM_ENTITY"
	MEDICAL_CONDITION = "MEDICAL_CONDITION"
	PERSON = "PERSON"
	ORGANIZATION = "ORGANIZATION"
	DEFINED_TERM = "DEFINED_TERM"
	NONE = "NONE"

class IdentifiersSQL(Base):
	__tablename__ = 'identifier'
	__table_args__ = {"extend_existing": True}  
	guid: str = Column('guid', String, primary_key=True)
	name: str = Column('name', String)
	metadataType: Mapped[MetadataTypeEnumSQL] = mapped_column(Enum(MetadataTypeEnumSQL))

class KeywordSQL(Base):
	__tablename__ = 'keyword_table'
	__table_args__ = {"extend_existing": True}
	id: Mapped[int] = mapped_column(primary_key=True)
	guid: Mapped[str]
	keywordValue: Mapped[str] 
	
class AuthorSQL(Base):
	__tablename__ = 'author'
	__table_args__ = {"extend_existing": True}  
	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str]
	orcid: Mapped[Optional[str]] = mapped_column(default=None)

class AuthorIdentifierSQL(Base):
	__tablename__ = 'author_identifier'
	__table_args__ = {"extend_existing": True}  
	id: Mapped[int] = mapped_column(primary_key=True)
	author_id: Mapped[int]
	identifier_guid: Mapped[str]


class MembershipSQL(Base):
	__tablename__ = 'membership'
	__table_args__ = {"extend_existing": True}  
	id: Mapped[int] = mapped_column(primary_key=True)
	parentGUID: Mapped[str] 
	parentType: Mapped[MetadataTypeEnumSQL] = mapped_column(Enum(MetadataTypeEnumSQL))
	childGUID: Mapped[str] 
	childType: Mapped[MetadataTypeEnumSQL] = mapped_column(Enum(MetadataTypeEnumSQL))


class ComputationUsedDatasetSQL(Base):
	__tablename__ = "used_dataset"
	__table_args__ = {'extend_existing': True}  
	id: Mapped[int] = mapped_column(primary_key=True)
	computationGUID: Mapped[str]
	datasetGUID: Mapped[str]


class ComputationGeneratedDatasetSQL(Base):
	__tablename__ = "generated_dataset"
	__table_args__ = {'extend_existing': True}  
	id: Mapped[int] = mapped_column(primary_key=True)
	computationGUID: Mapped[str]
	datasetGUID: Mapped[str]


class EntitySQL():
	__table_args__ = {"extend_existing": True}  
	id: Mapped[int] = mapped_column(primary_key=True)
	guid: Mapped[str] = Column('guid', String)
	name: Mapped[str] = Column('name', String)
	description: Mapped[str] = Column('description', String)
	datePublished: Mapped[Optional[str]] 


class HasContent():
	contentURL: Mapped[Optional[str]] = Column('contentURL', String, default=None)

class Versioned():
	version: Mapped[str]

class ROCrateMetadataElemSQL(EntitySQL, HasContent, Versioned, Base):
	__tablename__ = 'rocrate'
	__table_args__ = {"extend_existing": True}  
	license: Mapped[Optional[str]]

	# is part of add to membership table 
	#isPartOf: Mapped[Optional[List["MembershipSQL"]]] = relationship(back_populates="parentGUID")
	#datePublished: datetime
	#about: str
	#publisher: str


class DatasetSQL(EntitySQL, HasContent, Versioned, Base):
	__tablename__ = 'dataset'
	fileFormat: Mapped[str]
	generatedBy: Mapped[Optional[str]]
	derivedFrom: Mapped[Optional[str]]


class SoftwareSQL(EntitySQL, HasContent, Versioned, Base):
	__tablename__ = 'software'


class ComputationSQL(EntitySQL, Base):
	__tablename__ = 'computation'
	usedSoftware: Mapped[Optional[str]]