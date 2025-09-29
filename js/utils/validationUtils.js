const Ajv = require("ajv");
const addFormats = require("ajv-formats");

// --- AJV Setup ---
const ajv = new Ajv({
  useDefaults: true,
  coerceTypes: true,
  allErrors: true,
});
addFormats(ajv);

const compiledSchemaCache = new Map();

/**
 * Validates data against a given JSON schema using AJV, applying defaults.
 * Caches compiled schemas for performance.
 * @param {object} schemaJson - The JSON schema object to validate against.
 * @param {object} data - The data object to validate.
 * @returns {object} The validated (and potentially mutated with defaults) data object.
 * @throws {Error} If the schema fails to compile or the data fails validation.
 */
function validateAgainstSchema(schemaJson, data) {
  const cacheKey = JSON.stringify(schemaJson);
  let validate;

  if (compiledSchemaCache.has(cacheKey)) {
    validate = compiledSchemaCache.get(cacheKey);
  } else {
    try {
      validate = ajv.compile(schemaJson);
      compiledSchemaCache.set(cacheKey, validate);
    } catch (e) {
      console.error("Failed to compile JSON Schema:", schemaJson);
      throw new Error(
        `Internal Error: Schema compilation failed. ${e.message}`
      );
    }
  }

  const dataToValidate = JSON.parse(JSON.stringify(data));

  if (validate(dataToValidate)) {
    return dataToValidate;
  } else {
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
