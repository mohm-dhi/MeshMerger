export function setupUI(meshManager, interaction) {
  document.getElementById("loadBtn").addEventListener("click", () => meshManager.uploadMeshes());
  document.getElementById("mergeBtn").addEventListener("click", () => meshManager.merge());

  const slider = document.getElementById("lineWidthSlider");
  const label = document.getElementById("lineWidthLabel");
  slider.addEventListener("input", () => {
    label.textContent = parseFloat(slider.value).toFixed(1);
    meshManager.redraw();
  });
}
