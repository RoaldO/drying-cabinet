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


def _evenly_pitched(span: float, pitch: float) -> list[float]:
    """Positions of bars tiling `span` at `pitch` spacing, centered on 0."""
    count = int(span // pitch) + 1
    covered = (count - 1) * pitch
    start = -covered / 2
    return [start + i * pitch for i in range(count)]


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
    hole_diameter: float = 76,
    outer_width: float = 85,
    outer_radius: float = 5,
) -> Sketch:
    outer = rounded_square(outer_width, outer_radius)
    hole = Circle(hole_diameter / 2)
    return outer - hole


def rounded_square_wall(
    inner_width: float = 80,
    outer_radius: float = 5,
    wall_thickness: float = DEFAULT_WALL_THICKNESS,
    height: float = 10,
) -> Part:
    outer_width = inner_width + 2 * wall_thickness
    outer = rounded_square(outer_width, outer_radius)
    inner = offset(outer, -wall_thickness)
    return extrude(outer - inner, height)


def duct_transition(
    inner_x: float = 80,
    inner_y: float = 80,
    duct_wall_thickness: float = DEFAULT_WALL_THICKNESS,
    vent_hole_diameter: float = 76,
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
    vent_hole_diameter: float = 76,
    heat_insert_diameter: float = 4.0,
    heat_insert_depth: float = 5,
    heat_insert_corner_distance: float = 101.6 / 2,
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
    vent_hole_diameter: float = 76,
    vent_outer_radius: float = 5,
    vent_float_height: float = 20,
    heat_insert_diameter: float = 4.0,
    heat_insert_depth: float = 5,
    heat_insert_corner_distance: float = 101.6 / 2,
    rim_inner_width: float = 81,  # 1mm extra fan clearance
    rim_wall_thickness: float = DEFAULT_WALL_THICKNESS,
    rim_height: float = 10,
) -> Part:
    # the vent/plate outer boundary matches the rim's outer boundary sitting on top of it
    vent_outer_width = rim_inner_width + 2 * rim_wall_thickness
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
        rim_inner_width, vent_outer_radius, rim_wall_thickness, rim_height
    )
    return duct_part + transition + plate + rim


def finger_guard_bars(diameter: float, bar_width: float, bar_gap: float) -> Sketch:
    """Parallel bars spanning a circle of `diameter`, clipped to that circle.

    `bar_gap` is the clear opening between bars a fingertip could pass
    through. 6mm is a common child-safety rule of thumb for finger-guard
    openings (e.g. small-appliance/toy guidelines use openings in this
    range to block a child's finger) -- worth checking against whatever
    standard actually applies to this build before trusting it blindly.
    """
    circle = Circle(diameter / 2)
    bar = Rectangle(bar_width, diameter)
    bars = [Pos(x, 0) * bar for x in _evenly_pitched(diameter, bar_width + bar_gap)]
    return reduce(lambda a, b: a + b, bars) & circle


def protector_grill(
    width: float = 85,  # matches the rim's new outer size (81mm inner + 2x wall)
    corner_radius: float = 5,
    hole_diameter: float = 76,
    bar_width: float = DEFAULT_WALL_THICKNESS,
    bar_gap: float = 6,
    bolt_hole_diameter: float = 3.2,
    bolt_corner_distance: float = 101.6 / 2,
    thickness: float = DEFAULT_WALL_THICKNESS,
    wall_thickness: float = DEFAULT_WALL_THICKNESS,
    wall_height: float = 10,
) -> Part:
    """Duct protector grill: a finger-guard mesh across the vent hole.

    Straight parallel bars keep it easy to print (uniform cross-section,
    no overhangs in its natural orientation) while leaving most of the
    hole open for airflow.

    Modeled here in its natural print orientation (this face down on the
    bed): the finger-guard plate prints first, with a small perimeter
    wall built up on top of it (in print direction). When inserted into
    the full assembly it gets rotated 180° (flipped upside down, not
    mirrored), so that wall ends up underneath, matching the duct's rim.
    """
    outer = rounded_square(width, corner_radius)
    profile = outer - Circle(hole_diameter / 2)
    profile += finger_guard_bars(hole_diameter, bar_width, bar_gap)

    bolt_hole = Circle(bolt_hole_diameter / 2)
    corner_offset = bolt_corner_distance / 2**0.5
    for sign_x in (-1, 1):
        for sign_y in (-1, 1):
            profile -= Pos(sign_x * corner_offset, sign_y * corner_offset) * bolt_hole

    plate = extrude(profile, thickness)
    wall = Pos(0, 0, thickness) * rounded_square_wall(
        width - 2 * wall_thickness, corner_radius, wall_thickness, wall_height
    )
    return plate + wall


def dust_cover(
    fit_over_width: float = 85,  # matches the grill's new outer size
    fit_margin: float = 1.0,
    corner_radius: float = 5,
    thickness: float = DEFAULT_WALL_THICKNESS,
    wall_thickness: float = DEFAULT_WALL_THICKNESS,
    wall_height: float = 10,
) -> Part:
    """Solid plate + perimeter wall, sized to slip over the duct/grill
    assembly (`fit_over_width`, its outer footprint) and cap it off when
    the fan is idle, keeping dust out.

    `fit_over_width` becomes the cover's inside dimension (plus
    `fit_margin` clearance so it actually slides on/off) instead of its
    outside one, so the whole shape grows outward from there.
    """
    cavity_width = fit_over_width + fit_margin
    outer_width = cavity_width + 2 * wall_thickness
    plate = extrude(rounded_square(outer_width, corner_radius), thickness)
    wall = Pos(0, 0, thickness) * rounded_square_wall(
        cavity_width, corner_radius, wall_thickness, wall_height
    )
    return plate + wall


def support_ribs(width: float, height: float, rib_width: float, rib_gap: float) -> Sketch:
    """Sparse crossed grid of ribs spanning a `width` x `height` rectangle.

    For holding something up (e.g. a filter) without blocking much
    airflow -- no finger-safety spacing needed here, so the gaps can be
    much wider than finger_guard_bars() uses. Ribs run both directions
    (rather than just one) so the blockage is spread evenly across the
    area instead of leaving long open channels that jet air through in
    streaks -- important right before a filter feeding an airbrush
    cabinet, where an even flow matters more than a lower pressure drop.
    """
    clip = Rectangle(width, height)
    x_bar = Rectangle(rib_width, height)
    y_bar = Rectangle(width, rib_width)
    bars = [Pos(x, 0) * x_bar for x in _evenly_pitched(width, rib_width + rib_gap)]
    bars += [Pos(0, y) * y_bar for y in _evenly_pitched(height, rib_width + rib_gap)]
    return reduce(lambda a, b: a + b, bars) & clip


def filter_enclosure(
    inner_x: float = 80,
    inner_y: float = 80,
    border_width: float = 10,
    outer_radius: float = 5,
    hole_diameter: float = 4.0,  # M3 heat-insert press-fit diameter
    holes_per_side: int = 3,
    base_offset: float = DEFAULT_WALL_THICKNESS,
    filter_thickness: float = 20,
    rib_width: float = DEFAULT_WALL_THICKNESS,
    rib_gap: float = 15,
    seal_lip_thickness: float = 3,
    seal_lip_height: float = DEFAULT_WALL_THICKNESS,
) -> Part:
    """Filter enclosure, printed in its regular (natural) orientation.

    The space below base_offset is the filter's support base: a rounded
    rectangle matching the flange's outer shape exactly, with the border
    kept solid (sealing against the walls above so air can't bypass the
    filter along the sides) and only the inner opening spanned by sparse
    ribs (holds the filter up without blocking much airflow). A short
    seal lip stands up right at the inner_x/inner_y boundary (where the
    border meets the ribs) to block air from sneaking sideways between
    the filter's edge and the border instead of through the filter.
    Above that, the duct flange's 2D shape (with holes) is extruded
    upward by filter_thickness (2cm) for this section.
    """
    outer_x = inner_x + 2 * border_width
    outer_y = inner_y + 2 * border_width
    border = RectangleRounded(outer_x, outer_y, outer_radius) - Rectangle(inner_x, inner_y)
    ribs = support_ribs(inner_x, inner_y, rib_width, rib_gap)
    base = extrude(border + ribs, base_offset)

    seal_lip = Rectangle(inner_x, inner_y) - Rectangle(
        inner_x - 2 * seal_lip_thickness, inner_y - 2 * seal_lip_thickness
    )
    base += Pos(0, 0, base_offset) * extrude(seal_lip, seal_lip_height)

    profile = flange_profile(
        inner_x, inner_y, border_width, outer_radius, hole_diameter, holes_per_side
    )
    walls = Pos(0, 0, base_offset) * extrude(profile, filter_thickness)

    return base + walls


FLOAT_HEIGHT = 10  # mm, ~1cm gap between stacked preview parts


def _stack_upside_down(part: Part, base_top: float, gap: float) -> Part:
    flipped = Rot(180, 0, 0) * part
    flipped_bottom = flipped.bounding_box().min.Z
    return Pos(0, 0, base_top + gap - flipped_bottom) * flipped


filter_part = filter_enclosure()
filter_top = filter_part.bounding_box().max.Z

duct_assembly = Pos(0, 0, filter_top + FLOAT_HEIGHT) * duct_with_vent()
duct_top = duct_assembly.bounding_box().max.Z

grill = _stack_upside_down(protector_grill(), duct_top, FLOAT_HEIGHT)
grill_top = grill.bounding_box().max.Z

cover = _stack_upside_down(dust_cover(), grill_top, FLOAT_HEIGHT)

part = filter_part

if __name__ == "__main__":
    show(filter_part, duct_assembly, grill, cover, colors=["green", "gray", "orange", "blue"])
