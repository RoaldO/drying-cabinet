from functools import reduce

from build123d import *
from ocp_vscode import show


def _segment_centers(span: float, count: int) -> list[float]:
    """Center of each of `count` equal segments spanning [-span, span].

    Keeps holes away from the corners instead of anchoring one at each end.
    """
    if count <= 1:
        return [0.0]
    step = 2 * span / count
    return [-span + step * (i + 0.5) for i in range(count)]


def flange_profile(
    inner_x: float = 80,
    inner_y: float = 80,
    border_width: float = 10,
    outer_radius: float = 5,
    hole_diameter: float = 3.2,
    holes_per_side: int = 3,
) -> Sketch:
    outer_x = inner_x + 2 * border_width
    outer_y = inner_y + 2 * border_width
    outer = RectangleRounded(outer_x, outer_y, outer_radius)
    inner = Rectangle(inner_x, inner_y)
    frame = outer - inner

    if holes_per_side > 0:
        hole_radius = hole_diameter / 2
        mid_x = inner_x / 2 + border_width / 2
        mid_y = inner_y / 2 + border_width / 2
        span_x = outer_x / 2 - outer_radius - hole_radius
        span_y = outer_y / 2 - outer_radius - hole_radius

        holes = []
        for x in _segment_centers(span_x, holes_per_side):
            holes.append(Pos(x, mid_y) * Circle(hole_radius))
            holes.append(Pos(x, -mid_y) * Circle(hole_radius))
        for y in _segment_centers(span_y, holes_per_side):
            holes.append(Pos(mid_x, y) * Circle(hole_radius))
            holes.append(Pos(-mid_x, y) * Circle(hole_radius))

        frame -= reduce(lambda a, b: a + b, holes)

    return frame


part = flange_profile()

if __name__ == "__main__":
    show(part)
