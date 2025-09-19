import { PALETTE, BASE_LAYOUT } from "./config.js";

export function codeToColor(c) {
  if (c < 0) return "black";
  return PALETTE[c % PALETTE.length];
}

export function buildElementTrace(mesh, meshIdx, lineWidth) {
  let elemXs = [], elemYs = [];
  mesh.elems.forEach(e => {
    for (let i = 0; i < e.length; i++) {
      const ni = e[i], nj = e[(i + 1) % e.length];
      elemXs.push(mesh.nodes[ni][0], mesh.nodes[nj][0], null);
      elemYs.push(mesh.nodes[ni][1], mesh.nodes[nj][1], null);
    }
  });
  return {
    type: "scattergl",
    mode: "lines",
    x: elemXs,
    y: elemYs,
    line: { color: meshIdx === 0 ? "gray" : "lightblue", width: lineWidth },
    name: `Mesh ${meshIdx + 1} elements`
  };
}

export function buildNodeTraces(mesh, meshIdx) {
  const traces = {};
  const out = [];
  const uniqueCodes = Array.from(new Set(mesh.codes)).filter(c => c !== 0);
  uniqueCodes.forEach(code => {
    const indices = mesh.codes.map((c,i) => c===code ? i : -1).filter(i => i!==-1);
    const xs = indices.map(i => mesh.nodes[i][0]);
    const ys = indices.map(i => mesh.nodes[i][1]);
    out.push({
      type: "scattergl",
      mode: "markers",
      x: xs,
      y: ys,
      marker: { color: codeToColor(code), size: code === 1 ? 4 : 6 },
      text: indices.map(i => `node ${i} code ${mesh.codes[i]}`),
      hoverinfo: "text",
      name: `Mesh ${meshIdx + 1} - Code ${code}`,
      showlegend: true
    });
    traces[code] = out.length - 1;
  });
  return { traces: out, indexMap: traces };
}

export function initPlot(plotDiv, traces) {
  Plotly.newPlot(plotDiv, traces, BASE_LAYOUT, { scrollZoom: true, responsive: true });
}

export function updatePlot(plotDiv, traces) {
  Plotly.react(plotDiv, traces, BASE_LAYOUT);
}
