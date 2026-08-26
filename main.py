from build123d import *

part = Box(100, 100, 10)

if __name__ == "__main__":
    export_stl(part, "drying-cabinet.stl")
