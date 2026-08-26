from functools import reduce

from build123d import *
from ocp_vscode import show

DEFAULT_WALL_THICKNESS = 2  # mm, ~4 perimeters at a 0.5mm nozzle


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
    hole_outward_offset: float = 0,
) -> Sketch:
    """`hole_outward_offset` shifts the hole centerline toward the outer edge.

    Needed when something (e.g. a duct wall) covers part of the border's
    inner edge on one face, so the holes should center on the strip that's
    actually visible/accessible there instead of on the full border width.
    """
    outer_x = inner_x + 2 * border_width
    outer_y = inner_y + 2 * border_width
    outer = RectangleRounded(outer_x, outer_y, outer_radius)
    inner = Rectangle(inner_x, inner_y)
    frame = outer - inner

    if holes_per_side > 0:
        hole_radius = hole_diameter / 2
        mid_x = inner_x / 2 + border_width / 2 + hole_outward_offset
        mid_y = inner_y / 2 + border_width / 2 + hole_outward_offset
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


def flange(
    inner_x: float = 80,
    inner_y: float = 80,
    border_width: float = 10,
    outer_radius: float = 5,
    hole_diameter: float = 3.2,
    holes_per_side: int = 3,
    thickness: float = DEFAULT_WALL_THICKNESS,
    hole_outward_offset: float = 0,
) -> Part:
    profile = flange_profile(
        inner_x,
        inner_y,
        border_width,
        outer_radius,
        hole_diameter,
        holes_per_side,
        hole_outward_offset,
    )
    return extrude(profile, thickness)


def duct_profile(
    inner_x: float = 80,
    inner_y: float = 80,
    wall_thickness: float = DEFAULT_WALL_THICKNESS,
) -> Sketch:
    outer_x = inner_x + 2 * wall_thickness
    outer_y = inner_y + 2 * wall_thickness
    return Rectangle(outer_x, outer_y) - Rectangle(inner_x, inner_y)


def duct(
    inner_x: float = 80,
    inner_y: float = 80,
    wall_thickness: float = DEFAULT_WALL_THICKNESS,
    height: float = 5,
) -> Part:
    return extrude(duct_profile(inner_x, inner_y, wall_thickness), height)


def fan_duct(
    inner_x: float = 80,
    inner_y: float = 80,
    border_width: float = 10,
    outer_radius: float = 5,
    hole_diameter: float = 3.2,
    holes_per_side: int = 3,
    flange_thickness: float = DEFAULT_WALL_THICKNESS,
    duct_wall_thickness: float = DEFAULT_WALL_THICKNESS,
    duct_height: float = 5,
) -> Part:
    base = flange(
        inner_x,
        inner_y,
        border_width,
        outer_radius,
        hole_diameter,
        holes_per_side,
        flange_thickness,
        hole_outward_offset=duct_wall_thickness / 2,
    )
    tube = duct(inner_x, inner_y, duct_wall_thickness, duct_height)
    tube = Pos(0, 0, flange_thickness) * tube
    return base + tube


def rounded_square(width: float, corner_radius: float) -> Sketch:
    return RectangleRounded(width, width, corner_radius)


def vent_profile(
    hole_diameter: float = 70,
    outer_width: float = 85,
    outer_radius: float = 5,
) -> Sketch:
    outer = rounded_square(outer_width, outer_radius)
    hole = Circle(hole_diameter / 2)
    return outer - hole


def rounded_square_wall(
    width: float = 85,
    corner_radius: float = 5,
    wall_thickness: float = DEFAULT_WALL_THICKNESS,
    height: float = 10,
) -> Part:
    outer = rounded_square(width, corner_radius)
    inner = offset(outer, -wall_thickness)
    return extrude(outer - inner, height)


def duct_transition(
    inner_x: float = 80,
    inner_y: float = 80,
    duct_wall_thickness: float = DEFAULT_WALL_THICKNESS,
    vent_hole_diameter: float = 70,
    vent_outer_width: float = 85,
    vent_outer_radius: float = 5,
    height: float = 20,
) -> Part:
    bottom = duct_profile(inner_x, inner_y, duct_wall_thickness)
    top = Pos(0, 0, height) * vent_profile(
        vent_hole_diameter, vent_outer_width, vent_outer_radius
    )
    return loft([bottom, top])


def heat_insert_plate(
    vent_outer_width: float = 85,
    vent_outer_radius: float = 5,
    vent_hole_diameter: float = 70,
    heat_insert_diameter: float = 4.0,
    heat_insert_depth: float = 5,
    heat_insert_corner_distance: float = 40,
) -> Part:
    """Rounded-square plate with the vent hole plus one M3 heat-insert hole
    per corner (5 cylinders removed in total), extruded to the insert depth.
    """
    profile = rounded_square(vent_outer_width, vent_outer_radius) - Circle(
        vent_hole_diameter / 2
    )
    insert = Circle(heat_insert_diameter / 2)
    corner_offset = heat_insert_corner_distance / 2**0.5
    for sign_x in (-1, 1):
        for sign_y in (-1, 1):
            profile -= Pos(sign_x * corner_offset, sign_y * corner_offset) * insert
    return extrude(profile, heat_insert_depth)


def duct_with_vent(
    inner_x: float = 80,
    inner_y: float = 80,
    border_width: float = 10,
    outer_radius: float = 5,
    hole_diameter: float = 3.2,
    holes_per_side: int = 3,
    flange_thickness: float = DEFAULT_WALL_THICKNESS,
    duct_wall_thickness: float = DEFAULT_WALL_THICKNESS,
    duct_height: float = 5,
    vent_hole_diameter: float = 70,
    vent_outer_width: float = 85,
    vent_outer_radius: float = 5,
    vent_float_height: float = 20,
    heat_insert_diameter: float = 4.0,
    heat_insert_depth: float = 5,
    heat_insert_corner_distance: float = 40,
    rim_wall_thickness: float = DEFAULT_WALL_THICKNESS,
    rim_height: float = 10,
) -> Part:
    duct_part = fan_duct(
        inner_x,
        inner_y,
        border_width,
        outer_radius,
        hole_diameter,
        holes_per_side,
        flange_thickness,
        duct_wall_thickness,
        duct_height,
    )
    duct_top = flange_thickness + duct_height
    transition = Pos(0, 0, duct_top) * duct_transition(
        inner_x,
        inner_y,
        duct_wall_thickness,
        vent_hole_diameter,
        vent_outer_width,
        vent_outer_radius,
        vent_float_height,
    )
    plate = Pos(0, 0, duct_top + vent_float_height) * heat_insert_plate(
        vent_outer_width,
        vent_outer_radius,
        vent_hole_diameter,
        heat_insert_diameter,
        heat_insert_depth,
        heat_insert_corner_distance,
    )
    rim = Pos(0, 0, duct_top + vent_float_height + heat_insert_depth) * rounded_square_wall(
        vent_outer_width, vent_outer_radius, rim_wall_thickness, rim_height
    )
    return duct_part + transition + plate + rim


part = duct_with_vent()

if __name__ == "__main__":
    show(part)
