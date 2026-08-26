"""
PNG renders -> web assets.

  repo/img/<name>-1400.jpg   full width
  repo/img/<name>-700.jpg    srcset half
  manifest.json              base64 payloads for the self-contained Artifact build
"""
import os, json, base64, io
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "renders")
IMGDIR = os.path.join(HERE, "repo", "img")
os.makedirs(IMGDIR, exist_ok=True)

WIDTHS = [1240, 700]      # 1240 is the native render width
Q = 88
EMBED_W, EMBED_Q = 1240, 88


def encode(im, width, quality):
    w, h = im.size
    if w != width:
        im = im.resize((width, round(h * width / w)), Image.LANCZOS)
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True,
                           progressive=True, subsampling=1)
    return buf.getvalue()


def main():
    manifest, total = {}, 0
    names = sorted(f[:-4] for f in os.listdir(SRC) if f.endswith(".png"))
    for name in names:
        im = Image.open(os.path.join(SRC, name + ".png"))
        row = {"w": im.size[0], "h": im.size[1], "files": {}}
        for width in WIDTHS:
            if width > im.size[0]:
                continue
            data = encode(im, width, Q)
            fn = f"{name}-{width}.jpg"
            with open(os.path.join(IMGDIR, fn), "wb") as f:
                f.write(data)
            row["files"][width] = {"file": f"img/{fn}", "bytes": len(data)}
        emb = encode(im, min(EMBED_W, im.size[0]), EMBED_Q)
        row["embed"] = "data:image/jpeg;base64," + base64.b64encode(emb).decode()
        row["embed_bytes"] = len(emb)
        total += len(emb)
        manifest[name] = row
        print(f"{name:22s} {im.size[0]}x{im.size[1]}  "
              f"embed {len(emb)/1024:6.0f} KB  "
              + "  ".join(f"{w}:{row['files'][w]['bytes']/1024:.0f}KB"
                          for w in row["files"]), flush=True)

    with open(os.path.join(HERE, "manifest.json"), "w") as f:
        json.dump(manifest, f)
    print(f"\n{len(manifest)} images | embedded payload {total/1048576:.2f} MB "
          f"(base64 ~{total*1.34/1048576:.2f} MB of the 16 MB artifact budget)")


if __name__ == "__main__":
    main()
