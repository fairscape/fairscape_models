function generateEvidenceGraphs(data) {
  const graph = data["@graph"];
  const idToElement = new Map();
  const idToDepth = new Map();

  // Function to extract ARK prefix
  const getArkPrefix = (id) => {
    const match = id.match(/^(ark:\d+)\/.*/);
    return match ? match[1] : "ark:59852"; // Default to 'ark:59852' if no match
  };

  // Function to create evidence graph ID
  const createEvidenceGraphId = (elementId) => {
    const arkPrefix = getArkPrefix(elementId);
    const baseId = elementId.replace(/^ark:\d+\//, "");
    return `${arkPrefix}/evidence-graph-${baseId}`;
  };

  // First pass: create a map of id to element
  graph.forEach((element) => {
    if (element["@id"]) {
      idToElement.set(element["@id"], element);
    } else if (element["guid"]) {
      idToElement.set(element["guid"], element);
    }
  });

  // Add generatedBy to datasets based on computations
  graph.forEach((element) => {
    if (
      element["@type"] === "https://w3id.org/EVI#Computation" &&
      element["generated"]
    ) {
      element["generated"].forEach((datasetId) => {
        const dataset = idToElement.get(datasetId);
        if (dataset && !dataset["generatedBy"]) {
          dataset["generatedBy"] = element["@id"];
        }
      });
    }
  });

  // Function to recursively expand references and calculate depth
  function expandReferences(references, visited = new Set(), depth = 0) {
    return references.map((ref) => {
      if (visited.has(ref)) return { "@id": ref }; // Prevent circular references
      visited.add(ref);
      const element = idToElement.get(ref);
      if (!element) return { "@id": ref };

      const expanded = { ...element };
      let maxChildDepth = depth;

      if (expanded["generatedBy"]) {
        expanded["generatedBy"] = expandReferences(
          Array.isArray(expanded["generatedBy"])
            ? expanded["generatedBy"]
            : [expanded["generatedBy"]],
          new Set(visited),
          depth + 1
        );
        maxChildDepth = Math.max(maxChildDepth, depth + 1);
      }
      if (expanded["usedDataset"]) {
        expanded["usedDataset"] = expandReferences(
          expanded["usedDataset"],
          new Set(visited),
          depth + 1
        );
        maxChildDepth = Math.max(maxChildDepth, depth + 1);
      }
      if (expanded["usedSoftware"]) {
        expanded["usedSoftware"] = expandReferences(
          expanded["usedSoftware"],
          new Set(visited),
          depth + 1
        );
        maxChildDepth = Math.max(maxChildDepth, depth + 1);
      }

      idToDepth.set(ref, maxChildDepth);
      return expanded;
    });
  }

  // Second pass: create evidence graphs
  const evidenceGraphs = graph.map((element) => {
    const elementId = element["@id"] || element["guid"];
    const evidenceGraphId = createEvidenceGraphId(elementId);
    let evidenceGraph = {
      "@id": evidenceGraphId,
      "@type": "EVI:EvidenceGraph",
      name: `${element["name"] || elementId}`,
      description: `${element["name"] || elementId}`,
    };

    if (element["generatedBy"]) {
      evidenceGraph["generatedBy"] = expandReferences(
        Array.isArray(element["generatedBy"])
          ? element["generatedBy"]
          : [element["generatedBy"]]
      );
    }
    if (element["usedDataset"]) {
      evidenceGraph["usedDataset"] = expandReferences(element["usedDataset"]);
    }
    if (element["usedSoftware"]) {
      evidenceGraph["usedSoftware"] = expandReferences(element["usedSoftware"]);
    }

    // Add reference to the evidence graph in the original element
    element["hasEvidenceGraph"] = evidenceGraphId;
    return evidenceGraph;
  });

  // Find the deepest evidence graph
  let deepestGraphId = null;
  let maxDepth = -1;
  idToDepth.forEach((depth, id) => {
    if (depth > maxDepth) {
      maxDepth = depth;
      deepestGraphId = id;
    }
  });

  // Add the deepest evidence graph to the RO-Crate metadata (data object)
  if (deepestGraphId) {
    data["hasEvidenceGraph"] = createEvidenceGraphId(deepestGraphId);
  }

  // Add evidence graphs to the main graph
  data["@graph"] = [...graph, ...evidenceGraphs];
  return data;
}

module.exports = { generateEvidenceGraphs };
