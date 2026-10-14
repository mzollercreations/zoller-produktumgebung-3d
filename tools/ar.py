#!/usr/bin/env python3
"""AR-/3D-Ansicht im Showroom: dieselben CAD-Modelle wie auf den Produktseiten der Webseite.

Quelle ist das Nachbarprojekt ``zoller-webseite``:
    assets/ar/<id>.glb|.usdz|.webp   Modelle (tools/ar_models.py, ar_posters.py der Webseite)
    content/ar_models.json           Außenmaße B × T × H in mm
    content/ar.json                  Seiten -> Modelle, Gerätenamen, Texte in allen Sprachen
    assets/vendor/model-viewer.min.js, draco/, qrcode.js

    python3 tools/ar.py            # Modelle + Bibliotheken kopieren, docs/data/products.json ergänzen

tools/build.py ruft ``patch()`` für die deutsche Fassung auf, tools/build_locale.py für jede Sprachfassung.
Ergebnis je Fassung: ``data.ar`` (Modelle mit Maßen in der Landesschreibweise, Texte) und ``product.ar`` (Modell-IDs,
erstes = Standard). Nur Standardbibliothek.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT.parent / "zoller-webseite"
DOCS = ROOT / "docs"
PLANER = "https://mzollercreations.github.io/zoller-werkzeugraum-planer/"   # Werkzeugraum-Planer (eigenes Repo)
DOT_DECIMAL = ("en", "zh", "ja", "ko")     # wie die Webseite (tools/build.py num), dazu es-MX

sys.path.insert(0, str(SRC / "tools"))
import i18n as web_i18n  # noqa: E402  feste Texte der Webseite (»Jetzt anfragen«, »Werkzeugraum-Planer«)

AR = json.loads((SRC / "content" / "ar.json").read_text(encoding="utf-8"))
SIZES = json.loads((SRC / "content" / "ar_models.json").read_text(encoding="utf-8"))
KEYS = ("eyebrow", "title", "lead", "w", "d", "h", "area", "note", "ar", "ar_hint", "qr_title", "qr_text", "dims", "reset",
        "zoom_in", "zoom_out", "fullscreen", "drag", "loading", "noar", "arfail", "shown", "model", "viewer", "full")


def models_for(de_path):
    """Modell-IDs einer Produktseite (deutscher Pfad), sonst []."""
    return [m for m in AR["pages"].get(de_path, []) if m in SIZES]


def text(code, lang, key):
    tx = AR["texts"]
    return tx.get(code, {}).get(key) or tx.get(lang, {}).get(key) or tx["de"][key]


def web_text(code, lang, s):
    return web_i18n.T.get(code, {}).get(s) or web_i18n.T.get(lang, {}).get(s) or s


def block(lang="de", code="de-DE", planer=PLANER):
    """Modelle (Maße in der Schreibweise des Landes, USA zusätzlich Fuß/Zoll) und Texte einer Fassung."""
    dot = lang in DOT_DECIMAL or code == "es-MX"
    us = code == "en-US"
    m_ = lambda mm: f"{mm / 1000:.2f}" if dot else f"{mm / 1000:.2f}".replace(".", ",")
    ft = lambda mm: f"{round(mm / 25.4) // 12}′ {round(mm / 25.4) % 12}″"
    t = {k: text(code, lang, k) for k in KEYS}
    models = {}
    for mid, s in SIZES.items():
        if mid not in AR["devices"]:
            continue
        mm = s["size_mm"]
        name = AR["devices"][mid]
        area = mm[0] * mm[1] / 1e6
        dims = " × ".join(m_(v) for v in mm) + " m"
        files = [SRC / "assets" / "ar" / f"{mid}.{x}" for x in ("glb", "usdz", "webp")]
        ver = hashlib.sha1(b"".join(f.read_bytes() for f in files if f.exists())).hexdigest()[:8]   # ?v= gegen alte Fassungen im Cache
        e = {"name": name, "mm": mm, "v": ver, "title": t["title"].format(name=name), "label": t["viewer"].format(name=name),
             "full": t["full"].format(dims=dims), "area": (f"{area:.2f}" if dot else f"{area:.2f}".replace(".", ",")) + " m²",
             "area2": f"{area * 10.7639:.0f} sq ft" if us else ""}
        for k, v in zip(("w", "d", "h"), mm):
            e[k] = m_(v) + " m"
            e[k + "2"] = ft(v) if us else ""
        models[mid] = e
    t.update({"cta": web_text(code, lang, "Jetzt anfragen"), "planer": web_text(code, lang, "Werkzeugraum-Planer")})
    return {"models": models, "t": t, "planer": planer, "family": [p for p in AR.get("family", [])]}


def patch(data, lang="de", code="de-DE", planer=PLANER):
    """products.json einer Fassung um die AR-Angaben ergänzen (in place)."""
    blk = block(lang, code, planer)
    n = 0
    for p in data["products"]:
        ids = models_for(p.get("path", ""))
        if ids:
            p["ar"] = ids
            if p["path"] in blk["family"]:
                p["arShown"] = blk["t"]["shown"].format(name=blk["models"][ids[0]]["name"])
            n += 1
        else:
            p.pop("ar", None)
            p.pop("arShown", None)
    blk.pop("family")
    data["ar"] = blk
    return n


def sync_assets():
    """Modelle, Vorschaubilder und Bibliotheken aus der Webseite kopieren (nur geänderte Dateien)."""
    out = DOCS / "ar"
    out.mkdir(parents=True, exist_ok=True)
    need = {m for ids in AR["pages"].values() for m in ids if m in SIZES}
    copied = 0
    for mid in sorted(need):
        for ext in ("glb", "usdz", "webp"):
            src, dst = SRC / "assets" / "ar" / f"{mid}.{ext}", out / f"{mid}.{ext}"
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                shutil.copyfile(src, dst)
                copied += 1
    for old in out.iterdir():
        if old.stem not in need:
            old.unlink()
    vend = DOCS / "assets" / "vendor"
    for rel in ("model-viewer.min.js", "qrcode.js", "draco/draco_decoder.js", "draco/draco_decoder.wasm", "draco/draco_wasm_wrapper.js"):
        src, dst = SRC / "assets" / "vendor" / rel, vend / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            shutil.copyfile(src, dst)
            copied += 1
    return len(need), copied


def main():
    n_models, copied = sync_assets()
    f = DOCS / "data" / "products.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    n = patch(data)
    f.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"AR: {n_models} Modelle ({copied} Dateien kopiert), {n} Produkte mit AR-Ansicht")


if __name__ == "__main__":
    main()
