export class PolygonSelector {
  constructor(plotDiv, meshManager, buttonId) {
    this.plotDiv = plotDiv;
    this.meshManager = meshManager;
    this.btn = document.getElementById(buttonId);

    this.polygonMode = false;
    this.polygonPts = [];
    this.drawTraceIndex = null;
  }

  init() {
    this.btn.addEventListener("click", () => this.toggleMode());

    this.plotDiv.addEventListener("mousedown", (e) => this.onMouseDown(e));
    this.plotDiv.addEventListener("dblclick", (e) => this.onFinish(e));
    this.plotDiv.addEventListener("contextmenu", (e) => this.onFinish(e));
  }

  toggleMode() {
    this.polygonMode = !this.polygonMode;
    this.btn.classList.toggle("active", this.polygonMode);
    this.resetPolygon();
    this.plotDiv.style.cursor = this.polygonMode ? "crosshair" : "";
  }

  resetPolygon() {
    this.polygonPts = [];
    if (this.drawTraceIndex !== null) {
      Plotly.deleteTraces(this.plotDiv, this.drawTraceIndex);
      this.drawTraceIndex = null;
    }
  }

  clientToData(evt) {
    const rect = this.plotDiv.getBoundingClientRect();
    const full = this.plotDiv._fullLayout;
    const margin = full.margin || { l: 0, r: 0, t: 0, b: 0 };
    const xRange = full.xaxis.range || [0, 1];
    const yRange = full.yaxis.range || [0, 1];
    const plotWidth = full.width - margin.l - margin.r;
    const plotHeight = full.height - margin.t - margin.b;
    const offsetX = evt.clientX - rect.left - margin.l;
    const offsetY = evt.clientY - rect.top - margin.t;
    const rx = offsetX / plotWidth;
    const ry = offsetY / plotHeight;
    const x = xRange[0] + rx * (xRange[1] - xRange[0]);
    const y = yRange[1] - ry * (yRange[1] - yRange[0]);
    return [x, y];
  }

  drawPolygonPreview() {
    if (this.polygonPts.length === 0) return;
    const xs = this.polygonPts.map((p) => p[0]).concat([this.polygonPts[0][0]]);
    const ys = this.polygonPts.map((p) => p[1]).concat([this.polygonPts[0][1]]);
    if (this.drawTraceIndex === null) {
      Plotly.addTraces(this.plotDiv, {
        type: "scatter",
        mode: "lines+markers",
        x: xs,
        y: ys,
        hoverinfo: "none",
        line: { width: 2, color: "black" },
        marker: { size: 6, symbol: "circle", color: "black" },
        name: "polygon-draw",
        showlegend: false,
      }).then(() => {
        this.drawTraceIndex = this.plotDiv.data.length - 1;
      });
    } else {
      Plotly.restyle(this.plotDiv, { x: [xs], y: [ys] }, [this.drawTraceIndex]);
    }
  }

  pointInPoly(x, y, poly) {
    let inside = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const xi = poly[i][0],
        yi = poly[i][1];
      const xj = poly[j][0],
        yj = poly[j][1];
      const intersect =
        yi > y !== yj > y &&
        x < ((xj - xi) * (y - yi)) / (yj - yi || 1e-12) + xi;
      if (intersect) inside = !inside;
    }
    return inside;
  }

  onMouseDown(evt) {
    if (!this.polygonMode) return;
    if (evt.button === 2) {
      // right click
      evt.preventDefault();
      this.finishSelection();
      return;
    }
    if (evt.button !== 0) return; // only left click
    const pt = this.clientToData(evt);
    this.polygonPts.push(pt);
    this.drawPolygonPreview();
  }

  onFinish(evt) {
    if (!this.polygonMode) return;
    evt.preventDefault();
    this.finishSelection();
  }

  finishSelection() {
    if (!this.polygonMode || this.polygonPts.length < 3) {
      this.resetPolygon();
      this.toggleMode();
      return;
    }

    const selectedByMesh = { 0: [], 1: [] };

    [this.meshManager.mesh1, this.meshManager.mesh2].forEach((m, mi) => {
      if (!m) return;
      for (let i = 0; i < m.nodes.length; i++) {
        if (m.codes[i] === 0) continue;
        const p = m.nodes[i];
        if (this.pointInPoly(p[0], p[1], this.polygonPts)) {
          selectedByMesh[mi].push(i);
        }
      }
    });

    this.resetPolygon();
    if (selectedByMesh[0].length === 0 && selectedByMesh[1].length === 0)
      return;

    let val = prompt("Enter new code for selected nodes (integer):", "1");
    if (val === null) return;
    const newCode = parseInt(val, 10);
    if (isNaN(newCode)) return;

    this.meshManager.updateCodes(selectedByMesh, newCode);
  }
}
