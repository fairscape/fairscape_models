// File: src/rocrate/rocrate.js

const path = require("path");
const fs = require("fs");
const {
  generateROCrate,
  readROCrateMetadata,
  appendCrate,
} = require("../models/rocrate");
const { generateSoftware } = require("../models/software.js");
const { generateDataset } = require("../models/dataset.js");
const { generateComputation } = require("../models/computation.js");
const { generateSchema } = require("../models/schema.js");

function copyToROCrate(sourceFilepath, destinationFilepath) {
  if (!sourceFilepath || !destinationFilepath) {
    throw new Error(
      "Source and destination filepaths are required for copyToROCrate."
    );
  }
  if (!fs.existsSync(sourceFilepath)) {
    throw new Error(`Source file does not exist: ${sourceFilepath}`);
  }
  try {
    fs.mkdirSync(path.dirname(destinationFilepath), { recursive: true });
    fs.copyFileSync(sourceFilepath, destinationFilepath);
  } catch (error) {
    throw new Error(
      `Failed to copy file from ${sourceFilepath} to ${destinationFilepath}: ${error.message}`
    );
  }
}

function get_ro_crate_metadata(rocratePath) {
  return readROCrateMetadata(rocratePath);
}

function register_schema(
  rocrate_path,
  name,
  description,
  properties,
  required,
  separator,
  header,
  guid = null,
  additionalProperties = true,
  examples = []
) {
  try {
    const schema_instance = generateSchema({
      "@id": guid,
      name,
      description,
      properties,
      required,
      separator,
      header,
      additionalProperties,
      examples,
    });
    appendCrate(rocrate_path, [schema_instance]);
    return schema_instance["@id"];
  } catch (error) {
    throw new Error(`Error registering schema: ${error.message}`);
  }
}

async function get_registered_files(rocratePath) {
  try {
    if (!rocratePath) {
      throw new Error("Please select an RO-Crate directory.");
    }
    const metadata = readROCrateMetadata(rocratePath);

    const registeredFiles = metadata["@graph"]
      .filter((item) => item.contentUrl && item["@type"] !== "CreativeWork") // Assuming 'CreativeWork' is the descriptor type
      .map((item) => ({
        guid: item["@id"],
        name: item.contentUrl.replace(/^file:\/\/\//, "").replace(/\\/g, "/"),
      }));
    return registeredFiles;
  } catch (error) {
    throw new Error(
      `Error reading RO-Crate for registered files: ${error.message}`
    );
  }
}

function rocrate_init(
  name,
  organization_name,
  project_name,
  description,
  keywords,
  author,
  license = "https://creativecommons.org/licenses/by/4.0/",
  version = "1.0.0",
  guid = ""
) {
  const rootDatasetParams = {
    name,
    description,
    keywords,
    author,
    license,
    version,
  };
  if (guid) rootDatasetParams["@id"] = guid;
  const isPartOf = [];
  if (organization_name) {
    if (organization_name)
      rootDatasetParams.organizationName = organization_name;
    if (project_name) rootDatasetParams.projectName = project_name;
  }

  const rocrateRootDir = process.cwd();
  const createdRootDataset = generateROCrate(rocrateRootDir, rootDatasetParams);
  return createdRootDataset["@id"];
}

function rocrate_create(
  rocrate_path,
  name,
  description,
  keywords,
  author,
  license = "https://creativecommons.org/licenses/by/4.0/",
  version = "1.0.0",
  guid = "",
  organizationName = null,
  projectName = null,
  datePublished = null,
  ...otherRootProps
) {
  if (typeof keywords === "string") {
    keywords = keywords.split(",").map((keyword) => keyword.trim());
  }

  const rootDatasetParams = {
    name,
    description,
    author,
    keywords,
    version,
    license,
    datePublished,
    ...otherRootProps,
  };
  if (guid) rootDatasetParams["@id"] = guid;

  const isPartOf = [];
  if (organizationName) isPartOf.push({ "@id": organizationName }); // Assuming organizationName is an ARK/GUID
  if (projectName) isPartOf.push({ "@id": projectName }); // Assuming projectName is an ARK/GUID
  if (isPartOf.length > 0) rootDatasetParams.isPartOf = isPartOf;

  const createdRootDataset = generateROCrate(rocrate_path, rootDatasetParams);
  return createdRootDataset["@id"];
}

function register_software(rocrate_path, softwareParams, filepath = null) {
  try {
    const software_instance = generateSoftware(
      softwareParams,
      filepath,
      rocrate_path
    );
    appendCrate(rocrate_path, [software_instance]);
    return software_instance["@id"];
  } catch (error) {
    throw new Error(`Error registering software: ${error.message}`);
  }
}

function register_dataset(rocrate_path, datasetParams, filepath = null) {
  try {
    const dataset_instance = generateDataset(
      datasetParams,
      filepath,
      rocrate_path
    );
    appendCrate(rocrate_path, [dataset_instance]);
    return dataset_instance["@id"];
  } catch (error) {
    throw new Error(`Error registering dataset: ${error.message}`);
  }
}

function register_computation(rocrate_path, computationParams) {
  try {
    const computationInstance = generateComputation(computationParams);
    appendCrate(rocrate_path, [computationInstance]);
    return computationInstance["@id"];
  } catch (error) {
    throw new Error(`Error registering computation: ${error.message}`);
  }
}

module.exports = {
  get_ro_crate_metadata,
  register_schema,
  get_registered_files,
  rocrate_init,
  rocrate_create,
  register_software,
  register_dataset,
  register_computation,
};
