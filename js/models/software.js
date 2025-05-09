// File: fairscape_models/js/models/software.js

const path = require("path");
const fs = require("fs");
const { NAAN } = require("../utils/config");
const { generateDatetimeSquid } = require("../utils/guid");
const {
  findIdentifierFields,
  normalizeIdentifiers,
} = require("../utils/schemaUtils");
const { validateAgainstSchema } = require("../utils/validationUtils");
const softwareSchemaJson = require("../../json-schemas/Software.json");

// Pre-process schema on module load
const identifierFields = findIdentifierFields(softwareSchemaJson);

/**
 * Generates a Software metadata object, applying schema defaults and validation.
 * @param {Partial<SoftwareType>} params - Core metadata properties (keys should match schema).
 * @param {string | null} [filepath=null] - Optional path to source file (local/URL).
 * @param {string | null} [cratePath=null] - Optional path to RO-Crate dir (needed for local filepath).
 * @returns {SoftwareType} A validated Software object.
 * @throws {Error} If validation fails or filepath logic fails.
 */
function generateSoftware(params, filepath = null, cratePath = null) {
  const nameForGuid = params.name || "temp-guid-name";
  const guid =
    params["@id"] ||
    `ark:${NAAN}/software-${nameForGuid
      .toLowerCase()
      .replace(/[\s:]+/g, "-")}-${generateDatetimeSquid()}`;

  const initialMetadataObject = {
    ...params,
    "@id": guid,
  };

  // Normalize identifier fields identified from schema
  identifierFields.forEach((fieldName) => {
    if (initialMetadataObject.hasOwnProperty(fieldName)) {
      const normalizedValue = normalizeIdentifiers(
        initialMetadataObject[fieldName]
      );
      if (normalizedValue !== undefined) {
        initialMetadataObject[fieldName] = normalizedValue;
      } else {
        delete initialMetadataObject[fieldName];
      }
    }
  });

  // Calculate contentUrl if filepath is provided
  if (filepath) {
    if (/^(http:|https:|file:|Embargoed)/i.test(filepath)) {
      initialMetadataObject.contentUrl = filepath;
    } else {
      // Local file path
      if (!cratePath) {
        throw new Error(
          "`cratePath` is required for local `filepath` when generating Software metadata."
        );
      }
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
          `Software File Does Not Exist: ${potentialFilepathAbs} or ${potentialFilepathRel}`
        );

      try {
        const relativePath = path.relative(rocratePathAbs, targetFilepathAbs);
        if (relativePath.startsWith("..") || path.isAbsolute(relativePath)) {
          throw new Error(
            `File not in crate: ${targetFilepathAbs} is outside of ${rocratePathAbs}`
          );
        }
        initialMetadataObject.contentUrl = `file:///${relativePath.replace(
          /\\/g,
          "/"
        )}`;
      } catch (error) {
        throw new Error(
          `File path error relative to crate for Software (${error.message})`
        );
      }
    }
  }

  // Clean undefined keys before validation
  Object.keys(initialMetadataObject).forEach((key) => {
    if (initialMetadataObject[key] === undefined)
      delete initialMetadataObject[key];
  });

  // Validate and apply defaults using the utility function
  return validateAgainstSchema(softwareSchemaJson, initialMetadataObject);
}

module.exports = {
  generateSoftware,
};
