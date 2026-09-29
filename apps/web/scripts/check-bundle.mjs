import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";
import { join } from "node:path";

const dist = fileURLToPath(new URL("../dist/", import.meta.url));
const manifest = JSON.parse(readFileSync(join(dist, ".vite/manifest.json"), "utf8"));
const heavyByChunk = JSON.parse(readFileSync(join(dist, "heavy-dependencies.json"), "utf8"));
const entryKey = "index.html";
const projectKey = "src/product/PersistentProjectsPage.tsx";
const lightweightRoutes = ["src/product/HomePage.tsx", "src/product/OpportunityPages.tsx", "src/product/LearningWorkspace.tsx", "src/product/SystemAssetsKnowledgePage.tsx", "src/product/ProductSettingsPage.tsx", "src/product/PersistentProductionPage.tsx"];
const excludedRoutes = [
  "src/product/PersistentProjectPage.tsx",
  "src/product/PersistentProductionPage.tsx",
  "src/pages/Workspace.tsx",
  "src/pages/Workflows.tsx",
];
const textStudioKey = "src/product/TextStudioShell.tsx";
const graphicModelKey = "src/product/GraphicStudioModel.ts";
const videoModelKey = "src/product/VideoStudioModel.ts";
const siblingStudioKeys = ["src/product/GraphicStudioShell.tsx", "src/product/VideoStudioShell.tsx"];
const limit = 500_000;
const baseline = 1_095_280;

function resolveKey(key) {
  if (manifest[key]) return key;
  if (key === "src/product/PersistentProductionPage.tsx") {
    const aliases = Object.entries(manifest).filter(([, record]) => record.isDynamicEntry && record.name === "PersistentProductionPage");
    if (aliases.length === 1) return aliases[0][0];
  }
  throw new Error(`Missing JS manifest mapping: ${key}`);
}

function required(key) {
  const record = manifest[resolveKey(key)];
  if (!record?.file?.endsWith(".js")) throw new Error(`Missing JS manifest mapping: ${key}`);
  return record;
}

function staticClosure(keys) {
  const visited = new Set();
  function visit(key) {
    if (visited.has(key)) return;
    visited.add(key);
    for (const dependency of required(key).imports ?? []) visit(dependency);
  }
  for (const key of keys) visit(key);
  return new Set([...visited].map((key) => required(key).file));
}

function sizes(files) {
  let raw = 0;
  let gzip = 0;
  for (const file of files) {
    const contents = readFileSync(join(dist, file));
    raw += contents.length;
    gzip += gzipSync(contents).length;
  }
  return { raw, gzip };
}

try {
  const entry = required(entryKey);
  required(projectKey);
  if (!entry.isEntry || !entry.dynamicImports?.includes(projectKey)) {
    throw new Error("The /projects route is not a dynamic import from the entry manifest");
  }
  const initial = staticClosure([entryKey, projectKey]);
  for (const route of lightweightRoutes) {
    if (!entry.dynamicImports?.includes(resolveKey(route))) throw new Error(`Route is not lazy-loaded: ${route}`);
    if (initial.has(required(route).file)) throw new Error(`Route is in /projects initial graph: ${route}`);
    const closure = staticClosure([entryKey, route]);
    for (const file of closure) {
      if (heavyByChunk[file]?.length) throw new Error(`Heavy dependency in ${route}: ${file}`);
    }
    if (sizes(closure).raw >= limit) throw new Error(`Route initial JS exceeds budget: ${route}`);
    const routeSize = sizes(closure);
    console.log(`${route}: lazy route, no TipTap/XYFlow, ${(routeSize.raw / 1000).toFixed(2)} kB initial JS / ${(routeSize.gzip / 1000).toFixed(2)} kB gzip`);
  }
  for (const route of excludedRoutes) {
    if (initial.has(required(route).file)) throw new Error(`Unrelated route is in /projects initial graph: ${route}`);
  }
  const production = required("src/product/PersistentProductionPage.tsx");
  const graphicModelFile = required(graphicModelKey).file;
  const videoModelFile = required(videoModelKey).file;
  const commonProduction = staticClosure([entryKey, "src/product/PersistentProductionPage.tsx"]);
  if (commonProduction.has(graphicModelFile)) throw new Error("Graphic editor model leaked into common Production static graph");
  if (commonProduction.has(videoModelFile)) throw new Error("Video editor model leaked into common Production static graph");
  if (!production.dynamicImports?.includes(graphicModelKey)) throw new Error("Graphic editor model is not lazy-loaded from Production");
  if (!production.dynamicImports?.includes(videoModelKey)) throw new Error("Video editor model is not lazy-loaded from Production");
  if (!production.dynamicImports?.includes(textStudioKey)) throw new Error("Text Studio is not a Production dynamic import");
  const textClosure = staticClosure([entryKey, textStudioKey]);
  if (![...textClosure].some((file) => heavyByChunk[file]?.includes("TipTap"))) throw new Error("Text Studio TipTap module mapping missing");
  if (textClosure.has(graphicModelFile)) throw new Error("Graphic editor model leaked into Text Studio static graph");
  if (textClosure.has(videoModelFile)) throw new Error("Video editor model leaked into Text Studio static graph");
  for (const sibling of siblingStudioKeys) {
    if (!production.dynamicImports?.includes(sibling)) throw new Error(`Studio shell is not dynamic: ${sibling}`);
    const closure = staticClosure([entryKey, sibling]);
    if ([...closure].some((file) => heavyByChunk[file]?.includes("TipTap"))) throw new Error(`TipTap leaked into ${sibling}`);
    if (sibling !== "src/product/GraphicStudioShell.tsx" && closure.has(graphicModelFile)) throw new Error(`Graphic editor model leaked into ${sibling}`);
    if (sibling !== "src/product/VideoStudioShell.tsx" && closure.has(videoModelFile)) throw new Error(`Video editor model leaked into ${sibling}`);
  }
  console.log(`Text Studio: lazy TipTap closure ${(sizes(textClosure).raw / 1000).toFixed(2)} kB raw / ${(sizes(textClosure).gzip / 1000).toFixed(2)} kB gzip; Graphic/Video exclude TipTap`);
  for (const file of initial) {
    if (heavyByChunk[file]?.length) throw new Error(`Heavy dependency in /projects initial graph: ${file} (${heavyByChunk[file].join(", ")})`);
  }
  const observedHeavy = new Set(Object.values(heavyByChunk).flat());
  for (const name of ["TipTap", "XYFlow"]) {
    if (!observedHeavy.has(name)) throw new Error(`Missing ${name} module mapping in emitted chunks`);
  }
  const initialSize = sizes(initial);
  const allJs = new Set(Object.values(manifest).map((record) => record.file).filter((file) => file?.endsWith(".js")));
  const totalSize = sizes(allJs);
  const format = (bytes) => `${(bytes / 1000).toFixed(2)} kB`;

  console.log(`/projects initial JS: ${format(initialSize.raw)} raw, ${format(initialSize.gzip)} gzip across ${initial.size} chunks`);
  console.log(`FE-F4 baseline single JS: ${format(baseline)} raw; reduction ${((1 - initialSize.raw / baseline) * 100).toFixed(1)}%`);
  console.log(`All emitted JS: ${format(totalSize.raw)} raw, ${format(totalSize.gzip)} gzip (not an initial-load gate)`);
  console.log("Project detail, production, TipTap Workspace, and XYFlow Workflows chunks are outside /projects initial graph");
  if (initialSize.raw >= limit) throw new Error(`/projects initial JS is at or above ${format(limit)} raw`);
} catch (error) {
  console.error(`Bundle budget failed: ${error.message}`);
  process.exitCode = 1;
}
