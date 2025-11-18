const { NAAN } = require("../utils/config");
const { generateDatetimeSquid } = require("../utils/guid");
const {
  findIdentifierFields,
  normalizeIdentifiers,
} = require("../utils/schemaUtils");
const { validateAgainstSchema } = require("../utils/validationUtils");
const annotationSchemaJson = require("../../json-schemas/Annotation.json");

const identifierFields = findIdentifierFields(annotationSchemaJson);

/**
 * Generates an Annotation metadata object, applying schema defaults and validation.
 * @param {Partial<AnnotationType>} params - Core metadata properties (keys should match schema).
 * @returns {AnnotationType} A validated Annotation object.
 * @throws {Error} If validation fails.
 */
function generateAnnotation(params) {
  const nameForGuid = params.name || "temp-guid-name";
  const guid =
    params["@id"] ||
    `ark:${NAAN}/annotation-${nameForGuid
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
  return validateAgainstSchema(annotationSchemaJson, initialMetadataObject);
}

module.exports = {
  generateAnnotation,
};
