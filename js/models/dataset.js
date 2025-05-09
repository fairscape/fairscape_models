// File: fairscape_models/js/models/dataset.js

const path = require("path");
const fs = require("fs");
const { NAAN } = require("../utils/config");
const { generateDatetimeSquid } = require("../utils/guid");
const {
  findIdentifierFields,
  normalizeIdentifiers,
} = require("../utils/schemaUtils");
const { validateAgainstSchema } = require("../utils/validationUtils");
const datasetSchemaJson = require("../../json-schemas/Dataset.json");


const identifierFields = findIdentifierFields(datasetSchemaJson);

/**
 * Generates a Dataset metadata object, applying schema defaults and validation.
 * @param {Partial<DatasetType>} params - Core metadata properties (keys should match schema).
 * @param {string | null} [filepath=null] - Optional path to source file (local/URL).
 * @param {string | null} [cratePath=null] - Optional path to RO-Crate dir (needed for local filepath).
 * @returns {DatasetType} A validated Dataset object.
 * @throws {Error} If validation fails or filepath logic fails.
 */
function generateDataset(params, filepath = null, cratePath = null) {
  const nameForGuid = params.name || "temp-guid-name";
  const guid =
    params["@id"] ||
    `ark:${NAAN}/dataset-${nameForGuid
      .toLowerCase()
      .replace(/[\s:]+/g, "-")}-${generateDatetimeSquid()}`;

  const initialMetadataObject = { ...params, "@id": guid };

  identifierFields.forEach((fieldName) => {
    if (initialMetadataObject.hasOwnProperty(fieldName)) {
      const normalizedValue = normalizeIdentifiers(
        initialMetadataObject[fieldName]
      );
      if (normalizedValue !== undefined)
        initialMetadataObject[fieldName] = normalizedValue;
      else delete initialMetadataObject[fieldName];
    }
  });

  // Calculate contentUrl
  if (filepath) {
    if (/^(http:|https:|file:|Embargoed)/i.test(filepath)) {
      initialMetadataObject.contentUrl = filepath;
    } else {
      // Local file path
      if (!cratePath)
        throw new Error("`cratePath` is required for local `filepath`.");
      const rocratePathAbs = path.resolve(
        cratePath.includes("ro-crate-metadata.json")
          ? path.dirname(cratePath)
          : cratePath
      );
      const potentialFilepathAbs = path.resolve(filepath);
      const potentialFilepathRel = path.resolve(rocratePathAbs, filepath);
      let targetFilepathAbs = null;
      if (fs.existsSync(potentialFilepathAbs))
        targetFilepathAbs = potentialFilepathAbs;
      else if (fs.existsSync(potentialFilepathRel))
        targetFilepathAbs = potentialFilepathRel;
      else
        throw new Error(
          `Dataset File Does Not Exist: ${potentialFilepathAbs} or ${potentialFilepathRel}`
        );
      try {
        const relativePath = path.relative(rocratePathAbs, targetFilepathAbs);
        if (relativePath.startsWith("..") || path.isAbsolute(relativePath))
          throw new Error("File not in crate");
        initialMetadataObject.contentUrl = `file:///${relativePath.replace(
          /\\/g,
          "/"
        )}`;
      } catch (error) {
        throw new Error(`File path error relative to crate (${error.message})`);
      }
    }
  }

  Object.keys(initialMetadataObject).forEach((key) => {
    if (initialMetadataObject[key] === undefined)
      delete initialMetadataObject[key];
  });

  return validateAgainstSchema(datasetSchemaJson, initialMetadataObject);
}

module.exports = {
  generateDataset,
};
