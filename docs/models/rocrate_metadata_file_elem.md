# ROCrateMetadataFileElem Model

The `ROCrateMetadataFileElem` model is a special entity required by the RO-Crate specification. It describes the `ro-crate-metadata.json` file itself. Its primary purpose is to declare conformance to a specific version of the RO-Crate specification and to identify which entity in the `@graph` is the "Root Dataset" via the `about` property.

### Properties

| Property                        | Type                      | Description                                                                        | Required |
| ------------------------------- | ------------------------- | ---------------------------------------------------------------------------------- | :------: |
| `guid` (alias: `@id`)           | `str`                     | The identifier for this entity. It **must** be `"ro-crate-metadata.json"`.         |   Yes    |
| `metadataType` (alias: `@type`) | `Literal["CreativeWork"]` | The schema.org type. It **must** be `"CreativeWork"`.                              |   Yes    |
| `conformsTo`                    | `IdentifierValue`         | A link to the specific version of the RO-Crate specification the crate adheres to. |   Yes    |
| `about`                         | `IdentifierValue`         | A link to the "Root Dataset" entity (`ROCrateMetadataElem`) within the `@graph`.   |   Yes    |

### Example

This entity is typically the first item in the `@graph` list of an `ro-crate-metadata.json` file.

```json
{
  "@id": "ro-crate-metadata.json",
  "@type": "CreativeWork",
  "conformsTo": {
    "@id": "https://w3id.org/ro/crate/1.1"
  },
  "about": {
    "@id": "ark:59852/rocrate-data-from-treated-human-cancer-cells/"
  }
}
```
