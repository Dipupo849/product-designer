"""Wrap the artifact-style body into a standalone document for the repo / GitHub Pages."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BODY = os.path.join(HERE, "repo_body.html")
OUT = os.path.join(HERE, "repo", "index.html")

TOP = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="description" content="A six-stage product design dossier: a subdivision-modelled leather sofa (3ds Max) and a mains-metering instrument enclosure (Fusion 360), taken from concept to photorealistic visualization. All plates path-traced in Blender Cycles.">
<style>
/* minimal reset - the hosted Artifact runtime supplies one; a standalone file needs its own */
*,*::before,*::after{box-sizing:border-box}
body{margin:0}
ul,ol,dl,dd,figure,blockquote{margin:0;padding:0}
ul,ol{list-style:none}
img,svg{max-width:100%}
</style>
"""

src = open(BODY, encoding="utf8").read()
i = src.index("</style>") + len("</style>")
head, body = src[:i], src[i:]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf8") as f:
    f.write(TOP + head + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n")

print(f"repo/index.html {os.path.getsize(OUT)/1024:.0f} KB")
