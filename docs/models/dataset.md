# Dataset Model

The `Dataset` model is used to describe a data entity, which can be a single file or a logical grouping of files. It includes metadata about authorship, publication, version, and its relationships with other entities in the provenance graph.

### Properties

| Property                  | Type                                                      | Description                                                                                   | Required |
| ------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------------------- | :------: |
| `guid` (alias: `@id`)     | `str`                                                     | The unique, resolvable identifier for the Dataset. Should be an ARK.                          |   Yes    |
| `name`                    | `str`                                                     | A human-readable name for the dataset.                                                        |   Yes    |
| `author`                  | `Union[str, List[str]]`                                   | The person, people, or organization that created the dataset.                                 |   Yes    |
| `datePublished`           | `str`                                                     | The date the dataset was published, in ISO 8601 format.                                       |   Yes    |
| `description`             | `str`                                                     | A detailed description of the dataset (min 10 characters).                                    |   Yes    |
| `keywords`                | `List[str]`                                               | A list of keywords to aid in discovery.                                                       |   Yes    |
| `format`                  | `str`                                                     | The file format of the dataset (e.g., "CSV", "TSV", "image/jpeg"). Aliased from `fileFormat`. |   Yes    |
| `metadataType`            | `Optional[str]`                                           | The schema.org type. Defaults to `https://w3id.org/EVI#Dataset`.                              |    No    |
| `additionalType`          | `Optional[str]`                                           | An additional type identifier. Defaults to "Dataset".                                         |    No    |
| `version`                 | `str`                                                     | The version of the dataset. Defaults to "0.1.0".                                              |    No    |
| `associatedPublication`   | `Optional[str]`                                           | A URL or citation for a publication associated with this dataset.                             |    No    |
| `additionalDocumentation` | `Optional[str]`                                           | A URL for additional documentation.                                                           |    No    |
| `dataSchema`              | `Optional[IdentifierValue]`                               | A link (by `@id`) to a `Schema` object that describes the structure of this dataset.          |    No    |
| `generatedBy`             | `Optional[Union[IdentifierValue, List[IdentifierValue]]]` | Links to the `Computation` or `Experiment` that produced this dataset.                        |    No    |
| `derivedFrom`             | `Optional[List[IdentifierValue]]`                         | Links to one or more `Dataset` entities from which this dataset was derived.                  |    No    |
| `usedByComputation`       | `Optional[List[IdentifierValue]]`                         | Links to `Computation` entities that used this dataset as an input.                           |    No    |
| `contentUrl`              | `Optional[Union[str, List[str]]]`                         | The URL(s) or relative file path(s) pointing to the actual data file(s).                      |    No    |

### Example

```json
{
  "@id": "ark:59852/dataset-control-1-report",
  "@type": "https://w3id.org/EVI#Dataset",
  "name": "Control Experiment 1: SEC-MS Processed Data (Report.tsv)",
  "author": "Forget A, Obernier K, Krogan N",
  "datePublished": "2025-06-23",
  "version": "1.0",
  "description": "Processed SEC-MS data (Report.tsv) for MDA-MB468 cells, control experiment 1.",
  "keywords": [
    "MDA-MB468",
    "SEC-MS",
    "proteomics",
    "processed data",
    "control"
  ],
  "format": "TSV",
  "evi:Schema": {
    "@id": "ark:59852/schema-control-1-sec-ms-mda-mb468"
  },
  "generatedBy": [
    {
      "@id": "ark:59852/computation-control-1-sec-ms-mda-mb468"
    }
  ],
  "derivedFrom": [],
  "usedByComputation": [],
  "contentUrl": "ftp://massive-ftp.ucsd.edu/v10/MSV000098237/search/Biosep_MDAMB468_CTRL_1_Report.tsv"
}
```
