# Changelog


## [1.1.7] - 2026-06-30

Corrected regex for `fairscape_models.fairscape_base.IdentifierPattern`

## [1.1.6] - 2026-06-30

Uses the Base Class `fairscape_models.fairscape_base.Identifier` to preprocess ARK identifiers in the `guid` and `isPartOf` properties. This Base Class also uses a regex to validate ARK identifiers.

## [1.0.29] - 2026-03-20

Added D4DConverter class for converting ROCrateV1_2 into LinkML D4D yaml.
Added dependency PyYaml

Class for ROCrates now has default context set by default. Default context contained inside `fairscape_models.fairscape_base.DEFAULT_CONTEXT` is default for `fairscape_models.rocrate.ROCrateV1_2` property `context`. 

Added a bound method `generateFileElem` to `fairscape_models.rocrate.ROCrateMetadataElem` to generate the `fairscape_models.rocrate.ROCrateFileElem` required in an ROCrate.

## [1.0.24] - 2026-02-16

Added a property `fairscapeVersion` to all classes which is set to the version of this models package.