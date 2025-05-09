// File: fairscape_models/js/models/rocrate.js

const fs = require("fs");
const path = require("path");
const { NAAN, DEFAULT_CONTEXT } = require("../utils/config");
const { generateDatetimeSquid } = require("../utils/guid");
const {
  findIdentifierFields,
  normalizeIdentifiers,
} = require("../utils/schemaUtils");
const { validateAgainstSchema } = require("../utils/validationUtils");

// Load the schemas
const rocrateMetadataElemSchemaJson = require("../../json-schemas/ROCrateMetadataElem.json");
const rocrateMetadataFileElemSchemaJson = require("../../json-schemas/ROCrateMetadataFileElem.json");

// Pre-process ROCrateMetadataElem schema for identifier fields
const rocrateRootIdentifierFields = findIdentifierFields(
  rocrateMetadataElemSchemaJson
);

/**
 * Generates and writes an ro-crate-metadata.json file.
 * The structure of rootDatasetParams should align with the ROCrateMetadataElem schema.
 *
 * @param {string} cratePath - Path to the RO-Crate directory where ro-crate-metadata.json will be written.
 * @param {Partial<ROCrateMetadataElemType>} rootDatasetParams - Parameters for the RO-Crate's root dataset entity.
 * @returns {ROCrateMetadataElemType} The validated root dataset metadata element.
 * @throws {Error} If 'cratePath' is missing, or if 'name' is missing when '@id' is not provided, or if validation fails.
 */
function generateROCrate(cratePath, rootDatasetParams) {
  if (!cratePath) throw new Error("Parameter 'cratePath' is required.");
  if (!rootDatasetParams)
    throw new Error("Parameter 'rootDatasetParams' is required.");

  // Ensure either '@id' or 'name' (for GUID generation) is present
  if (!rootDatasetParams["@id"] && !rootDatasetParams.name) {
    throw new Error(
      "Either '@id' or 'name' must be provided in rootDatasetParams for RO-Crate generation."
    );
  }

  const finalGuid =
    rootDatasetParams["@id"] ||
    `ark:${NAAN}/rocrate-${rootDatasetParams.name
      .toLowerCase()
      .replace(/[\s:]+/g, "-")}-${generateDatetimeSquid()}`;

  // Prepare the root dataset object for validation
  let processedRootDatasetParams = {
    ...rootDatasetParams, // Spread all provided parameters
    "@id": finalGuid,
  };

  // Normalize any identifier fields present in the input parameters
  rocrateRootIdentifierFields.forEach((fieldName) => {
    if (processedRootDatasetParams.hasOwnProperty(fieldName)) {
      const normalizedValue = normalizeIdentifiers(
        processedRootDatasetParams[fieldName]
      );
      if (normalizedValue !== undefined) {
        processedRootDatasetParams[fieldName] = normalizedValue;
      } else {
        delete processedRootDatasetParams[fieldName];
      }
    }
  });

  // Clean undefined keys before validation (AJV generally handles this, but good practice)
  Object.keys(processedRootDatasetParams).forEach((key) => {
    if (processedRootDatasetParams[key] === undefined)
      delete processedRootDatasetParams[key];
  });

  const validatedRootDataset = validateAgainstSchema(
    rocrateMetadataElemSchemaJson,
    processedRootDatasetParams
  );

  const metadataFileDescriptorParams = {
    "@id": "ro-crate-metadata.json",
    conformsTo: { "@id": "https://w3id.org/ro/crate/1.1" }, // Defaulting to 1.1
    about: { "@id": finalGuid },
  };
  const validatedMetadataFileDescriptor = validateAgainstSchema(
    rocrateMetadataFileElemSchemaJson,
    metadataFileDescriptorParams
  );

  const roCrateInstanceMetadata = {
    "@context": DEFAULT_CONTEXT,
    "@graph": [validatedMetadataFileDescriptor, validatedRootDataset],
  };

  // Write to file
  let roCrateMetadataFilePath;
  if (cratePath.endsWith("ro-crate-metadata.json")) {
    roCrateMetadataFilePath = path.resolve(cratePath);
    fs.mkdirSync(path.dirname(roCrateMetadataFilePath), { recursive: true });
  } else {
    roCrateMetadataFilePath = path.resolve(cratePath, "ro-crate-metadata.json");
    fs.mkdirSync(path.resolve(cratePath), { recursive: true });
  }

  fs.writeFileSync(
    roCrateMetadataFilePath,
    JSON.stringify(roCrateInstanceMetadata, null, 2)
  );

  return validatedRootDataset;
}

/**
 * Reads the ro-crate-metadata.json file.
 * @param {string} cratePath - Path to the RO-Crate directory or the metadata file itself.
 * @returns {ROCrateV1_2Type} The parsed RO-Crate metadata object.
 * @throws {Error} If the file cannot be read or parsed.
 */
function readROCrateMetadata(cratePath) {
  const metadataFilePath = cratePath.endsWith("ro-crate-metadata.json")
    ? path.resolve(cratePath)
    : path.resolve(cratePath, "ro-crate-metadata.json");

  if (!fs.existsSync(metadataFilePath)) {
    throw new Error(`RO-Crate metadata file not found: ${metadataFilePath}`);
  }
  const rawData = fs.readFileSync(metadataFilePath, "utf8");
  return JSON.parse(rawData);
}

/**
 * Appends new metadata elements to an existing RO-Crate.
 * @param {string} cratePath - Path to the RO-Crate directory or its metadata file.
 * @param {Array<object>} elementsToAdd - An array of metadata objects to add.
 * @throws {Error} If the crate cannot be read/written or if elementsToAdd is not an array.
 */
function appendCrate(cratePath, elementsToAdd) {
  if (!Array.isArray(elementsToAdd) || elementsToAdd.length === 0) {
    console.warn("No elements provided to appendCrate.");
    return;
  }

  const metadataFilePath = cratePath.endsWith("ro-crate-metadata.json")
    ? path.resolve(cratePath)
    : path.resolve(cratePath, "ro-crate-metadata.json");

  const roCrateMetadata = readROCrateMetadata(metadataFilePath);

  const descriptor = roCrateMetadata["@graph"].find(
    (e) => e["@id"] === "ro-crate-metadata.json"
  );
  if (!descriptor || !descriptor.about || !descriptor.about["@id"]) {
    throw new Error(
      "Invalid RO-Crate structure: Cannot find root dataset reference in descriptor."
    );
  }
  const rootDatasetId = descriptor.about["@id"];
  const rootDataset = roCrateMetadata["@graph"].find(
    (e) => e["@id"] === rootDatasetId
  );

  if (!rootDataset) {
    throw new Error(
      `Invalid RO-Crate structure: Root dataset with ID '${rootDatasetId}' not found.`
    );
  }

  if (!Array.isArray(rootDataset.hasPart)) {
    rootDataset.hasPart = [];
  }
  const existingHasPartIds = new Set(rootDataset.hasPart.map((p) => p["@id"]));
  const existingGraphIds = new Set(
    roCrateMetadata["@graph"].map((e) => e["@id"])
  );

  elementsToAdd.forEach((element) => {
    if (!element || !element["@id"]) {
      console.warn("Skipping element with no @id:", element);
      return;
    }
    if (!existingGraphIds.has(element["@id"])) {
      roCrateMetadata["@graph"].push(element);
      existingGraphIds.add(element["@id"]);
    }
    if (!existingHasPartIds.has(element["@id"])) {
      rootDataset.hasPart.push({ "@id": element["@id"] });
      existingHasPartIds.add(element["@id"]);
    }
  });

  fs.writeFileSync(metadataFilePath, JSON.stringify(roCrateMetadata, null, 2));
}

module.exports = {
  generateROCrate,
  readROCrateMetadata,
  appendCrate,
};
