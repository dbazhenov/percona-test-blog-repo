const blocks = [...document.querySelectorAll("code.language-mermaid")];
if (blocks.length === 0) {
  // No diagrams on this page.
} else {
  const { default: mermaid } = await import("https://cdn.jsdelivr.net/npm/mermaid@11.12.0/dist/mermaid.esm.min.mjs");
  mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });
  const nodes = [];
  for (const code of blocks) {
    const pre = code.closest("pre") || code;
    const graph = document.createElement("div");
    graph.className = "mermaid";
    graph.textContent = code.textContent;
    pre.replaceWith(graph);
    nodes.push(graph);
  }
  await mermaid.run({ nodes });
}
