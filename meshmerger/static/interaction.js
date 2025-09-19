import { updatePlot } from "./plot.js";

export class Interaction {
  constructor(plotDiv, meshManager) {
    this.plotDiv = plotDiv;
    this.meshManager = meshManager;
    this.nodeTraceByMesh = { 0: {}, 1: {} };
  }

  bind() {
    this.plotDiv.on("plotly_selected", (e) => this.onSelected(e));
    this.plotDiv.on("plotly_click", (e) => this.onClick(e));
  }

  onSelected(eventData) {
    if (!eventData || !eventData.points) return;

    const selectedNodesByMesh = { 0: [], 1: [] };

    eventData.points.forEach((pt) => {
      let meshIdx = null;
      let code = null;

      for (let mIdx in this.nodeTraceByMesh) {
        for (let c in this.nodeTraceByMesh[mIdx]) {
          if (this.nodeTraceByMesh[mIdx][c] === pt.curveNumber) {
            meshIdx = parseInt(mIdx);
            code = parseInt(c);
            break;
          }
        }
        if (meshIdx !== null) break;
      }

      if (meshIdx === null) return;
      const mesh =
        meshIdx === 0 ? this.meshManager.mesh1 : this.meshManager.mesh2;
      if (!mesh) return;

      let nodeIndex = -1,
        count = 0;
      for (let i = 0; i < mesh.codes.length; i++) {
        if (mesh.codes[i] === code) {
          if (count === pt.pointIndex) {
            nodeIndex = i;
            break;
          }
          count++;
        }
      }
      if (nodeIndex !== -1) selectedNodesByMesh[meshIdx].push(nodeIndex);
    });

    if (
      selectedNodesByMesh[0].length === 0 &&
      selectedNodesByMesh[1].length === 0
    )
      return;

    let val = prompt("Enter new code for selected nodes (integer):", "1");
    if (val === null) return;
    const newCode = parseInt(val, 10);
    if (isNaN(newCode)) return;

    this.meshManager.updateCodes(selectedNodesByMesh, newCode);
  }

  onClick(eventData) {
    const selected = this.meshManager.findNodesFromEvent(
      eventData,
      this.nodeTraceByMesh
    );
    const first = Object.values(selected).flat()[0];
    if (first === undefined) return;
    let val = prompt("Enter new code for selected node (integer):");
    if (!val) return;
    this.meshManager.updateCodes(selected, parseInt(val, 10));
  }
}
