import argparse
from .dfs2_to_mesh_converter import dfs2_to_fm_mesh

def main():
    parser = argparse.ArgumentParser(description="Convert DFS2 file to FM mesh")
    parser.add_argument("input", help="Path to input DFS2 file")
    parser.add_argument("output", help="Path to output mesh file")
    args = parser.parse_args()

    dfs2_to_fm_mesh(args.input, args.output)

if __name__ == "__main__":
    main()
