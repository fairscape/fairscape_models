# Sample Model

The `Sample` model is used to describe a biological or physical sample used in an experiment, such as a cell line or tissue specimen.

### Properties

| Property                        | Type                              | Description                                                                                      | Required |
| ------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------ | :------: |
| `guid` (alias: `@id`)           | `str`                             | The unique, resolvable identifier for the Sample.                                                |   Yes    |
| `name`                          | `str`                             | A human-readable name for the sample.                                                            |   Yes    |
| `author`                        | `Union[str, List[str]]`           | The person, people, or organization that prepared or provided the sample.                        |   Yes    |
| `description`                   | `str`                             | A detailed description of the sample, its source, and any preparation steps (min 10 characters). |   Yes    |
| `keywords`                      | `List[str]`                       | A list of keywords to aid in discovery.                                                          |   Yes    |
| `metadataType` (alias: `@type`) | `Optional[str]`                   | The schema.org type. Defaults to `https://w3id.org/EVI#Sample`.                                  |    No    |
| `contentUrl`                    | `Optional[Union[str, List[str]]]` | A URL pointing to more information about the sample type.                                        |    No    |
| `cellLineReference`             | `Optional[IdentifierValue]`       | A link (by `@id`) to a `BioChemEntity` that formally describes the cell line.                    |    No    |

### Example

```json
{
  "@id": "ark:59852/sample-MDA-MB-468-cell-line-mass-spec-sample-oPzB4vOldoF",
  "@type": "https://w3id.org/EVI#Sample",
  "name": "MDA-MB-468 Cell Line Mass Spec Sample",
  "author": "Forget A, Obernier K, Krogan N",
  "description": "SEC-MS profiling of MDA-MB468 breast cancer cell line following treatment with vorinostat or paclitaxel. Each SEC-MS set is composed of 72 fractions.",
  "keywords": [
    "human",
    "MDA-MB-468",
    "mass spectrometry",
    "SEC-MS",
    "vorinostat",
    "paclitaxel"
  ],
  "cellLineReference": {
    "@id": "ark:59852/cell-line-MDA-MB-468"
  }
}
```
