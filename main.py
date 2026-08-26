from build123d import *
from ocp_vscode import show

part = Box(100, 100, 10)

if __name__ == "__main__":
    show(part)
    export_stl(part, "drying-cabinet.stl")
