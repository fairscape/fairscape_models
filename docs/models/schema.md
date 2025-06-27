# Schema Model

The `Schema` model provides a formal, machine-readable definition for a tabular dataset, based on JSON Schema principles. It is used to validate the structure and content of data files and to provide semantic meaning to their columns.

It inherits from `FairscapeEVIBaseModel`, which includes properties like `keywords`, `license`, and `context`.

### Properties

| Property                        | Type                  | Description                                                                                                          | Required |
| ------------------------------- | --------------------- | -------------------------------------------------------------------------------------------------------------------- | :------: |
| `guid` (alias: `@id`)           | `str`                 | The unique, resolvable identifier for the Schema.                                                                    |   Yes    |
| `name`                          | `str`                 | A human-readable name for the schema.                                                                                |   Yes    |
| `description`                   | `str`                 | A detailed description of the data that this schema defines (min 5 characters).                                      |   Yes    |
| `properties`                    | `Dict[str, Property]` | A dictionary where keys are property names and values are `Property` objects describing each column or column group. |   Yes    |
| `metadataType` (alias: `@type`) | `str`                 | The schema type. Defaults to `evi:Schema`.                                                                           |    No    |
| `schemaType` (alias: `type`)    | `Optional[str]`       | The JSON Schema type for the root object. Defaults to "object".                                                      |    No    |
| `additionalProperties`          | `Optional[bool]`      | Whether additional columns not defined in `properties` are allowed. Defaults to `True`.                              |    No    |
| `required`                      | `Optional[List[str]]` | A list of property names that must be present in the data.                                                           |    No    |
| `separator`                     | `Optional[str]`       | The character used to separate columns in the data file (e.g., "," or "\t"). Defaults to ",".                        |    No    |
| `header`                        | `Optional[bool]`      | Whether the data file contains a header row. Defaults to `True`.                                                     |    No    |

### The `Property` Object

Each key in the `properties` dictionary maps to a `Property` object with the following fields:

| Property       | Type              | Description                                                                                                   | Required |
| -------------- | ----------------- | ------------------------------------------------------------------------------------------------------------- | :------: |
| `description`  | `str`             | A human-readable description of the column/property.                                                          |   Yes    |
| `index`        | `Union[str, int]` | The 0-based index or slice (e.g., `2::`, `::5`, `2:5`) of the column(s).                                      |   Yes    |
| `type`         | `str`             | The data type for the column (`string`, `number`, `integer`, `array`, `boolean`).                             |   Yes    |
| `value_url`    | `Optional[str]`   | A URL to an ontology term that formally defines the property's meaning.                                       |    No    |
| `pattern`      | `Optional[str]`   | For `string` types, a valid regular expression that the column's values must match.                           |    No    |
| `items`        | `Optional[Item]`  | For `array` types, an `Item` object describing the elements within the array. It must contain a `type` field. |    No    |
| `min_items`    | `Optional[int]`   | For `array` types, the minimum number of items.                                                               |    No    |
| `max_items`    | `Optional[int]`   | For `array` types, the maximum number of items.                                                               |    No    |
| `unique_items` | `Optional[bool]`  | For `array` types, whether all items must be unique.                                                          |    No    |

### Example

```json
{
  "@context": {
    "@vocab": "https://schema.org/",
    "EVI": "https://w3id.org/EVI#"
  },
  "@id": "ark:59852/schema-apms-music-embedding-izNjXSs",
  "@type": "EVI:Schema",
  "name": "APMS Embedding Schema",
  "description": "Tabular format for APMS music embeddings from PPI networks from the music pipeline from the B2AI Cellmaps for AI project",
  "properties": {
    "Experiment Identifier": {
      "description": "Identifier for the APMS experiment responsible for generating the raw PPI used to create this embedding vector",
      "index": 0,
      "type": "string",
      "pattern": "^APMS_[0-9]*$"
    },
    "Gene Symbol": {
      "description": "Gene Symbol for the APMS bait protien",
      "index": 1,
      "type": "string",
      "pattern": "^[A-Za-z0-9\\\\-]*$"
    },
    "MUSIC APMS Embedding": {
      "description": "Embedding Vector values for genes determined by running node2vec on APMS PPI networks. Vector has 1024 values for each bait protien",
      "index": "2::",
      "type": "array",
      "maxItems": 1024,
      "minItems": 1024,
      "uniqueItems": false,
      "items": { "type": "number" }
    }
  },
  "type": "object",
  "required": ["Experiment Identifier", "Gene Symbol", "MUSIC APMS Embedding"],
  "separator": ",",
  "header": false
}
```
