# Instrument Model

The `Instrument` model is used to describe a physical instrument, such as a microscope or mass spectrometer, used in an experiment.

### Properties

| Property                        | Type                              | Description                                                                        | Required |
| ------------------------------- | --------------------------------- | ---------------------------------------------------------------------------------- | :------: |
| `guid` (alias: `@id`)           | `str`                             | The unique, resolvable identifier for the Instrument.                              |   Yes    |
| `name`                          | `str`                             | A human-readable name for the instrument.                                          |   Yes    |
| `manufacturer`                  | `str`                             | The company or organization that manufactured the instrument (min 4 characters).   |   Yes    |
| `model`                         | `str`                             | The model name or number of the instrument.                                        |   Yes    |
| `description`                   | `str`                             | A detailed description of the instrument and its capabilities (min 10 characters). |   Yes    |
| `metadataType` (alias: `@type`) | `Optional[str]`                   | The schema.org type. Defaults to `https://w3id.org/EVI#Instrument`.                |    No    |
| `associatedPublication`         | `Optional[str]`                   | A URL or citation for a publication that features or describes this instrument.    |    No    |
| `additionalDocumentation`       | `Optional[str]`                   | A URL to the instrument's manual or specification sheet.                           |    No    |
| `usedByExperiment`              | `Optional[List[IdentifierValue]]` | A list of links (by `@id`) to `Experiment` entities that used this instrument.     |    No    |
| `contentUrl`                    | `Optional[str]`                   | A URL pointing to a webpage about the instrument.                                  |    No    |

### Example

```json
{
  "@id": "ark:59852/instrument-timstof-pro-2-2BwpIzIY0p",
  "@type": "https://w3id.org/EVI#Instrument",
  "name": "timsTOF Pro 2",
  "manufacturer": "Bruker",
  "model": "timsTOF Pro 2",
  "description": "The timsTOF Pro 2 is a mass spectrometry instrument that combines quadrupole time-of-flight (QTOF) technology with trapped ion mobility spectrometry (TIMS).",
  "additionalDocumentation": "https://www.bruker.com/en/products-and-solutions/mass-spectrometry/timstof/timstof-pro.html"
}
```
