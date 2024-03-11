from Xlib import X, XK

from clipboard import copy
from constants import TARGET
from vim import open_vim
import text
import styles

# Set of pressed keys
pressed = set()


# This is a list of received events that haven't been handled yet.
# Only when the user releases a key, the script knows what it should do.
# Then it either discards the preceding events, or replays them.
events = []


def event_to_string(self, event):
    mods = []
    if event.state & X.ShiftMask:
        mods.append("Shift")

    if event.state & X.ControlMask:
        mods.append("Control")

    keycode = event.detail
    keysym = self.disp.keycode_to_keysym(keycode, 0)
    char = XK.keysym_to_string(keysym)

    return "".join(mod + "+" for mod in mods) + (char if char else "?")


def replay(self):
    for e in events:
        self.inkscape.send_event(e, propagate=True)

    self.disp.flush()
    self.disp.sync()


def normal_mode(self, event, char):
    events.append(event)

    if event.type == X.KeyPress and char:
        pressed.add(event_to_string(self, event))
        return

    if event.type != X.KeyRelease:
        return

    handled = False
    if len(pressed) > 1:
        paste_style(self, pressed)
        handled = True
    elif len(pressed) == 1:
        # Get the only element in pressed
        ev = next(iter(pressed))
        handled = handle_single_key(self, ev)

    # replay events to Inkscape if we couldn't handle them
    if not handled:
        replay(self)

    events.clear()
    pressed.clear()


def handle_single_key(self, ev):
    if ev == "q":
        # Enter
        self.press("Return")
    elif ev == "w":
        # Save
        self.press("s", X.ControlMask)
    elif ev == "a":
        # Add objects mode
        self.mode = styles.object_mode
    elif ev == "Shift+a":
        # Save objects mode
        styles.save_object_mode(self)
    elif ev == "s":
        # Apply style mode
        self.mode = styles.style_mode
    elif ev == "Shift+s":
        # Save style mode
        styles.save_style_mode(self)
    elif ev == "d":
        # Pencil
        self.press("p")
    elif ev == "f":
        # Bezier
        self.press("b")
    elif ev == "t":
        # Vim mode
        open_vim(self, compile_latex=False)
    elif ev == "Shift+t":
        # Vim mode pre-rendered
        open_vim(self, compile_latex=True)
    elif ev == "v":
        # Snap
        self.press("percent", X.ShiftMask)
    elif ev == "z":
        # Undo
        self.press("z", X.ControlMask)
    elif ev == "x":
        # Delete
        self.press("Delete")
    elif ev == "c":
        # Redo
        self.press("z", X.ControlMask | X.ShiftMask)
    elif ev == "`":
        # Disabled mode
        self.press("t")
        self.mode = text.text_mode
    else:
        # Not handled
        return False
    return True


def paste_style(self, combination):
    """This creates the style depending on the combination of keys."""

    # Stolen from TikZ
    pt = 1.327  # pixels
    w = 0.4 * pt
    thick_width = 0.8 * pt
    very_thick_width = 1.2 * pt

    style = {"stroke-opacity": 1}

    # Clean
    if "y" in combination:
        style["fill"] = "none"
        style["stroke"] = "#000000"
        style["stroke-width"] = w
        style["marker-end"] = "none"
        style["marker-start"] = "none"
        style["stroke-dasharray"] = "none"

    # Fills
    if "1" in combination:
        style["fill"] = "#BBEEFF"
        style["fill-opacity"] = 1

    if "2" in combination:
        style["fill"] = "#FF80DF"
        style["fill-opacity"] = 1

    if "3" in combination:
        style["fill"] = "#000000"
        style["fill-opacity"] = 1

    if "4" in combination:
        style["fill"] = "#FFFFFF"
        style["fill-opacity"] = 1
        style["stroke"] = "#000000"

    if "5" in combination:
        style["fill"] = "#000000"
        style["fill-opacity"] = 0.12

    if "6" in combination:
        style["fill"] = "none"
        style["fill-opacity"] = 1

    # Stroke
    if "q" in combination:
        style["stroke"] = "#3DC6F3"

    if "w" in combination:
        style["stroke"] = "#F034A3"

    if "e" in combination:
        style["stroke"] = "#000000"

    if "r" in combination:
        style["stroke"] = "#FFFFFF"

    if "t" in combination:
        style["stroke"] = "#000000"
        style["stroke-opacity"] = 0.12

    # Sizes
    if "a" in combination:
        w = thick_width
        style["stroke-width"] = w

    if "s" in combination:
        w = very_thick_width
        style["stroke-width"] = w

    if "d" in combination:
        style["stroke-width"] = w

    # Dashes
    if "f" in combination:
        style["stroke-dasharray"] = f"{w},{2*pt}"

    if "g" in combination:
        style["stroke-dasharray"] = f"{3*pt},{3*pt}"

    if "h" in combination:
        style["stroke-dasharray"] = "none"

    color = style.get("stroke", "#000000")
    fill_opacity = style.get("stroke-opacity", 1.0)

    # Arrows
    if "z" in combination:
        style["marker-start"] = f"url(#marker-arrow-{w}-{color}-{fill_opacity})"
        style["marker-end"] = "none"

    if "x" in combination:
        style["marker-start"] = f"url(#marker-arrow-{w}-{color}-{fill_opacity})"
        style["marker-end"] = f"url(#marker-arrow-{w}-{color}-{fill_opacity})"

    if "c" in combination:
        style["marker-start"] = "none"
        style["marker-end"] = f"url(#marker-arrow-{w}-{color}-{fill_opacity})"

    if "v" in combination:
        style["marker-start"] = "none"
        style["marker-end"] = "none"

    # Start creation of the svg.
    # Later on, we'll write this svg to the clipboard, and send Ctrl+Shift+V to
    # Inkscape, to paste this style.
    svg = """
          <?xml version="1.0" encoding="UTF-8" standalone="no"?>
          <svg>
          """

    # If a marker is applied, add its definition to the clipboard
    # Arrow styles stolen from tikz
    if ("marker-end" in style and style["marker-end"] != "none") or (
        "marker-start" in style and style["marker-start"] != "none"
    ):
        svg += f"""
<defs id="marker-defs">
    <marker
        id="marker-arrow-{w}-{color}-{fill_opacity}"
        orient="auto-start-reverse"
        refY="0" refX="0"
        markerHeight="1.690" markerWidth="0.911"
    >
        <g transform="scale({(2.40 * w + 3.87)/(4.5*w)})">
            <path
                d="M 1.99252,0 -1.19551,1.59401 0,0 -1.19551,-1.59401"
                style="fill:{color};fill-opacity:{fill_opacity};fill-rule:nonzero;stroke:none;"
            />
        </g>
    </marker>
</defs>
"""

    style_string = ";".join(
        "{}: {}".format(key, value)
        for key, value in sorted(style.items(), key=lambda x: x[0])
    )
    svg += f'<inkscape:clipboard style="{style_string}" /></svg>'

    copy(svg, target=TARGET)
    self.press("v", X.ControlMask | X.ShiftMask)
