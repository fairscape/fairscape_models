# Fairscape Models Documentation

Welcome to the documentation for `fairscape-models`. This library provides a set of Pydantic models for creating and validating FAIRSCAPE and RO-Crate metadata. These models are designed to ensure that scientific data packages are described in a rich, interoperable, and machine-readable format.

Each model corresponds to a specific entity in the FAIRSCAPE ecosystem, such as a Dataset, Software, or Computation, and is built to serialize to and from JSON-LD.

### Installation

For instructions on how to install the library, please see the [Installation Guide](installation.md).

---

## Available Models

Below is a list of the available Pydantic models. Click on a model name to see its detailed documentation, including properties, types, and examples.

### RO-Crate Models

These models are used to create and structure a complete RO-Crate.

- **[ROCrateV1_2](models/rocrate.md)**: The top-level container for a Research Object Crate. It encapsulates all other metadata elements in its `@graph`.
- **[ROCrateMetadataElem](models/rocrate_metadata_elem.md)**: The "Root Dataset" entity that describes the RO-Crate as a whole.
- **[ROCrateMetadataFileElem](models/rocrate_metadata_file_elem.md)**: The descriptor for the `ro-crate-metadata.json` file itself, as required by the RO-Crate specification.

### Core EVI Models

These models represent the primary entities used to describe a research project's provenance graph.

- **[Dataset](models/dataset.md)**: Describes a data file or a collection of data files.
- **[Software](models/software.md)**: Describes a piece of software used or generated in a project.
- **[Computation](models/computation.md)**: Describes a specific execution or run of software that consumes inputs and produces outputs.
- **[Experiment](models/experiment.md)**: Describes a wet-lab or physical experiment.
- **[Schema](models/schema.md)**: A formal description of the structure and constraints of a tabular data file.

### Supporting Entity Models

These models represent supporting entities that are referenced by the core models.

- **[Instrument](models/instrument.md)**: Describes a physical instrument used in an experiment.
- **[Sample](models/sample.md)**: Describes a biological or physical sample used in an experiment.
- **[BioChemEntity](models/biochem_entity.md)**: A general-purpose model for biochemical entities like proteins, genes, or chemical compounds.
- **[MedicalCondition](models/medical_condition.md)**: Describes a medical condition relevant to the research.

### Base and Helper Models

These models are typically used as parts of other models and are not usually instantiated on their own at the top level of a crate.

- **[IdentifierValue](models/identifier_value.md)**: A simple object used to link to another entity by its `@id`.
- **[IdentifierPropertyValue](models/identifier_property_value.md)**: A key-value pair for providing external identifiers (e.g., from an ontology).
