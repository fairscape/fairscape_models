// File: fairscape_models/js/utils/guid.js

const { v4: uuidv4 } = require("uuid");
const { NAAN } = require("./config");

/**
 * Generates a short, somewhat time-based, somewhat random part for a GUID
 * using the first block of a UUID v4.
 * @returns {string} A short pseudo-random string.
 */
function generateDatetimeSquid() {
  return uuidv4().split("-")[0];
}

/**
 * Generates a full ARK-formatted GUID with a given prefix and a datetime-based SQUID.
 * Example: ark:59852/dataset-my-data-a1b2c3d4
 *
 * @param {string} prefix - The prefix for the GUID (e.g., "dataset-my-data").
 * @returns {string} The generated ARK.
 */
function generatePrefixedGUID(prefix) {
  if (!prefix || typeof prefix !== "string" || !prefix.trim()) {
    throw new Error(
      "A valid prefix string is required for generatePrefixedGUID."
    );
  }
  const sq = generateDatetimeSquid();
  const sanitizedPrefix = prefix.toLowerCase().replace(/[\s:]+/g, "-");
  return `ark:${NAAN}/${sanitizedPrefix}-${sq}`;
}

module.exports = {
  generateDatetimeSquid,
  generatePrefixedGUID,
};
