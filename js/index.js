const {
  generateEvidenceGraphs,
} = require("./rocrate/evidence_graph_builder.js");

const { generateComputation } = require("./models/computation.js");

const { generateDataset } = require("./models/dataset.js");
const { generateSoftware } = require("./models/software.js");
const { Schema, generateSchema, addProperty } = require("./models/schema.js");

const {
  generateROCrate,
  readROCrateMetadata,
  appendCrate,
} = require("./models/rocrate.js");

const {
  get_ro_crate_metadata,
  register_schema,
  get_registered_files,
  rocrate_init,
  rocrate_create,
  register_software,
  register_dataset,
  register_computation,
} = require("./rocrate/rocrate.js");

// Constants
const DEFAULT_CONTEXT = {
  "@vocab": "https://schema.org/",
  sh: "http://www.w3.org/ns/shacl#",
  EVI: "https://w3id.org/EVI#",
};
const NAAN = "59852";

// Export everything
module.exports = {
  // Evidence Graph Builder exports
  generateEvidenceGraphs,

  // Computation exports
  generateComputation,

  // Dataset exports
  generateDataset,

  // ROCrate core functionality
  generateROCrate,
  readROCrateMetadata,
  appendCrate,

  // Software exports
  generateSoftware,

  // Schema exports
  Schema,
  generateSchema,
  addProperty,

  // High-level ROCrate functions
  get_ro_crate_metadata,
  register_schema,
  get_registered_files,
  rocrate_init,
  rocrate_create,
  register_software,
  register_dataset,
  register_computation,
};
