from build123d import *
from ocp_vscode import show


def flange_profile(
    inner_x: float = 80,
    inner_y: float = 80,
    border_width: float = 10,
    outer_radius: float = 5,
) -> Sketch:
    outer_x = inner_x + 2 * border_width
    outer_y = inner_y + 2 * border_width
    outer = RectangleRounded(outer_x, outer_y, outer_radius)
    inner = Rectangle(inner_x, inner_y)
    return outer - inner


part = flange_profile()

if __name__ == "__main__":
    show(part)
