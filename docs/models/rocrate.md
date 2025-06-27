# RO-Crate Model (ROCrateV1_2)

The `ROCrateV1_2` model is the top-level container for a Research Object Crate. It encapsulates all metadata about a project—including datasets, software, computations, and their relationships—into a single, structured JSON-LD document.

### Main Properties

| Property   | Type               | Description                                                                                                                | Required |
| ---------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------- | :------: |
| `@context` | `Optional[Dict]`   | The JSON-LD context, which defines the vocabularies (e.g., schema.org, EVI) used in the crate.                             |    No    |
| `@graph`   | `List[Union[...]]` | The main content of the crate. It is a list of all metadata entities (e.g., `Dataset`, `Software`, `Computation` objects). |   Yes    |

### The `@graph`

The `@graph` is a list that contains all the individual metadata "nodes" of the project. This includes:

- **A `ROCrateMetadataFileElem`**: A special "descriptor" node for the `ro-crate-metadata.json` file itself. It conforms to the RO-Crate specification and points to the root dataset.
- **A `ROCrateMetadataElem`**: The "root dataset" node that describes the RO-Crate as a whole. It includes top-level metadata like the crate's name, description, author, and license, and lists all other entities in its `hasPart` property.
- **All other entities**: Instances of `Dataset`, `Software`, `Computation`, `Experiment`, and any other supporting models used to describe the project's components and provenance.

### Example Snippet

This example shows the high-level structure of an `ro-crate-metadata.json` file.

```json
{
  "@context": {
    "@vocab": "https://schema.org/",
    "EVI": "https://w3id.org/EVI#"
  },
  "@graph": [
    {
      "@id": "ro-crate-metadata.json",
      "@type": "CreativeWork",
      "conformsTo": { "@id": "https://w3id.org/ro/crate/1.1" },
      "about": { "@id": "ark:59852/my-awesome-rocrate" }
    },
    {
      "@id": "ark:59852/my-awesome-rocrate",
      "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
      "name": "My Awesome RO-Crate",
      "description": "An example RO-Crate.",
      "hasPart": [
        { "@id": "ark:59852/dataset-input-data" },
        { "@id": "ark:59852/software-my-script" },
        { "@id": "ark:59852/computation-analysis-run" }
      ]
    },
    {
      "@id": "ark:59852/dataset-input-data",
      "@type": "https://w3id.org/EVI#Dataset",
      "name": "Input Data"
    }
  ]
}
```
