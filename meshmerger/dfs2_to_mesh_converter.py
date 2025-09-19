import numpy as np
import mikeio
from collections import defaultdict


def center2corner_1D(vector):
    midpoints = (vector[:-1] + vector[1:]) / 2
    beginning = 2 * vector[0] - midpoints[0]
    end = 2 * vector[-1] - midpoints[-1]
    return np.concatenate(([beginning], midpoints, [end]))

def dfs2_to_fm_mesh(dfs2_file, out_mesh, projection=None, land_value=10):
    ds = mikeio.open(dfs2_file)
    data = ds.read()
    bathy = data[0].to_numpy().squeeze()
    bathy[bathy>land_value] = land_value
    geom = getattr(data, "geometry", getattr(ds, "geometry", None))

    try:
        x0, y0 = geom.origin
        dx, dy = geom.dx, geom.dy
        nx, ny = int(geom.nx), int(geom.ny)
        alpha_deg = geom.orientation
    except Exception:
        x0, y0 = geom.x0, geom.y0
        dx, dy = geom.dx, geom.dy
        nx, ny = int(geom.nx), int(geom.ny)
        alpha_deg = getattr(geom, "orientation", 0.0)

    xs = center2corner_1D(x0 + np.arange(nx) * dx)
    ys = center2corner_1D(y0 + np.arange(ny) * dy)
    X, Y = np.meshgrid(xs, ys)

    theta = np.radians(alpha_deg)
    cth = np.cos(theta)
    sth = np.sin(theta)
    Xr = (X - x0) * cth + (Y - y0) * sth + x0
    Yr = -(X - x0) * sth + (Y - y0) * cth + y0

    node_ids = np.arange((nx + 1) * (ny + 1)).reshape(ny + 1, nx + 1) + 1

    node_pos = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            nid = int(node_ids[j, i])
            node_pos[nid] = (i, j)

    if projection is None:
        try:
            projection = str(geom.projection).strip()
        except Exception:
            projection = "LONG/LAT"

    elements = []
    eid = 1
    for j in range(ny):
        for i in range(nx):
            v = bathy[j, i]
            if not np.isnan(v) and v != land_value:
                n1 = int(node_ids[j, i])
                n2 = int(node_ids[j, i + 1])
                n3 = int(node_ids[j + 1, i + 1])
                n4 = int(node_ids[j + 1, i])
                elements.append((eid, (n1, n2, n3, n4), (i, j)))
                eid += 1

    edge_count = defaultdict(list)
    for eid, (n1, n2, n3, n4), (ci, cj) in elements:
        for e in ((n1, n2), (n2, n3), (n3, n4), (n4, n1)):
            key = (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
            edge_count[key].append((eid, ci, cj))

    node_code = defaultdict(lambda: 0)
    outer_boundary_nodes = set()
    boundary_graph = defaultdict(list)

    for edge, cells in edge_count.items():
        if len(cells) == 1:
            n1, n2 = edge
            p1 = node_pos[n1]
            p2 = node_pos[n2]
            on_frame1 = (p1[0] == 0 or p1[0] == nx or p1[1] == 0 or p1[1] == ny)
            on_frame2 = (p2[0] == 0 or p2[0] == nx or p2[1] == 0 or p2[1] == ny)
            if on_frame1:
                outer_boundary_nodes.add(n1)
            if on_frame2:
                outer_boundary_nodes.add(n2)
            if on_frame1 and on_frame2:
                boundary_graph[n1].append(n2)
                boundary_graph[n2].append(n1)
            if not on_frame1:
                node_code[n1] = 1
            if not on_frame2:
                node_code[n2] = 1

    for n in outer_boundary_nodes:
        _ = boundary_graph[n]

    # inner boundary codes are already done above
    bcode = 2

    # define the four edges clockwise
    edges = [
        [(i, 0) for i in range(nx+1)],            # bottom edge (left→right)
        [(nx, j) for j in range(1, ny+1)],        # right edge (bottom→top)
        [(i, ny) for i in range(nx-1, -1, -1)],   # top edge (right→left)
        [(0, j) for j in range(ny-1, 0, -1)]      # left edge (top→bottom)
    ]

    for edge in edges:
        run_active = False
        for i, j in edge:
            nid = int(node_ids[j, i])
            if nid in outer_boundary_nodes:
                if not run_active:
                    run_active = True
                node_code[nid] = bcode
            else:
                if run_active:
                    bcode += 1
                    run_active = False
        if run_active:
            bcode += 1

    # collect all nodes that are used in elements
    used_nodes = set()
    for _, (n1, n2, n3, n4), _ in elements:
        used_nodes.update([n1, n2, n3, n4])

    # build mapping old_nid → new_nid
    nid_map = {}
    nodes = []
    new_id = 1
    for j in range(ny + 1):
        for i in range(nx + 1):
            nid = int(node_ids[j, i])
            if nid in used_nodes:
                x, y = float(Xr[j, i]), float(Yr[j, i])
                z = 0.0
                code = int(node_code[nid])
                nid_map[nid] = new_id
                nodes.append((new_id, x, y, z, code))
                new_id += 1

    with open(out_mesh, "w") as f:
        f.write(f"{100079}  {1000}  {len(nodes)}  {projection}\n")
        for n in nodes:
            f.write(f"{n[0]:10d} {n[1]:16.10f} {n[2]:16.10f} {n[3]:16.10f} {n[4]:6d}\n")
        f.write(f"{len(elements):10d}{4:12d}{25:11d}\n")
        for eid, (n1, n2, n3, n4), _ in elements:
            f.write(f"{eid:12d}{nid_map[n1]:12d}{nid_map[n2]:12d}{nid_map[n3]:12d}{nid_map[n4]:12d}\n")

    print("Conversion is Done!")

