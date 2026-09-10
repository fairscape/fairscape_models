import sys
import os

# load in the fairscape models library
sys.path.insert(0, '/workspaces/fairscape_models')

import sqlalchemy as sa

# create engine
from fairscape_models.sql.models import *
from fairscape_models.sql.query import TYPE_LOOKUP, METADATA_TYPE_PROPERTY
import sqlalchemy as sa

# create an engine
engine = sa.create_engine("sqlite:///integration_test.db")

# create table 
Base.metadata.create_all(engine)

test_rocrate_guid = 'https://fairscape.net/api/ark:59853/rocrate-cm4ai-image-downloader'

# create a session
session = sa.orm.Session(engine)

# membership query
#children_guid_query = sa.select(MembershipSQL.childGUID, MembershipSQL.childType).where(MembershipSQL.parentGUID == test_rocrate_guid)

#children_guid_results = session.execute(children_guid_query).all()

element_guid = test_rocrate_guid
element_type = MetadataTypeEnumSQL.ROCRATE

metadata = {}
root_entity_query = sa.select(TYPE_LOOKUP[element_type]).filter_by(guid=element_guid)
root_entity_results = session.scalars(root_entity_query).all()

# keywords
keyword_query = sa.select(KeywordSQL.keywordValue).filter_by(guid=element_guid)

# authors
author_identifier_query = sa.select(AuthorSQL.name, AuthorSQL.orcid).join(AuthorIdentifierSQL, AuthorIdentifierSQL.author_id == AuthorSQL.id).where(AuthorIdentifierSQL.identifier_guid==element_guid)

author_results = session.execute(author_identifier_query).all()

# hasPart
has_part_query = sa.select(MembershipSQL.childGUID).where(MembershipSQL.parentGUID==element_guid)
has_part_results = session.execute(has_part_query).all()

# isPartOf
is_part_of_query = sa.select(MembershipSQL.parentGUID).where(MembershipSQL.childGUID==element_guid)
is_part_of_results = session.execute(is_part_of_query).all()

match element_type:
	case MetadataTypeEnumSQL.DATASET:
		# if its a dataset usedBy/generatedBy
		used_by_query = sa.select(ComputationUsedDatasetSQL.computationGUID).where(ComputationUsedDatasetSQL.datasetGUID == element_guid)
		used_by_results = session.execute(used_by_query).all()


		generated_by_query = sa.select(ComputationGeneratedDatasetSQL.computationGUID).where(ComputationUsedDatasetSQL.datasetGUID == element_guid)
		generated_by_results = session.execute(generated_by_query).all()

		pass
	case MetadataTypeEnumSQL.SOFTWARE:
		# if its a software usedBy
		used_by_query = sa.select(ComputationSQL.guid).where(ComputationSQL.usedSoftware == element_guid)
		used_by_results = session.execute(used_by_query).all()

		pass
	case MetadataTypeEnumSQL.COMPUTATION:
	# if its a computation used/generated
		used_query = sa.select(ComputationUsedDatasetSQL.datasetGUID).where(ComputationUsedDatasetSQL.computationGUID == element_guid)
		used_results = session.execute(used_query).all()

		generated_query = sa.select(ComputationGeneratedDatasetSQL.datasetGUID).where(ComputationGeneratedDatasetSQL.computationGUID == element_guid)
		generated_results = session.execute(generated_query).all()

session.close()