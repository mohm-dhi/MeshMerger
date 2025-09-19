import { postFile, postJSON } from "./api.js";

export function normalizeMesh(m) {
  if (!m) return null;
  m.nodes = m.nodes.map(n => [parseFloat(n[0]), parseFloat(n[1])]);
  m.elems = m.elems.map(e => e.map(x => parseInt(x)));
  m.codes = m.codes.map(c => parseInt(c));
  return m;
}

export async function loadMesh(file) {
  return normalizeMesh(await postFile("/load_mesh", file));
}

export async function mergeMeshes(mesh1, mesh2) {
  return normalizeMesh(await postJSON("/merge", { mesh1, mesh2 }));
}
