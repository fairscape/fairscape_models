// File: fairscape_models/js/utils/schemaUtils.js

/**
 * Checks if a JSON schema part represents or references an IdentifierValue.
 * NOTE: Adjust '$ref' path if your IdentifierValue definition is different.
 * @param {object | null | undefined} schemaPart - A part of a JSON schema.
 * @returns {boolean} - True if it represents an IdentifierValue.
 */
const isIdentifierRef = (schemaPart) => {
  if (!schemaPart) return false;
  // Direct reference check
  if (
    schemaPart.$ref === "#/$defs/IdentifierValue" ||
    schemaPart.$ref === "../Dataset.json#/$defs/IdentifierValue" ||
    schemaPart.$ref === "../Computation.json#/$defs/IdentifierValue"
  )
    return true; // Added Computation specific ref
  // Check within anyOf/oneOf constructs
  if (Array.isArray(schemaPart.anyOf))
    return schemaPart.anyOf.some(isIdentifierRef);
  if (Array.isArray(schemaPart.oneOf))
    return schemaPart.oneOf.some(isIdentifierRef);
  return false;
};

/**
 * Analyzes a JSON schema's properties to find fields that represent IdentifierValues.
 * @param {object} schemaJson - The loaded JSON schema object.
 * @returns {string[]} - An array of property names that represent IdentifierValues.
 */
const findIdentifierFields = (schemaJson) => {
  const identifierFields = [];
  if (schemaJson && schemaJson.properties) {
    for (const fieldName in schemaJson.properties) {
      const propSchema = schemaJson.properties[fieldName];
      let checkPart = propSchema;
      // If it's an array, check the items definition
      if (propSchema.type === "array" && propSchema.items) {
        checkPart = propSchema.items;
      }
      // Check the part identified (item schema or property schema) and also check anyOf/oneOf on the top-level property
      if (
        isIdentifierRef(checkPart) ||
        (Array.isArray(propSchema.anyOf) &&
          propSchema.anyOf.some(isIdentifierRef)) ||
        (Array.isArray(propSchema.oneOf) &&
          propSchema.oneOf.some(isIdentifierRef))
      ) {
        identifierFields.push(fieldName);
      }
    }
  }
  return identifierFields;
};

/**
 * Normalizes input values intended to be IdentifierValue(s) to the { "@id": "..." } format.
 * Handles strings, objects with @id, and arrays of these. Returns structure mirroring input.
 * @param {any} input - The value to normalize.
 * @returns {object | object[] | undefined} - Normalized value(s) or undefined if invalid/empty.
 */
const normalizeIdentifiers = (input) => {
  if (input === null || input === undefined) return undefined;

  const processItem = (item) => {
    if (typeof item === "string" && item.trim()) return { "@id": item.trim() };
    if (
      typeof item === "object" &&
      item !== null &&
      typeof item["@id"] === "string" &&
      item["@id"].trim()
    )
      return { "@id": item["@id"].trim() };
    return null; // Invalid format
  };

  if (Array.isArray(input)) {
    const normalized = input.map(processItem).filter((i) => i !== null);
    return normalized.length > 0 ? normalized : undefined;
  } else {
    const normalized = processItem(input);
    return normalized !== null ? normalized : undefined;
  }
};

module.exports = {
  findIdentifierFields,
  normalizeIdentifiers,
};
