import enum
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy.schema import Index
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import Column, Enum, String, JSON, DateTime, func
from typing import Optional
import datetime

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
	guid: Mapped[str] = mapped_column(primary_key=True)
	name: Mapped[str] 
	metadataType: Mapped[MetadataTypeEnumSQL]

Index("idx_identifier_guid", IdentifiersSQL.guid)
	
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

Index("idx_membership_parent_child", MembershipSQL.parentGUID, MembershipSQL.childGUID)

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
	guid: Mapped[str]
	name: Mapped[str]
	description: Mapped[str] 
	datePublished: Mapped[Optional[str]] 
	author: Mapped[list[dict]] = mapped_column(MutableList.as_mutable(JSON))


class HasKeywords():
	keywords: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSON))

class HasContent():
	contentURL: Mapped[Optional[str]] = mapped_column(default=None)

class Versioned():
	version: Mapped[str]

class ROCrateMetadataElemSQL(EntitySQL, HasKeywords, HasContent, Versioned, Base):
	__tablename__ = 'rocrate'
	__table_args__ = {"extend_existing": True}  
	license: Mapped[Optional[str]]
	#datePublished: datetime
	#about: str
	#publisher: str

Index("idx_rocrate_guid", ROCrateMetadataElemSQL.guid)

class DatasetSQL(EntitySQL, HasKeywords, HasContent, Versioned, Base):
	__tablename__ = 'dataset'
	fileFormat: Mapped[str]
	generatedBy: Mapped[Optional[str]]
	derivedFrom: Mapped[Optional[str]]

Index("idx_dataset_guid", DatasetSQL.guid)

class SoftwareSQL(EntitySQL, HasContent, Versioned, Base):
	__tablename__ = 'software'
	fileFormat: Mapped[str]

Index("idx_software_guid", SoftwareSQL.guid)

class ComputationSQL(EntitySQL, Base):
	__tablename__ = 'computation'
	usedSoftware: Mapped[Optional[str]]
	dateCreated: Mapped[Optional[str]]

Index("idx_computation_guid", SoftwareSQL.guid)

class ROCrateRegistration(Base):
	__tablename__ = 'registration'
	id: Mapped[int] = mapped_column(primary_key=True)
	guid: Mapped[str] 
	version: Mapped[int] = mapped_column(default=1)
	filepath: Mapped[str] = mapped_column(unique=True)
	time_registerd: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
	time_updated: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

Index("idx_registration_filepath", ROCrateRegistration.filepath)