import fs from "fs";
import path from "path";

/* =========================
PATHS
========================= */
const BLOG_PATH = "./posts_clean.json";
const LEGAL_PATH = "./src/knowledge/legal";
const OUTPUT_PATH = "./data/master_content.json";

/* =========================
UTILS
========================= */
function cleanText(text = "") {
  return text
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/* =========================
LOAD BLOG DATA
========================= */
const blogRaw = JSON.parse(fs.readFileSync(BLOG_PATH, "utf8"));

const blog = blogRaw.map(p => ({
  id: "blog_" + p.id,
  type: "blog",
  title: p.title || "Untitled",
  content: cleanText(p.content || "")
}));

/* =========================
LOAD LEGAL DATA (RECURSIVE)
========================= */
let legal = [];

function loadLegalFiles(dir) {
  const files = fs.readdirSync(dir);

  for (const file of files) {
    const fullPath = path.join(dir, file);

    try {
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        loadLegalFiles(fullPath);
      } else if (file.endsWith(".json")) {
        const raw = JSON.parse(fs.readFileSync(fullPath, "utf8"));

        const text =
          raw?.metadata?.text ||
          raw?.content ||
          JSON.stringify(raw);

        legal.push({
          id: "law_" + legal.length,
          type: "legal",
          title: file.replace(".json", ""),
          content: cleanText(text)
        });
      }

    } catch (err) {
      console.warn("Skipped:", file, err.message);
    }
  }
}

// Execute loader
loadLegalFiles(LEGAL_PATH);

/* =========================
MERGE DATA
========================= */
const master = [...blog, ...legal];

/* =========================
VALIDATION
========================= */
if (master.length === 0) {
  console.error("ERROR: No data loaded");
  process.exit(1);
}

/* =========================
SAVE FILE
========================= */
fs.writeFileSync(
  OUTPUT_PATH,
  JSON.stringify(master, null, 2)
);

console.log("DONE");
console.log("Blog:", blog.length);
console.log("Legal:", legal.length);
console.log("Total:", master.length);
