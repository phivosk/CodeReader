import sys
import sv_ttk

if sys.platform == "win32":
    try:
        import pywinstyles
    except ImportError:
        pywinstyles = None
else:
    pywinstyles = None


def apply_windows_titlebar_style(root):
    if not pywinstyles or not sys.platform == "win32":
        return

    dark_color = "#1c1c1c"
    light_color = "#fafafa"

    is_dark = sv_ttk.get_theme() == "dark"
    color_to_apply = dark_color if is_dark else light_color

    version = sys.getwindowsversion()

    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, color_to_apply)
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if is_dark else "normal")