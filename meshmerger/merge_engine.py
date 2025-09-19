import numpy as np
import mikeio
import triangle
import matplotlib.pyplot as plt
from collections import defaultdict


def triangulate(nodes, segments):
    A = dict(vertices=nodes, segments=np.array(segments))
    B = triangle.triangulate(A, "p")
    conn_nodes = np.c_[B["vertices"], np.zeros(len(B["vertices"])), np.zeros(len(B["vertices"]), dtype=int)]
    conn_elems = B["triangles"]
    return conn_nodes, conn_elems


def build_nodes_and_segments(line1, line2, num_parallel=1):
    def resample_line(line, num_points):
        t = np.linspace(0, 1, len(line))
        t_new = np.linspace(0, 1, num_points)
        x_new = np.interp(t_new, t, line[:, 0])
        y_new = np.interp(t_new, t, line[:, 1])
        return np.vstack([x_new, y_new]).T

    def line_intersection(p1, p2, q1, q2, tol=1e-10):
        """
        Find the intersection point of two line segments.
        Returns the intersection point or None if lines are parallel.
        """
        p1 = np.array(p1, dtype=np.float64)
        p2 = np.array(p2, dtype=np.float64)
        q1 = np.array(q1, dtype=np.float64)
        q2 = np.array(q2, dtype=np.float64)
        
        # Direction vectors
        r = p2 - p1
        s = q2 - q1
        
        # For 2D cross product, we need to convert to 3D or use the 2D formula
        # Cross product for 2D vectors: cross(a, b) = a.x * b.y - a.y * b.x
        r_cross_s = r[0] * s[1] - r[1] * s[0]
        q_minus_p = q1 - p1
        
        # Check if lines are parallel
        if abs(r_cross_s) < tol:
            # Lines are parallel or coincident
            return (p1 + p2) / 2.0  # Return midpoint as fallback
        
        # Calculate parameters using 2D cross product formula
        t = (q_minus_p[0] * s[1] - q_minus_p[1] * s[0]) / r_cross_s
        u = (q_minus_p[0] * r[1] - q_minus_p[1] * r[0]) / r_cross_s
        
        # Check if intersection is within both line segments
        if 0 <= t <= 1 and 0 <= u <= 1:
            intersection = p1 + t * r
            return intersection
        else:
            # Lines intersect but not within segments, return the intersection anyway
            intersection = p1 + t * r
            return intersection

    def line_intersection_old(p1, p2, q1, q2):
        A = np.array([[p2[0] - p1[0], q1[0] - q2[0]], [p2[1] - p1[1], q1[1] - q2[1]]])
        b = np.array([q1[0] - p1[0], q1[1] - p1[1]])
        try:
            t, _ = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            return (p1 + p2) / 2.0
        return p1 + t * (p2 - p1)

    def create_parallel_lines(line1, line2, num_parallel=3):
        s1 = np.linalg.norm(np.diff(line1, axis=0), axis=1).mean()
        s2 = np.linalg.norm(np.diff(line2, axis=0), axis=1).mean()
        n_points = max(len(line1), len(line2))
        line1_rs = resample_line(line1, n_points)
        line2_rs = resample_line(line2, n_points)
        d = np.linspace(s1, s2, num_parallel + 2)
        total = s1 + s2
        parallel_lines = []
        for i in range(1, num_parallel + 1):
            t = np.sum(d[i]) / total
            interp_line = (1 - t) * line1_rs + t * line2_rs
            n_target = max(2, round(len(line1) + (i / (num_parallel + 1)) * (len(line2) - len(line1))))
            interp_line_rs = resample_line(interp_line, n_target)
            parallel_lines.append(interp_line_rs)
        return parallel_lines

    tol = 1e-8
    nodes = []
    segments = []

    def add_point(p):
        p = np.asarray(p, dtype=float)
        for i, q in enumerate(nodes):
            if abs(q[0] - p[0]) < tol and abs(q[1] - p[1]) < tol:
                return i
        nodes.append(p.copy())
        return len(nodes) - 1

    def add_line(line):
        idxs = [add_point(p) for p in line]
        for i in range(len(idxs) - 1):
            segments.append((idxs[i], idxs[i + 1]))
        return idxs

    add_line(line1)
    add_line(line2)

    parallel_lines = create_parallel_lines(line1, line2, num_parallel)

    for pl in parallel_lines:
        for p in pl: 
            add_point(p)
        p_start = line_intersection(pl[0], pl[-1], line1[0], line2[0])
        p_end = line_intersection(pl[0], pl[-1], line1[-1], line2[-1])

        idx_l1s = add_point(line1[0])
        idx_ps = add_point(p_start)
        idx_l2s = add_point(line2[0])
        segments.extend([(idx_l1s, idx_ps), (idx_ps, idx_l2s)])

        idx_l1e = add_point(line1[-1])
        idx_pe = add_point(p_end)
        idx_l2e = add_point(line2[-1])
        segments.extend([(idx_l1e, idx_pe), (idx_pe, idx_l2e)])

    return np.asarray(nodes), segments


def extract_boundary_edges(mesh):
    edges_dict = defaultdict(list)
    for elem in mesh["elems"]:
        n = len(elem)
        for i in range(n):
            a, b = elem[i], elem[(i + 1) % n]
            code_a, code_b = mesh["codes"][a], mesh["codes"][b]
            if code_a <= 1 or code_b <= 1:
                continue
            edges_dict[int(code_b)].append([int(a), int(b)])
    return edges_dict


def order_edges_strict(edges):
    adj = defaultdict(list)
    used = set()
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)

    first_nodes = {a for a, _ in edges}
    second_nodes = {b for _, b in edges}
    start = (first_nodes - second_nodes).pop() if first_nodes - second_nodes else edges[0][0]

    ordered, current = [start], start
    while True:
        neighbors = adj[current]
        next_nodes = [n for n in neighbors if (current, n) not in used and (n, current) not in used]
        if not next_nodes:
            break
        nxt = next_nodes[0]
        used.update({(current, nxt), (nxt, current)})
        ordered.append(nxt)
        current = nxt
    return ordered


def normalize_line(line):
    dists = np.linalg.norm(line[:, None] - line[None, :], axis=-1)
    i, j = np.unravel_index(np.argmax(dists), dists.shape)
    start, end = line[i], line[j]
    direction = end - start
    proj = (line - start) @ direction
    return line[np.argsort(proj)]


def order_lines_for_polygon(b1, b2):
    b1, b2 = normalize_line(b1), normalize_line(b2)
    dists = [
        np.linalg.norm(b1[-1] - b2[0]),
        np.linalg.norm(b1[-1] - b2[-1]),
        np.linalg.norm(b1[0] - b2[0]),
        np.linalg.norm(b1[0] - b2[-1]),
    ]
    dmin = np.argmin(dists)
    if dmin == 0:
        poly = np.vstack([b1, b2])
    elif dmin == 1:
        poly = np.vstack([b1, b2[::-1]])
    elif dmin == 2:
        poly = np.vstack([b1[::-1], b2])
    else:
        poly = np.vstack([b1[::-1], b2[::-1]])
    return np.vstack([poly, poly[0]])


def extract_boundary_nodes(mesh, code):
    return np.where(mesh.codes == code)[0].tolist()


def plot_polygon(poly_points, segments):
    plt.figure(figsize=(6, 6))
    for s in segments:
        x = [poly_points[s[0], 0], poly_points[s[1], 0]]
        y = [poly_points[s[0], 1], poly_points[s[1], 1]]
        plt.plot(x, y, "k-")
    plt.scatter(poly_points[:, 0], poly_points[:, 1], c="r")
    for i, (x, y) in enumerate(poly_points):
        plt.text(x, y, str(i), fontsize=8, color="blue")
    plt.axis("equal")
    plt.title("Polygon boundary with segments")
    plt.show()


def plot_triangulation(vertices, triangles):
    plt.figure(figsize=(6, 6))
    for tri in triangles:
        pts = np.vstack([vertices[tri], vertices[tri[0]]])
        plt.plot(pts[:, 0], pts[:, 1], "g-")
    plt.scatter(vertices[:, 0], vertices[:, 1], c="r")
    plt.axis("equal")
    plt.title("Generated triangulation")
    plt.show()


def triangulate_between(mesh1, mesh2, b1_ids, b2_ids, debug=False):
    b1_coords = np.array(mesh1["nodes"])[b1_ids, :2]
    b2_coords = np.array(mesh2["nodes"])[b2_ids[::-1], :2]
    nodes, segments = build_nodes_and_segments(b1_coords, b2_coords, num_parallel=1)
    return triangulate(nodes, segments)


def write_mesh(out_mesh, nodes, elements, codes, projection="UTM-48"):
    with open(out_mesh, "w") as f:
        f.write(f"{100079}  {1000}  {len(nodes)}  {projection}\n")
        for nid, (x, y, z, code) in enumerate(nodes, start=1):
            f.write(f"{nid:10d} {x:16.10f} {y:16.10f} {z:16.10f} {codes[nid-1]:6d}\n")
        f.write(f"{len(elements):10d}{4:12d}{25:11d}\n")
        for eid, conn in enumerate(elements, start=1):
            conn_fmt = "".join(f"{nid+1:12d}" for nid in conn)
            f.write(f"{eid:12d}{conn_fmt}\n")

def update_boundary_codes(nodes, elems):
    from collections import defaultdict
    edge_count = defaultdict(int)
    for tri in elems:
        n = len(tri)
        for i in range(n):
            a, b = tri[i], tri[(i + 1) % n]
            edge = tuple(sorted((a, b)))
            edge_count[edge] += 1

    codes = [0] * len(nodes)
    for (a, b), cnt in edge_count.items():
        if cnt == 1:
            codes[a] = 1
            codes[b] = 1
    return codes


def merge(mesh1, mesh2, debug=False):
    out_file = r"c:\\temp\\merged.mesh"
    
    all_conn_nodes = []
    all_conn_elems = []
    codes1 = sorted(set(mesh1["codes"]))
    codes2 = sorted(set(mesh2["codes"]))

    uniq1 = [c for c in codes1 if c > 1]
    uniq2 = [c for c in codes2 if c > 1]

    if len(uniq1) != len(uniq2):
        raise ValueError(f"Meshes have different number of boundary codes: {len(uniq1)} vs {len(uniq2)}")

    codes_list_to_merge = list(zip(uniq1, uniq2))

    for codes in codes_list_to_merge:
        b1_ids = order_edges_strict(extract_boundary_edges(mesh1)[codes[0]])
        b2_ids = order_edges_strict(extract_boundary_edges(mesh2)[codes[1]])
        conn_nodes, conn_elems = triangulate_between(mesh1, mesh2, b1_ids, b2_ids, debug=debug)
        all_conn_nodes.append(conn_nodes)
        all_conn_elems.append(conn_elems)

    merged_nodes, codes_list, node_index = [], [], {}

    def key_from_coord(coord, tol=1e-8):
        return tuple((coord[:2] / tol).round().astype(int))

    def add_node(coord, code):
        k = key_from_coord(coord)
        if k in node_index:
            return node_index[k]
        idx = len(merged_nodes)
        merged_nodes.append((float(coord[0]), float(coord[1])))  # normalize to 2D
        codes_list.append(code)
        node_index[k] = idx
        return idx

    elems = []

    nodes1 = np.array(mesh1["nodes"])
    codes1 = mesh1["codes"]
    nodes2 = np.array(mesh2["nodes"])
    codes2 = mesh2["codes"]

    for coord, code in zip(nodes1, codes1):
        add_node(coord, code)
    for coord, code in zip(nodes2, codes2):
        add_node(coord, code)

    for elem in mesh1["elems"]:
        elems.append([add_node(nodes1[i], codes1[i]) for i in elem])
    for elem in mesh2["elems"]:
        elems.append([add_node(nodes2[i], codes2[i]) for i in elem])

    for conn_nodes, conn_elems in zip(all_conn_nodes, all_conn_elems):
        conn_map = [add_node(coord, 1) for coord in conn_nodes[:, :2]]  # only keep x,y
        for tri in conn_elems:
            elems.append([conn_map[i] for i in tri])

    nodes = [(x, y, 0.0, code) for (x, y), code in zip(merged_nodes, codes_list)]

    codes = update_boundary_codes(nodes, elems)
    write_mesh(out_file, nodes, elems, codes)
    return {"nodes": merged_nodes, "elems": elems, "codes": codes}


if __name__ == "__main__":
    mesh1_file = r"C:\Projects\Merge Gridded Mesh\20250606\cropsWesternSG3\D2-L-merged_V2.mesh"
    mesh2_file = r"C:\Projects\Merge Gridded Mesh\20250606\cropsWesternSG3\BanI-20250606_cropsWesternSG3 - Conv.mesh"
    codes_list = [[2, 2], [3, 3], [4,4], [5,5], [6,6], [7,7]]
    out_file = r"C:\Projects\Merge Gridded Mesh\20250606\cropsWesternSG3\D2-L-I-merged.mesh"
    merge(mesh1_file, mesh2_file, codes_list, out_file, debug=False)
