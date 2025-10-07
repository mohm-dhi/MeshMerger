from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import mikeio
from .merge_engine import merge


def parse_mesh(file_path):
    msh = mikeio.Mesh(filename=file_path)
    nodes = msh.node_coordinates.tolist()
    elems = [list(map(int, e.tolist())) for e in msh.element_table]
    codes = list(map(int, msh.codes.tolist()))
    return {"nodes": nodes, "elems": elems, "codes": codes}


def fake_merge(m1, m2):
    nodes = m1["nodes"] + m2["nodes"]
    codes = m1["codes"] + m2["codes"]
    offset = len(m1["nodes"])
    elems = m1["elems"] + [[int(n) + offset for n in e] for e in m2["elems"]]
    return {"nodes": nodes, "elems": elems, "codes": codes}


def create_app():

    app = Flask(__name__, static_folder="static", static_url_path="/static")
    UPLOAD_FOLDER = r"c:\temp\uploads"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    @app.route("/")
    def index():
        return send_from_directory("static", "index.html")

    @app.route("/load_mesh", methods=["POST"])
    def load_mesh():
        file = request.files.get("file")
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        mesh = parse_mesh(path)
        return jsonify(mesh)

    @app.route("/merge", methods=["POST"])
    def merge_mesh():
        data = request.get_json()
        m1 = data.get("mesh1")
        m2 = data.get("mesh2")
        merged = merge(m1, m2)
        return jsonify(merged)

    return app


def run():
    app = create_app()
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    run()
