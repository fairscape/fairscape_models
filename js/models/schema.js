const path = require("path");
const { v4: uuidv4 } = require("uuid");
const NAAN = "59852";

function generateDatetimeSquid() {
  return uuidv4().split("-")[0];
}

class Schema {
  constructor(data) {
    this["@id"] = data["@id"] || null;
    this["@context"] = data["@context"] || {
      "@vocab": "https://schema.org/",
      EVI: "https://w3,org/EVI#",
    };
    this["@type"] = data["@type"] || "EVI:Schema";
    this.schema = data.schema || "https://json-schema.org/draft/2020-12/schema";
    this.name = data.name;
    this.description = data.description;
    this.properties = data.properties || {};
    this.datatype = data.type || "object";
    this.additionalProperties =
      data.additionalProperties !== undefined
        ? data.additionalProperties
        : true;
    this.required = data.required || [];
    this.separator = data.separator;
    this.header = data.header !== undefined ? data.header : false;
    this.examples = data.examples || [];
  }
}

function generateSchema({
  guid,
  name,
  description,
  properties,
  required,
  separator,
  header,
  examples,
  additionalProperties,
}) {
  if (!guid) {
    const sq = generateDatetimeSquid();
    guid = `ark:${NAAN}/schema-${name
      .toLowerCase()
      .replace(/\s+/g, "-")}-${sq}`;
  }
  const schemaMetadata = new Schema({
    "@id": guid,
    name,
    description,
    properties,
    required,
    separator,
    header,
    examples,
    additionalProperties,
  });

  return schemaMetadata;
}

function addProperty(schema, propertyName, propertyData) {
  console.log("I was called!!");
  if (validateProperty(propertyData)) {
    schema.properties[propertyName] = propertyData;
    if (!schema.required.includes(propertyName)) {
      schema.required.push(propertyName);
    }
  } else {
    throw new Error(`Invalid property data for ${propertyName}`);
  }
}

module.exports = {
  Schema,
  generateSchema,
  addProperty,
};
