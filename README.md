# Mesh Merge Tool

<p align="center">
  <img src="meshmerger/static/icon.png" alt="Mesh Merge Tool Logo" width="200"/>
</p>

<p align="center">
  <b>A Python-based utility for merging MIKE meshes with interactive boundary selection</b>
</p>

---

## 📸 Screenshots

<p align="center">
  <img src="meshmerger/static/screenshot0.png" alt="Mesh Merge Example" width="700"/>
</p>

<p align="center">
  <img src="meshmerger/static/screenshot1.png" alt="Main Interface" width="700"/>
</p>

<p align="center">
  <img src="meshmerger/static/screenshot2.png" alt="Mesh Merge Example" width="700"/>
</p>

---

## ⚙️ Installation

1. **Clone or download the repository**
   ```bash
   git clone https://github.com/mohm-dhi/MeshMerger.git
   cd MeshMerger
   ```

2. **Install required dependencies**  
   The tool requires Python 3.9+ and the following packages:
   ```bash
   pip install -r requirements.txt
   ```
   Or install manually:
   ```bash
   pip install numpy matplotlib flask triangle werkzeug mikeio
   ```
   finally install the package:
   ```bash
   pip install .
   ```
   or for editable version:
   ```bash
   pip install -e .
   ```

3. **Prepare your meshes**  
   Convert `.dfs2` files into mesh format using either:
   - The provided Python script:  
   - Or using **MIKE Toolbox**

---

## 🚀 Usage

1. **Start the software** and load the two mesh files you want to merge.  

2. **Define merge boundary** using:
   - **Lasso tool**, or
   - **Polygon selection tool**

   ⚠️ Important:
   - **MIKE mesh boundary codes must follow counterclockwise orientation**
   - See the [MIKE Manual](https://doc.mikepoweredbydhi.help/webhelp/2025/MeshEdit/index.htm) for boundary coding rules or define them accourding to instructions in the figure below: 
   <p align="center">
  <img src="meshmerger/static/BoundaryDefinition.png" alt="Mesh Merge Example" width="700"/>
</p>

3. **Click "Merge"**  
   - The meshes will be merged along your defined boundary.  

4. **Output**  
   - The merged mesh is stored in:
     ```
     C:\temp\
     ```

---

## 🧭 Example Workflow

1. Convert `.dfs2` → `.mesh`:
   ```bash
   python dfs2_to_mesh.py mesh1.dfs2 mesh1.mesh
   python dfs2_to_mesh.py mesh2.dfs2 mesh2.mesh
   ```

2. Launch the software and load both meshes.  

3. Define the boundary with **lasso/polygon**.  

4. Click **Merge**.  

5. Retrieve merged result from `C:\temp\`.  

---

## 📖 Notes

- Always ensure boundary selection follows **counterclockwise rotation**.  
- For large meshes, ensure your system has sufficient memory.  
- Check the **MIKE Mesh Manual** for detailed boundary rules.  

---

<p align="center">
  <i>Developed for seamless mesh merging in hydrodynamic modeling workflows.</i>
</p>
