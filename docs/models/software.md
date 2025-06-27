# Software Model

The `Software` model is used to describe a piece of software, such as a script, library, or command-line tool, that is used or created within a research project.

### Properties

| Property                       | Type                              | Description                                                                             | Required |
| ------------------------------ | --------------------------------- | --------------------------------------------------------------------------------------- | :------: |
| `guid` (alias: `@id`)          | `str`                             | The unique, resolvable identifier for the Software. Should be an ARK.                   |   Yes    |
| `name`                         | `str`                             | The name of the software.                                                               |   Yes    |
| `author`                       | `str`                             | The person, people, or organization that created the software (min 4 characters).       |   Yes    |
| `dateModified`                 | `str`                             | The date this version of the software was last modified, in ISO 8601 format.            |   Yes    |
| `description`                  | `str`                             | A detailed description of the software's function (min 10 characters).                  |   Yes    |
| `format` (alias: `fileFormat`) | `str`                             | The file format of the software if it's a file (e.g., "Python script", "Docker image"). |   Yes    |
| `metadataType`                 | `Optional[str]`                   | The schema.org type. Defaults to `https://w3id.org/EVI#Software`.                       |    No    |
| `additionalType`               | `Optional[str]`                   | An additional type identifier. Defaults to "Software".                                  |    No    |
| `version`                      | `str`                             | The version string of the software. Defaults to "0.1.0".                                |    No    |
| `associatedPublication`        | `Optional[str]`                   | A URL or citation for a publication that describes the software.                        |    No    |
| `additionalDocumentation`      | `Optional[str]`                   | A URL for the software's documentation.                                                 |    No    |
| `usedByComputation`            | `Optional[List[IdentifierValue]]` | A list of links (by `@id`) to `Computation` entities that used this software.           |    No    |
| `contentUrl`                   | `Optional[str]`                   | A URL pointing to the software's source code, download page, or container registry.     |    No    |

### Example

```json
{
  "@id": "ark:59852/software-spectronaut-wGLsihNfp5w",
  "@type": "https://w3id.org/EVI#Software",
  "name": "Spectronaut",
  "author": "Biognosys",
  "dateModified": "2024-06-30",
  "version": "19.0",
  "description": "Spectronaut is a commercial software package developed by Biognosys for the analysis of mass spectrometry-based proteomics data.",
  "format": "unknown",
  "contentUrl": "https://biognosys.com/software/spectronaut/"
}
```
