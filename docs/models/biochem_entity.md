# BioChemEntity Model

The `BioChemEntity` model is a flexible class for describing a wide range of biological or chemical entities, such as proteins, genes, chemical compounds, or cell lines. It is based on the schema.org `BioChemEntity` type.

### Properties

| Property                        | Type                                      | Description                                                                            | Required |
| ------------------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------- | :------: |
| `guid` (alias: `@id`)           | `str`                                     | The unique, resolvable identifier for the entity.                                      |   Yes    |
| `name`                          | `str`                                     | The common name of the entity (e.g., "Paclitaxel", "TP53").                            |   Yes    |
| `metadataType` (alias: `@type`) | `Optional[str]`                           | The schema.org type. Defaults to "BioChemEntity".                                      |    No    |
| `identifier`                    | `Optional[List[IdentifierPropertyValue]]` | A list of formal identifiers from other databases or ontologies (e.g., RRID, PubChem). |    No    |
| `associatedDisease`             | `Optional[IdentifierValue]`               | A link (by `@id`) to a `MedicalCondition` associated with this entity.                 |    No    |
| `usedBy`                        | `Optional[List[IdentifierValue]]`         | A list of links (by `@id`) to experiments or other entities that used this entity.     |    No    |
| `description`                   | `Optional[str]`                           | A detailed description of the entity.                                                  |    No    |

### Example

```json
{
  "@id": "ark:59852/treatment-paclitaxel",
  "@type": "BioChemEntity",
  "name": "Paclitaxel",
  "description": "Paclitaxel is a taxoid chemotherapeutic agent used for the treatment of various cancers including breast and lung cancer.",
  "associatedDisease": {
    "@id": "ark:59852/medicalcondition-breast-adenocarcinoma"
  },
  "identifier": [
    {
      "@type": "PropertyValue",
      "name": "RxNORM",
      "value": "https://rxnav.nlm.nih.gov/id/rxnorm/56946"
    },
    {
      "@type": "PropertyValue",
      "name": "PubChem",
      "value": "https://pubchem.ncbi.nlm.nih.gov/compound/Paclitaxel"
    }
  ]
}
```
