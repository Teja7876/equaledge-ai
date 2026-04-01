import legalRaw from "../data/data_storage/raw/domains/legal/RPWD_2016_FULL_ACT_STRUCTURED.json";
const legalDocs = legalRaw.definitions.sections;


export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/ask") {
      const { question } = await request.json();
      const words = (question || "").toLowerCase().split(" ");

      const matches = legalDocs
        .map(sec => {
          const text = (sec.section_heading + " " + sec.section_text).toLowerCase();
          let score = 0;
          for (const w of words) {
            if (text.includes(w)) score++;
          }
          return { sec, score };
        })
        .filter(r => r.score > 0)
        .sort((a, b) => b.score - a.score)
        .slice(0, 5);

      let context = "";
      for (const m of matches) {
        context += `Section ${m.sec.section_number}: ${m.sec.section_heading}\n${m.sec.section_text.slice(0,500)}\n\n`;
      }

      const prompt = `
Answer strictly using the RPwD Act context below.
Always mention section numbers.

Question: ${question}

Context:
${context}`;

      const aiRes = await env.AI.run("@cf/meta/llama-3-8b-instruct", { prompt });

      return new Response(JSON.stringify({
        answer: aiRes.response,
        sections_used: matches.map(m => m.sec.section_number)
      }), { headers: { "Content-Type": "application/json" } });
    }

    return new Response(JSON.stringify({ status: "AI running" }), {
      headers: { "Content-Type": "application/json" }
    });
  }
};
