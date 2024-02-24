import subprocess
from pathlib import Path


def openEditor(filename):
    subprocess.run([
        "kitty",
        "--name",
        "latex-terminal-ink",
        "--",
        "nvim",
        "--cmd",
        "let g:isInkscape='yes'",
        filename
    ])


def latexDocument(latex):
    return (
        r"""\documentclass[12pt,border=12pt]{standalone}

            \usepackage[utf8]{inputenc}
            \usepackage[T1]{fontenc}
            \usepackage{textcomp}
            \usepackage{amsmath, amssymb}
            \newcommand{\R}{\mathbb R}
            \usepackage{cmbright}

            \begin{document}
            """
        + latex
        + r"\end{document}"
    )


config = {
    "font": "Iosevka",
    "fontSize": 14,
    "openEditor": openEditor,
    "latexDocument": latexDocument,
}


# From https://stackoverflow.com/a/67692
def import_file(name, path):
    import importlib.util as util

    spec = util.spec_from_file_location(name, path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONFIG_PATH = Path("~/.config/lesson-manager").expanduser()
