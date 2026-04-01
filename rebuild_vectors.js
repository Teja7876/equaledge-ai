import fs from "fs";

const INPUT_FILE = "./posts_clean.json";
const OUTPUT_FILE = "./vector_index.json";
const API_URL = "https://equaledge-ai.equaledge1ai.workers.dev/embed";

const posts = JSON.parse(fs.readFileSync("./data/master_content.json", "utf8"));

function cleanText(text) {
  return text
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchWithTimeout(url, options, timeout = 10000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(id);
    return res;
  } catch (err) {
    clearTimeout(id);
    throw err;
  }
}

async function getEmbedding(text, retries = 3) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const res = await fetchWithTimeout(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();

      if (!data.vector || !Array.isArray(data.vector)) {
        throw new Error("Invalid vector format");
      }

      return data.vector;

    } catch (err) {
      console.warn(`Retry ${attempt}/${retries} failed:`, err.message);

      if (attempt === retries) {
        throw err;
      }

      await sleep(500 * attempt); // backoff
    }
  }
}

async function run() {
  const results = [];
  let success = 0;
  let failed = 0;

  for (const post of posts) {
    try {
      const text = cleanText(post.title + " " + post.content);

      if (!text) {
        console.warn("Skipped empty:", post.id);
        continue;
      }

      const vector = await getEmbedding(text);

      results.push({
        article_id: post.id,
        vector,
      });

      success++;
      console.log("OK:", post.id);

    } catch (err) {
      failed++;
      console.error("FAILED:", post.id, err.message);
    }
  }

  fs.writeFileSync(
    OUTPUT_FILE,
    JSON.stringify(results, null, 2)
  );

  console.log("\nDONE");
  console.log("Success:", success);
  console.log("Failed:", failed);
  console.log("Total:", posts.length);
}

run();
