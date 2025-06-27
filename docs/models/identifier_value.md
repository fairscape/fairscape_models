# IdentifierValue Model

The `IdentifierValue` model is a simple helper class used for creating a link to another entity within the RO-Crate `@graph`. It consists of a single property, `@id`, which holds the unique identifier of the target entity.

This model is used extensively in properties like `usedSoftware`, `usedDataset`, `generated`, `derivedFrom`, etc., to establish relationships between different metadata nodes.

### Properties

| Property              | Type  | Description                                                                      | Required |
| --------------------- | ----- | -------------------------------------------------------------------------------- | :------: |
| `guid` (alias: `@id`) | `str` | The unique, resolvable identifier (e.g., an ARK) of the entity being referenced. |   Yes    |

### Example

A `Computation` linking to the `Software` it used:

```json
{
  "@id": "ark:59852/computation-analysis-run",
  "@type": "https://w3id.org/EVI#Computation",
  "name": "Analysis Run",
  "usedSoftware": [
    {
      "@id": "ark:59852/software-analysis-script"
    }
  ]
}
```
