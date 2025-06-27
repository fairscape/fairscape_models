# Experiment Model

The `Experiment` model is used to describe a physical, non-computational process, such as a wet-lab experiment. It captures key details about the experimental setup, including the instruments and samples used, and links to the data it generated.

### Properties

| Property                        | Type                              | Description                                                                          | Required |
| ------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------ | :------: |
| `guid` (alias: `@id`)           | `str`                             | The unique, resolvable identifier for the Experiment. Should be an ARK.              |   Yes    |
| `name`                          | `str`                             | A human-readable name for the experiment.                                            |   Yes    |
| `experimentType`                | `str`                             | The type of experiment performed (e.g., "Immunofluorescence Staining", "SEC-MS").    |   Yes    |
| `runBy`                         | `str`                             | The person, lab, or organization that performed the experiment.                      |   Yes    |
| `description`                   | `str`                             | A detailed description of the experimental protocol and purpose (min 10 characters). |   Yes    |
| `datePerformed`                 | `str`                             | The date the experiment was performed, in ISO 8601 format.                           |   Yes    |
| `metadataType` (alias: `@type`) | `Optional[str]`                   | The schema.org type. Defaults to `https://w3id.org/EVI#Experiment`.                  |    No    |
| `associatedPublication`         | `Optional[str]`                   | A URL or citation for a publication that describes this experiment.                  |    No    |
| `protocol`                      | `Optional[str]`                   | A URL pointing to a detailed experimental protocol.                                  |    No    |
| `usedInstrument`                | `Optional[List[IdentifierValue]]` | A list of links (by `@id`) to the `Instrument` entities used.                        |    No    |
| `usedSample`                    | `Optional[List[IdentifierValue]]` | A list of links (by `@id`) to the `Sample` entities used.                            |    No    |
| `usedTreatment`                 | `Optional[List[IdentifierValue]]` | A list of links (by `@id`) to `BioChemEntity` entities applied as treatments.        |    No    |
| `usedStain`                     | `Optional[List[IdentifierValue]]` | A list of links (by `@id`) to `BioChemEntity` entities used as stains.               |    No    |
| `generated`                     | `Optional[List[IdentifierValue]]` | A list of links (by `@id`) to the `Dataset` entities produced by this experiment.    |    No    |

### Example

```json
{
  "@id": "ark:59852/experiment-control-1-sec-ms-mda-mb468",
  "@type": "https://w3id.org/EVI#Experiment",
  "name": "Control Experiment 1: SEC-MS of MDA-MB468 following no treatment",
  "experimentType": "Size Exclusion Chromatography-Mass Spectrometry",
  "runBy": "Krogan Laboratory, UCSF",
  "description": "SEC-MS profiling of MDA-MB468 breast cancer cell line following treatment with vorinostat or paclitaxel. Each SEC-MS set is composed of 72 fractions.",
  "datePerformed": "2024-07-04",
  "usedInstrument": [
    {
      "@id": "ark:59852/instrument-timstof-pro-2-2BwpIzIY0p"
    }
  ],
  "usedSample": [
    {
      "@id": "ark:59852/sample-MDA-MB-468-cell-line-mass-spec-sample-oPzB4vOldoF"
    }
  ],
  "generated": [
    {
      "@id": "ark:59852/dataset-control-1-sec-ms-mda-mb468"
    }
  ]
}
```
