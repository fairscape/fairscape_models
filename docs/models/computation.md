# Computation Model

The `Computation` model is used to describe a specific execution of a software tool, script, or computational workflow. It's a critical component for provenance, linking input datasets and software to their generated outputs.

### Properties

| Property                  | Type                              | Description                                                                                  | Required |
| ------------------------- | --------------------------------- | -------------------------------------------------------------------------------------------- | :------: |
| `guid` (alias: `@id`)     | `str`                             | The unique, resolvable identifier for the Computation. Should be an ARK.                     |   Yes    |
| `name`                    | `str`                             | A human-readable name for the computation (e.g., "Spectronaut Analysis Run 1").              |   Yes    |
| `runBy`                   | `str`                             | The person, organization, or agent that executed the computation.                            |   Yes    |
| `description`             | `str`                             | A detailed description of the computation's purpose and methods (min 10 characters).         |   Yes    |
| `dateCreated`             | `str`                             | The date the computation was executed, in ISO 8601 format.                                   |   Yes    |
| `metadataType`            | `Optional[str]`                   | The schema.org type. Defaults to `https://w3id.org/EVI#Computation`.                         |    No    |
| `additionalType`          | `Optional[str]`                   | An additional type identifier. Defaults to "Computation".                                    |    No    |
| `associatedPublication`   | `Optional[str]`                   | A URL or citation for a publication associated with this computation.                        |    No    |
| `additionalDocumentation` | `Optional[str]`                   | A URL for additional documentation.                                                          |    No    |
| `command`                 | `Optional[Union[List[str], str]]` | The exact command-line invocation, script, or set of parameters used to run the computation. |    No    |
| `usedSoftware`            | `Optional[List[IdentifierValue]]` | A list of links (by `@id`) to the `Software` entities used in this computation.              |    No    |
| `usedDataset`             | `Optional[List[IdentifierValue]]` | A list of links (by `@id`) to the `Dataset` entities consumed as input.                      |    No    |
| `generated`               | `Optional[List[IdentifierValue]]` | A list of links (by `@id`) to the `Dataset` entities that were produced as output.           |    No    |

### Example

```json
{
  "@id": "ark:59852/computation-control-1-sec-ms-mda-mb468",
  "@type": "https://w3id.org/EVI#Computation",
  "name": "Generation of Biosep_MDAMB468_CTRL_1_Report.tsv",
  "runBy": "Krogan Laboratory, UCSF",
  "description": "Computational process that generated Biosep_MDAMB468_CTRL_1_Report.tsv from control experiment 1 raw data using Spectronaut software.",
  "dateCreated": "2025-06-23",
  "usedSoftware": [
    {
      "@id": "ark:59852/software-spectronaut-wGLsihNfp5w"
    }
  ],
  "usedDataset": [
    {
      "@id": "ark:59852/dataset-control-1-sec-ms-mda-mb468"
    }
  ],
  "generated": [
    {
      "@id": "ark:59852/dataset-control-1-report"
    }
  ]
}
```
