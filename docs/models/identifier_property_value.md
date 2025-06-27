# IdentifierPropertyValue Model

The `IdentifierPropertyValue` model is a helper class used to represent a key-value pair, typically for providing formal identifiers from external databases, ontologies, or registries. It is based on the schema.org `PropertyValue` type.

This is commonly used in the `identifier` property of models like `BioChemEntity` and `MedicalCondition`.

### Properties

| Property                        | Type  | Description                                                                    | Required |
| ------------------------------- | ----- | ------------------------------------------------------------------------------ | :------: |
| `metadataType` (alias: `@type`) | `str` | The schema type of the object. Defaults to "PropertyValue".                    |    No    |
| `value`                         | `str` | The value of the identifier (e.g., "RRID:CVCL_0419", "NCIt:C5214").            |   Yes    |
| `name`                          | `str` | The name of the property or identifier source (e.g., "RRID", "NCI Thesaurus"). |   Yes    |

### Example

Describing a cell line with an RRID identifier:

```json
{
  "@id": "ark:59852/cell-line-MDA-MB-468",
  "@type": "BioChemEntity",
  "name": "MDA-MB-468 Cell Line",
  "identifier": [
    {
      "@type": "PropertyValue",
      "name": "RRID",
      "value": "RRID:CVCL_0419"
    }
  ]
}
```
