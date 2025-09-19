import { loadMesh, mergeMeshes } from "./mesh.js";
import {
  buildElementTrace,
  buildNodeTraces,
  initPlot,
  updatePlot,
} from "./plot.js";
import { Interaction } from "./interaction.js";
import { setupUI } from "./ui.js";

class MeshManager {
  constructor() {
    this.mesh1 = null;
    this.mesh2 = null;
    this.merged = null;
    this.plotDiv = document.getElementById("mesh-view");
    this.interaction = new Interaction(this.plotDiv, this);
  }

  async uploadMeshes() {
    try {
      const f1 = document.getElementById("mesh1").files[0];
      const f2 = document.getElementById("mesh2").files[0];
      this.mesh1 = f1 ? await loadMesh(f1) : null;
      this.mesh2 = f2 ? await loadMesh(f2) : null;
      this.redraw();
    } catch (err) {
      alert("Error loading meshes: " + err);
    }
  }

  async merge() {
    if (!this.mesh1 || !this.mesh2) {
      alert("Load two meshes to merge!");
      return;
    }
    try {
      this.merged = await mergeMeshes(this.mesh1, this.mesh2);
      this.mesh1 = this.merged;
      this.mesh2 = null;
      this.redraw();
    } catch (err) {
      alert("Merge error: " + err);
    }
  }

  redraw() {
    const traces = [];
    const map = { 0: {}, 1: {} };
    const lineWidth =
      parseFloat(document.getElementById("lineWidthSlider").value) || 0.5;

    [this.mesh1, this.mesh2].forEach((m, idx) => {
      if (!m) return;

      traces.push(buildElementTrace(m, idx, lineWidth));

      const { traces: nodeTraces, indexMap } = buildNodeTraces(m, idx);
      const baseIndex = traces.length;
      nodeTraces.forEach((t) => traces.push(t));

      Object.keys(indexMap).forEach((code) => {
        map[idx][code] = baseIndex + indexMap[code];
      });
    });

    if (!this.plotDiv._initialized) {
      initPlot(this.plotDiv, traces);
      this.plotDiv._initialized = true;
      this.interaction.nodeTraceByMesh = map;
      this.interaction.bind();
    } else {
      updatePlot(this.plotDiv, traces);
      this.interaction.nodeTraceByMesh = map;
    }
  }

  findNodesFromEvent(eventData, traceMap) {
    const result = { 0: [], 1: [] };
    if (!eventData || !eventData.points) return result;
    eventData.points.forEach((pt) => {
      for (let mIdx in traceMap) {
        for (let code in traceMap[mIdx]) {
          if (traceMap[mIdx][code] === pt.curveNumber) {
            const mesh = mIdx == 0 ? this.mesh1 : this.mesh2;
            if (!mesh) return;
            let nodeIndex = -1,
              count = 0;
            for (let i = 0; i < mesh.codes.length; i++) {
              if (mesh.codes[i] == code) {
                if (count === pt.pointIndex) {
                  nodeIndex = i;
                  break;
                }
                count++;
              }
            }
            if (nodeIndex !== -1) result[mIdx].push(nodeIndex);
          }
        }
      }
    });
    return result;
  }

  updateCodes(selected, newCode) {
    for (let mIdx in selected) {
      const mesh = mIdx == 0 ? this.mesh1 : this.mesh2;
      selected[mIdx].forEach((i) => (mesh.codes[i] = newCode));
    }
    this.redraw();
  }
}

import { PolygonSelector } from "./polygon.js";
const manager = new MeshManager();
setupUI(manager, manager.interaction);

const polygonSelector = new PolygonSelector(
  manager.plotDiv,
  manager,
  "polySelectBtn"
);
polygonSelector.init();
