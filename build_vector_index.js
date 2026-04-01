import fs from "fs";

const embeddings = JSON.parse(
fs.readFileSync("./embeddings.json","utf8")
);

const index = embeddings.map(e => ({
id: e.id,
vector: Float32Array.from(e.vector)
}));

fs.writeFileSync(
"./vector_index.json",
JSON.stringify(index)
);

console.log("Vector index created.");
