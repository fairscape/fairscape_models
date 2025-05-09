// File: fairscape_models/js/utils/validationUtils.js

const Ajv = require("ajv");
const addFormats = require("ajv-formats");

// --- AJV Setup ---
// Create a single Ajv instance
const ajv = new Ajv({
  useDefaults: true, // Apply defaults from the schema
  coerceTypes: true, // Coerce types where possible
  allErrors: true, // Collect all validation errors
});
addFormats(ajv); // Add standard formats like date-time, uri, etc.

// Cache for compiled schemas to avoid recompiling every time
const compiledSchemaCache = new Map();
// --- End AJV Setup ---

/**
 * Validates data against a given JSON schema using AJV, applying defaults.
 * Caches compiled schemas for performance.
 * @param {object} schemaJson - The JSON schema object to validate against.
 * @param {object} data - The data object to validate.
 * @returns {object} The validated (and potentially mutated with defaults) data object.
 * @throws {Error} If the schema fails to compile or the data fails validation.
 */
function validateAgainstSchema(schemaJson, data) {
  const cacheKey = JSON.stringify(schemaJson); // Use schema content as cache key
  let validate;

  if (compiledSchemaCache.has(cacheKey)) {
    validate = compiledSchemaCache.get(cacheKey);
  } else {
    try {
      validate = ajv.compile(schemaJson);
      compiledSchemaCache.set(cacheKey, validate);
    } catch (e) {
      console.error("Failed to compile JSON Schema:", schemaJson); // Log the problematic schema
      throw new Error(
        `Internal Error: Schema compilation failed. ${e.message}`
      );
    }
  }

  // Deep copy data before validation as ajv mutates it with defaults
  const dataToValidate = JSON.parse(JSON.stringify(data));

  if (validate(dataToValidate)) {
    return dataToValidate; // Validation successful, defaults applied
  } else {
    // Validation failed
    console.error("Object Failed Validation:", dataToValidate);
    console.error("AJV Errors:", JSON.stringify(validate.errors, null, 2));
    const errorDetails = validate.errors
      ?.map((e) => `(${e.instancePath || "/"} ${e.message})`)
      .join("; ");
    throw new Error(`Generated metadata invalid: ${errorDetails}`);
  }
}

module.exports = {
  validateAgainstSchema,
};
