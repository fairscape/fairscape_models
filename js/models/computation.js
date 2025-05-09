// File: fairscape_models/js/models/computation.js

const { NAAN } = require("../utils/config");
const { generateDatetimeSquid } = require("../utils/guid");
const {
  findIdentifierFields,
  normalizeIdentifiers,
} = require("../utils/schemaUtils");
const { validateAgainstSchema } = require("../utils/validationUtils");
const computationSchemaJson = require("../../json-schemas/Computation.json");

const identifierFields = findIdentifierFields(computationSchemaJson);

/**
 * Generates a Computation metadata object, applying schema defaults and validation.
 * @param {Partial<ComputationType>} params - Core metadata properties (keys should match schema).
 * @returns {ComputationType} A validated Computation object.
 * @throws {Error} If validation fails.
 */
function generateComputation(params) {
  const nameForGuid = params.name || "temp-guid-name";
  const guid =
    params["@id"] ||
    `ark:${NAAN}/computation-${nameForGuid
      .toLowerCase()
      .replace(/[\s:]+/g, "-")}-${generateDatetimeSquid()}`;

  const initialMetadataObject = { ...params, "@id": guid };

  // Normalize identifier fields identified from schema
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

  // Clean undefined keys before validation
  Object.keys(initialMetadataObject).forEach((key) => {
    if (initialMetadataObject[key] === undefined)
      delete initialMetadataObject[key];
  });

  // Validate and apply defaults using the utility function
  return validateAgainstSchema(computationSchemaJson, initialMetadataObject);
}

module.exports = {
  generateComputation,
};
