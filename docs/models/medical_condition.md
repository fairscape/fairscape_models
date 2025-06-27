# MedicalCondition Model

The `MedicalCondition` model is used to describe a disease, disorder, or other condition relevant to the research. It is based on the schema.org `MedicalCondition` type.

### Properties

| Property                        | Type                                      | Description                                                                                           | Required |
| ------------------------------- | ----------------------------------------- | ----------------------------------------------------------------------------------------------------- | :------: |
| `guid` (alias: `@id`)           | `str`                                     | The unique, resolvable identifier for the medical condition.                                          |   Yes    |
| `name`                          | `str`                                     | The common name of the condition (e.g., "Breast adenocarcinoma").                                     |   Yes    |
| `description`                   | `str`                                     | A detailed description of the medical condition.                                                      |   Yes    |
| `metadataType` (alias: `@type`) | `Optional[str]`                           | The schema.org type. Defaults to "MedicalCondition".                                                  |    No    |
| `identifier`                    | `Optional[List[IdentifierPropertyValue]]` | A list of formal identifiers from medical ontologies (e.g., NCI Thesaurus, MeSH).                     |    No    |
| `drug`                          | `Optional[List[IdentifierValue]]`         | A list of links (by `@id`) to `BioChemEntity` models representing drugs used to treat this condition. |    No    |
| `usedBy`                        | `Optional[List[IdentifierValue]]`         | A list of links to other entities that reference this condition.                                      |    No    |

### Example

```json
{
  "@id": "ark:59852/disease-breast-adenocarcinoma",
  "@type": "MedicalCondition",
  "name": "Breast adenocarcinoma",
  "description": "The most common histologic type of breast carcinoma. Representative examples include invasive ductal carcinoma not otherwise specified, ductal carcinoma in situ, etc.",
  "identifier": [
    {
      "@type": "PropertyValue",
      "name": "NCI Thesaurus",
      "value": "NCIt:C5214",
      "url": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=C5214"
    }
  ]
}
```
