#!/usr/bin/env python3
"""Erzeugt die Produktdaten und Bilder für die ZOLLER Produktumgebung 3D.

Quelle ist der strukturierte Inhalt der deutschen zoller.info-Seiten aus dem
Projekt ``zoller-webseite`` (content/pages/*.json und docs/fileadmin/…).

    .venv/bin/python tools/build.py [pfad/zu/zoller-webseite]

Ergebnis:
    docs/data/products.json   Kategorien, Produkte, Werkzeugtypen
    docs/img/p/<id>.webp      freigestelltes Produktbild für die 3D-Szene (512 px)
    docs/img/hd/<id>.webp     dasselbe in hoher Auflösung (1024 px), lädt bei Fokus
    docs/img/g/…              Bilder für das Detail-Panel (Header, Galerie, Modelle)
    docs/img/wall/<cat>.webp  Rückwand-Motive der Themenwelten

Benötigt Pillow (``pip install pillow``).
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT.parent / "zoller-webseite"
PAGES = SRC / "content" / "pages"
FILEADMIN = SRC / "docs"
OUT = ROOT / "docs"
SITE = "https://www.zoller.info"
WEB = "https://mzollercreations.github.io/zoller-webseite"   # eigene Webseite (Relaunch)
WEB_DOCS = SRC / "docs"


RENAMES_DE = json.loads((SRC / "content" / "renames.json").read_text(encoding="utf-8")).get("de", {})


def web(path):
    """Link auf die eigene ZOLLER-Webseite; nur falls die Seite dort fehlt, auf zoller.info.
    Umbenannte deutsche Adressen (content/renames.json, »de«) zeigen gleich auf die neue Adresse."""
    clean_path = "/" + path.strip("/")
    for old, new in RENAMES_DE.items():
        if clean_path == old or clean_path.startswith(old + "/"):
            clean_path = new + clean_path[len(old):]
            break
    if (WEB_DOCS / clean_path.strip("/") / "index.html").exists():
        return f"{WEB}{clean_path}/"
    return SITE + clean_path

# ---------------------------------------------------------------------------
# Kategorien (Reihenfolge wie auf zoller.info/produkte)
# ---------------------------------------------------------------------------
CATEGORIES = [
    ("einstellen-messen", "Einstellen & Messen", "csm_teaser_presetting_small_"),
    ("toolmanagement", "Toolmanagement", "csm_teaser_toolmanagement_small_"),
    ("pruefen-messen", "Prüfen & Messen", "csm_teaser_inspection_small_"),
    ("automation", "Automation", "csm_teaser_automation_small_"),
    ("schrumpftechnik", "Schrumpftechnik", "csm_teaser_shrinking_small_"),
    ("werkzeugaufnahmen", "Werkzeugaufnahmen", "csm_teaser_tooling_"),
    ("wuchttechnik", "Wuchttechnik", "csm_teaser_balancing_small_"),
]

# ---------------------------------------------------------------------------
# Produkte: (id, Pfad auf zoller.info, Kategorie, Unterkategorie, Darstellung,
#            Höhe in Metern in der Szene, Bild-Präfix in fileadmin)
# Darstellung: machine = freigestelltes Gerät auf Bodenplatte
#              pedestal = Tischgerät auf Säule
#              software = schwebendes Software-Symbol
#              screen = Präsentationsdisplay mit Foto (kein freigestelltes Bild)
#              package = TMS-Softwarepaket (prozedural)
#              vitrine = kleine Exponate in Glasvitrine
# ---------------------------------------------------------------------------
P = "/produkte"
PRODUCTS = [
    # Einstellen & Messen
    ("smile", f"{P}/einstellen-messen/vertikale-geraete/smile", "einstellen-messen", "Vertikale Geräte", "machine", 1.75, "csm_smile_preview_"),
    ("venturion", f"{P}/einstellen-messen/vertikale-geraete/venturion", "einstellen-messen", "Vertikale Geräte", "machine", 1.95, "csm_venturion_preview_"),
    ("hyperion", f"{P}/einstellen-messen/horizontale-geraete/hyperion", "einstellen-messen", "Horizontale Geräte", "machine", 1.75, "csm_hyperion_preview_"),
    ("smile-gbo", f"{P}/einstellen-messen/cnc-steinbearbeitung/smile-gbo", "einstellen-messen", "CNC-Steinbearbeitung", "machine", 1.8, "csm_smileGBO_preview_"),
    ("reamcheck", f"{P}/einstellen-messen/vertikale-geraete/venturion/modelle/reamcheck", "einstellen-messen", "Speziallösungen", "machine", 2.05, "csm_reamCheck_preview_"),
    ("torquematic", f"{P}/einstellen-messen/vertikale-geraete/venturion/modelle/torquematic", "einstellen-messen", "Speziallösungen", "machine", 1.95, "csm_torquematic_preview_"),
    ("tribos", f"{P}/einstellen-messen/vertikale-geraete/venturion/modelle/tribos", "einstellen-messen", "Speziallösungen", "machine", 1.95, "csm_tribos_preview_"),
    ("phoenix", f"{P}/einstellen-messen/spezialloesungen/uebersicht/phoenix", "einstellen-messen", "Speziallösungen", "machine", 1.95, "csm_phoenix_preview_"),
    ("zenit", f"{P}/einstellen-messen/spezialloesungen/uebersicht/zenit", "einstellen-messen", "Speziallösungen", "machine", 1.9, "csm_zenit_preview_"),
    ("equick", f"{P}/einstellen-messen/spezialloesungen/uebersicht/equick", "einstellen-messen", "Speziallösungen", "machine", 2.0, "csm_eQuick_preview_"),
    ("gemini", f"{P}/einstellen-messen/spezialloesungen/uebersicht/gemini", "einstellen-messen", "Speziallösungen", "machine", 2.0, "csm_gemini_preview_"),
    ("millcheck", f"{P}/einstellen-messen/spezialloesungen/uebersicht/millcheck", "einstellen-messen", "Speziallösungen", "machine", 1.9, "csm_millCheck_preview_"),
    # Toolmanagement
    ("tms-core", f"{P}/toolmanagement/software/tms-core", "toolmanagement", "Software", "software", 1.25, "csm_TMSCore_product_"),
    ("zstock", f"{P}/toolmanagement/software/add-on-zstock", "toolmanagement", "Software", "software", 1.1, "csm_zStock_product_"),
    ("zcam-integration", f"{P}/toolmanagement/software/add-on-zcam-integration", "toolmanagement", "Software", "software", 1.1, "csm_zCAM_Integration_product_"),
    ("zresources", f"{P}/toolmanagement/software/add-on-zresources", "toolmanagement", "Software", "software", 1.1, "csm_zResources_product_"),
    ("zshopfloor", f"{P}/toolmanagement/software/add-on-zshopfloor", "toolmanagement", "Software", "software", 1.1, "csm_zShopfloor_product_"),
    ("zconnectivity", f"{P}/toolmanagement/software/add-on-zconnectivity", "toolmanagement", "Software", "software", 1.1, "csm_zConnectivity_product_"),
    ("zintegration", f"{P}/toolmanagement/software/add-on-zintegration", "toolmanagement", "Software", "software", 1.1, "csm_zIntegration_product_"),
    ("tms-starter", f"{P}/toolmanagement/tms-tool-management-solutions/softwarepakete/starter-lagerverwaltung", "toolmanagement", "TMS Softwarepakete", "package", 1.0, None),
    ("tms-bronze", f"{P}/toolmanagement/tms-tool-management-solutions/softwarepakete/bronze-cad-cam-modul", "toolmanagement", "TMS Softwarepakete", "package", 1.0, None),
    ("tms-silver", f"{P}/toolmanagement/tms-tool-management-solutions/softwarepakete/silver-betriebsorganisation", "toolmanagement", "TMS Softwarepakete", "package", 1.0, None),
    ("tms-gold", f"{P}/toolmanagement/tms-tool-management-solutions/softwarepakete/gold-shopfloormanagement", "toolmanagement", "TMS Softwarepakete", "package", 1.0, None),
    ("twister", f"{P}/toolmanagement/werkzeuglager/twister", "toolmanagement", "Werkzeuglager", "machine", 1.95, "csm_twister__preview_"),
    ("autolock", f"{P}/toolmanagement/werkzeuglager/autolock", "toolmanagement", "Werkzeuglager", "machine", 1.95, "csm_autolock__preview_"),
    ("toolorganizer", f"{P}/toolmanagement/werkzeuglager/toolorganizer", "toolmanagement", "Werkzeuglager", "machine", 1.95, "csm_toolOrganizer_preview_"),
    ("keeper", f"{P}/toolmanagement/werkzeuglager/keeper", "toolmanagement", "Werkzeuglager", "machine", 1.95, "csm_keeper_preview_"),
    ("zstorage", f"{P}/toolmanagement/werkzeuglager/zstorage", "toolmanagement", "Werkzeuglager", "pedestal", 0.42, "csm_zStorage_preview_"),
    ("ztower", f"{P}/toolmanagement/smart-cabinets/ztower", "toolmanagement", "Werkzeugmontage", "machine", 2.0, "csm_zTower_preview_"),
    ("toolstation", f"{P}/toolmanagement/smart-cabinets/toolstation", "toolmanagement", "Werkzeugmontage", "machine", 1.7, "csm_toolStation_preview_"),
    ("toolcart", f"{P}/toolmanagement/smart-cabinets/toolcart", "toolmanagement", "Werkzeugtransport", "machine", 1.45, "csm_toolcart750__preview_"),
    ("zidcode", f"{P}/toolmanagement/zidcode", "toolmanagement", "Datentransfer", "pedestal", 0.8, "csm_zidCode_preview_"),
    # Prüfen & Messen
    ("genius", f"{P}/pruefen-messen/universal-messmaschinen/genius", "pruefen-messen", "Universal-Messmaschinen", "machine", 2.0, "csm_genius_1_"),
    ("titan", f"{P}/pruefen-messen/universal-messmaschinen/titan", "pruefen-messen", "Universal-Messmaschinen", "machine", 2.05, "csm_titan__preview_"),
    ("smartcheck", f"{P}/pruefen-messen/universal-messmaschinen/smartcheck", "pruefen-messen", "Universal-Messmaschinen", "machine", 1.9, "csm_smartCheck_preview_"),
    ("pombasic", f"{P}/pruefen-messen/prozessorientertes-messen/pombasic", "pruefen-messen", "Prozessorientiertes Messen", "pedestal", 0.72, "csm_pombasic__preview_"),
    ("mmfocus", f"{P}/pruefen-messen/prozessorientertes-messen/mmfocus", "pruefen-messen", "Prozessorientiertes Messen", "pedestal", 0.8, "csm_myFocus__preview_"),
    ("condiaz", f"{P}/pruefen-messen/cnc-steinbearbeitung/condiaz", "pruefen-messen", "CNC-Steinbearbeitung", "pedestal", 0.85, "csm_conDiaz_preview_"),
    ("condress", f"{P}/pruefen-messen/cnc-steinbearbeitung/condress", "pruefen-messen", "CNC-Steinbearbeitung", "pedestal", 0.62, "csm_conDress_preview_"),
    ("hobcheck", f"{P}/pruefen-messen/universal-messmaschinen/hobcheck", "pruefen-messen", "Speziallösungen", "machine", 2.05, "csm_hobCheck__preview_"),
    ("threadcheckcc", f"{P}/pruefen-messen/universal-messmaschinen/threadcheckcc", "pruefen-messen", "Speziallösungen", "machine", 2.05, "csm_threadCheckCC__preview_"),
    ("threadcheck", f"{P}/pruefen-messen/spezialloesungen/uebersicht/threadcheck", "pruefen-messen", "Speziallösungen", "machine", 1.95, "csm_threadCheck_preview_"),
    ("sawcheck", f"{P}/pruefen-messen/spezialloesungen/uebersicht/sawcheck", "pruefen-messen", "Speziallösungen", "machine", 1.95, "csm_sawcheck_preview_"),
    ("edgecontrol-600", f"{P}/pruefen-messen/spezialloesungen/uebersicht/edgecontrol-600", "pruefen-messen", "Speziallösungen", "machine", 1.95, "csm_edgeControl600_preview_"),
    ("edgecontrol", f"{P}/pruefen-messen/spezialloesungen/uebersicht/edgecontrol", "pruefen-messen", "Speziallösungen", "screen", 2.0, "csm_edgeControl_7b3d78c68b"),
    ("3dcheck", f"{P}/pruefen-messen/spezialloesungen/uebersicht/3dcheck", "pruefen-messen", "Speziallösungen", "screen", 2.0, "csm_3dCheck_5a94f0c180"),
    ("caz", f"{P}/pruefen-messen/spezialloesungen/uebersicht/caz", "pruefen-messen", "Speziallösungen", "screen", 2.0, "csm_software_caz_"),
    # Automation
    ("coralogistic", f"{P}/automation/werkzeuglogistik/coralogistic", "automation", "Werkzeuglogistik", "machine", 2.0, "csm_coraLogistics_preview_"),
    ("coramachineload", f"{P}/automation/werkzeuglogistik/coramachineload", "automation", "Werkzeuglogistik", "machine", 2.1, "csm_coraMaschineLoad_preview_"),
    ("corameasure-lg", f"{P}/automation/werkzeugvorbereitung/corameasure-lg", "automation", "Werkzeugvorbereitung", "machine", 2.2, "csm_corameasureLG_preview_"),
    ("robobox", f"{P}/automation/werkzeugvorbereitung/robobox", "automation", "Werkzeugvorbereitung", "machine", 2.25, "csm_roboBox_preview_"),
    ("micbox", f"{P}/automation/werkzeugvorbereitung/micbox", "automation", "Werkzeugvorbereitung", "machine", 2.0, "csm_micbox_preview_"),
    ("loadbox", f"{P}/automation/werkzeugbereitstellung/loadbox", "automation", "Werkzeugbereitstellung", "machine", 2.1, "csm_loadBox_preview_"),
    ("roboset-2", f"{P}/automation/werkzeuginspektion/roboset-2", "automation", "Werkzeuginspektion", "machine", 2.1, "csm_genius_roboSet2__preview_"),
    ("robomark", f"{P}/automation/laserbeschriftung/robomark", "automation", "Laserbeschriftung", "machine", 2.15, "csm_roboMark_preview_"),
    # Schrumpftechnik
    ("powershrink", f"{P}/schrumpftechnik/powershrink", "schrumpftechnik", "Schrumpfgeräte", "machine", 1.95, "csm_powerShrink_preview_"),
    ("redomatic", f"{P}/schrumpftechnik/redomatic", "schrumpftechnik", "Schrumpfgeräte", "machine", 1.95, "csm_redomatic_preview_"),
    # Werkzeugaufnahmen
    ("tooling", f"{P}/werkzeugaufnahmen", "werkzeugaufnahmen", "Tooling Solutions", "vitrine", 1.15, "csm_ToolingSolutions4_preview_"),
    # »idChip« (2026-10-12): eigene Seite der Webseite (zoller-webseite/tools/idchip.py), Freisteller eines Halters mit Chip
    ("idchip", f"{P}/werkzeugaufnahmen/idchip", "werkzeugaufnahmen", "Tooling Solutions", "pedestal", 0.5, "zoller_idchip_werkzeughalter"),
    # Wuchttechnik
    ("toolbalancer", f"{P}/wuchttechnik/toolbalancer", "wuchttechnik", "Wuchtmaschinen", "machine", 1.9, "csm_toolBalancer_preview_"),
]

# Querverweise: Produkte, die zoller.info zusätzlich in anderen Kategorien zeigt
ALSO = {
    "corameasure-lg": [("einstellen-messen", "Automationslösungen")],
    "robobox": [("einstellen-messen", "Automationslösungen")],
    "condress": [("einstellen-messen", "CNC-Steinbearbeitung")],
    "redomatic": [("einstellen-messen", "Speziallösungen")],
    "smartcheck": [("einstellen-messen", "Speziallösungen")],
    "roboset-2": [("pruefen-messen", "Automationslösungen")],
}

# Texte für Produkte ohne eigenen Navigations-Claim
PACKAGE_TIER = {"tms-starter": "STARTER", "tms-bronze": "BRONZE", "tms-silver": "SILVER", "tms-gold": "GOLD"}

CTA_TEXTS = {"1:1 Expertengespräch", "Jetzt kaufen", "Jetzt anfragen", "Paketvergleich", "Mehr erfahren",
             "Angebot anfordern", "Kontakt aufnehmen", "Zum Shop"}

TEASER_HREFS = ("/solutions", "myzoller.com/de/de/expert", "/unternehmen/kontakt", "/ihr-erfolg", "/academy")


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def page_file(path):
    return PAGES / (path.strip("/").replace("/", "__") + ".json")


def load_page(path):
    f = page_file(path)
    return json.loads(f.read_text()) if f.exists() else None


def clean(s):
    """HTML entfernen, Leerraum normalisieren, Zero-Width-Zeichen entfernen."""
    if not s:
        return ""
    s = re.sub(r"<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = s.replace("\ufeff", "").replace("\u200b", "").replace("\u202f", " ").replace("❘", "|")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([.,;:!?])", r"\1", s)
    return s


def clean_name(s):
    s = clean(s)
    s = re.sub(r"»\s+", "»", s)
    s = re.sub(r"\s+«", "«", s)
    return s


def paragraphs(body):
    """Liste der Absätze eines HTML-Textblocks ohne Buttons."""
    if not body:
        return []
    body = re.sub(r'<a class="btn"[^>]*>.*?</a>', "", body, flags=re.S)
    out = []
    for m in re.finditer(r"<(p|li)[^>]*>(.*?)</\1>", body, flags=re.S):
        t = clean(m.group(2))
        if t and len(t) > 2 and not t.startswith("●") and t not in CTA_TEXTS:
            out.append(t)
    if not out:
        t = clean(body)
        if t:
            out.append(t)
    return out


def headings(header):
    return [(m.group(1), clean(m.group(2))) for m in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", header or "", flags=re.S)]


def iter_blocks(blocks):
    for b in blocks:
        yield b
        if b.get("type") == "cols":
            for col in b.get("columns", []):
                yield from iter_blocks(col)


def find_image(prefix):
    """Größte lokale Datei in fileadmin, deren Name mit prefix beginnt."""
    hits = sorted((FILEADMIN / "fileadmin").rglob(prefix + "*"), key=lambda p: p.stat().st_size, reverse=True)
    hits = [h for h in hits if h.suffix.lower() in (".webp", ".png", ".jpg", ".jpeg")]
    return hits[0] if hits else None


def local(src):
    if not src or not src.startswith("/fileadmin/"):
        return None
    p = FILEADMIN / src.lstrip("/")
    return p if p.exists() else None


copied = {}


def copy_gallery(src):
    """Kopiert ein Bild aus fileadmin nach docs/img/g und gibt den Web-Pfad zurück."""
    p = local(src)
    if not p:
        return None
    if p in copied:
        return copied[p]
    dst = OUT / "img" / "g" / p.name
    if not dst.exists():
        shutil.copyfile(p, dst)
    copied[p] = f"img/g/{p.name}"
    return copied[p]


def is_teaser(img):
    href = img.get("href", "") or ""
    return any(t in href for t in TEASER_HREFS) or "teaser" in (img.get("src") or "").lower()


def bleed(im):
    """Farben in transparente Bereiche ausdehnen, damit Mipmaps keine dunklen Ränder bekommen."""
    a = np.asarray(im.getchannel("A"), dtype=np.float32) / 255.0
    rgb = np.asarray(im.convert("RGB"), dtype=np.float32)
    fill = rgb.copy()
    done = a >= 0.5
    for radius in (2, 6, 16, 48):
        pm = Image.fromarray(np.uint8(np.clip(rgb * a[..., None], 0, 255))).filter(ImageFilter.GaussianBlur(radius))
        ab = Image.fromarray(np.uint8(a * 255)).filter(ImageFilter.GaussianBlur(radius))
        pm = np.asarray(pm, dtype=np.float32)
        ab = np.asarray(ab, dtype=np.float32) / 255.0
        est = pm / np.maximum(ab, 1e-4)[..., None]
        take = (~done) & (ab > 0.002)
        fill[take] = est[take]
        done |= take
    out = np.where(a[..., None] >= 0.5, rgb, fill)
    res = Image.fromarray(np.uint8(np.clip(out, 0, 255)))
    res.putalpha(im.getchannel("A"))
    return res


def cutout(src_path, pid):
    """Freigestelltes Bild auf den sichtbaren Bereich zuschneiden und in zwei Größen speichern."""
    im = Image.open(src_path).convert("RGBA")
    alpha = im.getchannel("A").point(lambda a: 255 if a > 14 else 0)
    bbox = alpha.getbbox() or (0, 0, im.width, im.height)
    l, t, r, b = bbox
    pad = int(max(r - l, b - t) * 0.012)
    l, t = max(0, l - pad), max(0, t - pad)
    r, b = min(im.width, r + pad), min(im.height, b + pad)
    crop = im.crop((l, t, r, b))
    out = {}
    for size, folder in ((512, "p"), (1024, "hd")):
        c = crop.copy()
        c.thumbnail((size, size), Image.LANCZOS)
        bleed(c).save(OUT / "img" / folder / f"{pid}.webp", "WEBP", quality=90, method=6, exact=True)
        out[folder] = c.size
    w, h = out["p"]
    return {"aspect": round(w / h, 4)}


def screen_image(src_path, pid):
    im = Image.open(src_path).convert("RGB")
    for size, folder in ((768, "p"), (1280, "hd")):
        c = im.copy()
        c.thumbnail((size, size), Image.LANCZOS)
        c.save(OUT / "img" / folder / f"{pid}.webp", "WEBP", quality=86, method=6)
    return {"aspect": round(im.width / im.height, 4)}


def tables_of(blocks):
    specs = []
    for b in iter_blocks(blocks):
        if b.get("type") != "table":
            continue
        rows = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", b.get("table", ""), flags=re.S):
            cells = [clean(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S)]
            if any(cells):
                rows.append(cells)
        if rows:
            title = clean(b.get("header", "")) or ""
            specs.append({"title": title, "rows": rows[:24]})
    return specs


# ---------------------------------------------------------------------------
# Navigation (Claims, Kurztexte) und Werkzeugtypen
# ---------------------------------------------------------------------------
nav = json.loads((SRC / "content" / "nav.json").read_text())
nav_info = {}


def walk(n, trail):
    if n.get("href", "").startswith("/produkte") and ("claim" in n or "desc" in n):
        nav_info.setdefault(n["href"], {"claim": clean(n.get("claim")), "desc": clean(n.get("desc")),
                                        "label": clean_name(n.get("label"))})
    for c in n.get("children", []):
        walk(c, trail + [n.get("label")])


for m in nav["main"]:
    walk(m, [])

overview = load_page("/produkte")
plist = next(b for b in overview["blocks"] if b["type"] == "productlist")
cat_text = {it["href"].split("/")[-1]: clean(it["text"]) for it in plist["rows"][0]["items"]}
tool_types = []
tool_map = {}
list_text = {}
for key, v in plist["tools"].items():
    tool_types.append(v["label"])
    for it in v["items"]:
        tool_map.setdefault(it["href"], []).append(v["label"])
        list_text.setdefault(it["href"], clean(it.get("text")))


# ---------------------------------------------------------------------------
# Produkte extrahieren
# ---------------------------------------------------------------------------
def extract(pid, path, kind):
    page = load_page(path)
    if not page:
        raise SystemExit(f"Seite fehlt: {path}")
    blocks = page["blocks"]
    d = {"title": clean_name(page["title"]), "headline": "", "claim": "", "intro": [], "sections": [],
         "highlights": [], "features": [], "gallery": [], "header_img": None, "links": [], "shop": None,
         "specs": [], "models": []}

    # Unterseiten-Navigation
    sub = next((b for b in blocks if b["type"] == "subnav"), None)
    subpages = []
    if sub:
        for it in sub.get("items", []):
            href = it.get("href") or ""
            if href and href != path and href.startswith(path + "/"):
                subpages.append((clean(it["label"]).lstrip("/ ").strip(), href))

    hdr = next((b for b in blocks if b["type"] == "product_header"), None)
    if hdr:
        d["claim"] = " ".join(paragraphs(hdr.get("text")))
        if hdr.get("img"):
            d["header_img"] = copy_gallery(hdr["img"]["src"])

    for b in iter_blocks(blocks):
        t = b.get("type")
        if t == "textmedia":
            hs = headings(b.get("header"))
            ps = paragraphs(b.get("body"))
            imgs = [i for i in b.get("images", []) if not is_teaser(i)]
            if hs and not d["headline"] and not hdr:
                # Speziallösungen: <h3>Name</h3><h1>Headline</h1>
                h1 = [h for lvl, h in hs if lvl in ("1", "2")]
                d["headline"] = h1[0] if h1 else hs[-1][1]
                d["intro"] = ps[:3]
            elif ps and (hs or len(" ".join(ps)) > 120):
                title = next((h for lvl, h in hs if lvl in ("1", "2")), hs[0][1] if hs else "")
                if not d["intro"]:
                    if hdr or not d["headline"]:
                        d["headline"] = d["headline"] or title
                    d["intro"] = ps[:3]
                elif title and len(d["sections"]) < 4 and "Service" not in title:
                    d["sections"].append({"title": title, "text": ps[:2]})
            for i in imgs:
                cap = i.get("caption") or ""
                ctitle = clean(i.get("title")) or (headings(cap)[0][1] if headings(cap) else "")
                ctext = " ".join(paragraphs(re.sub(r"<h[1-6][^>]*>.*?</h[1-6]>", "", cap)))
                ctext = ctext.replace("Mehr erfahren", "").strip()
                src = copy_gallery(i["src"]) if len(d["gallery"]) < 8 else None
                if src:
                    d["gallery"].append({"src": src, "title": ctitle, "text": ctext})
        elif t == "highlight":
            d["highlights"] += [clean(x) for x in b.get("items", []) if clean(x)]
        elif t == "hotspots":
            for s in b.get("spots", []):
                txt = " ".join(paragraphs(re.sub(r"<h[1-6][^>]*>.*?</h[1-6]>", "", s.get("text", ""))))
                d["features"].append({"title": clean_name(s.get("label")), "text": txt})
        elif t == "quotes":
            for s in b.get("slides", []):
                hs = headings(s.get("text"))
                ps = paragraphs(s.get("text"))
                if hs and ps and len(d["sections"]) < 5:
                    d["sections"].append({"title": clean_name(hs[0][1]), "text": ps[:2]})
        elif t == "overlay":
            if b.get("img") and len(d["gallery"]) < 8:
                src = copy_gallery(b["img"]["src"])
                if src:
                    d["gallery"].append({"src": src, "title": clean(b.get("title")), "text": " ".join(paragraphs(b.get("text")))})
        elif t == "tiles":
            for tl in b.get("tiles", []):
                hs = headings(tl.get("text"))
                ps = paragraphs(tl.get("text"))
                if hs:
                    d["features"].append({"title": hs[0][1], "text": " ".join(ps)})

    # Shop-Link
    raw = json.dumps(blocks, ensure_ascii=False)
    m = re.search(r'href=\\"(https://myzoller\.com/de/de/shop/[^"\\]+)', raw)
    if m:
        d["shop"] = m.group(1)

    # Technische Daten
    d["specs"] = tables_of(blocks)
    for label, href in subpages:
        if href.endswith("/technische-daten"):
            tp = load_page(href)
            if tp:
                d["specs"] += tables_of(tp["blocks"])

    # Modelle
    for label, href in subpages:
        if not href.endswith("/modelle"):
            continue
        mp = load_page(href)
        if not mp:
            continue
        for b in iter_blocks(mp["blocks"]):
            for i in b.get("images", []) if b.get("type") == "textmedia" else []:
                if is_teaser(i) or not i.get("title"):
                    continue
                cap = i.get("caption") or ""
                text = " ".join(paragraphs(re.sub(r"<h[1-6][^>]*>.*?</h[1-6]>", "", cap))).replace("Mehr erfahren", "").strip()
                d["models"].append({"name": clean_name(i["title"]), "text": text, "img": copy_gallery(i["src"]),
                                    "href": web(i["href"]) if (i.get("href") or "").startswith("/produkte") else None})

    # Links zu zoller.info
    d["links"] = [{"label": "Produktseite", "href": web(path)}]
    for label, href in subpages:
        d["links"].append({"label": label, "href": web(href)})
    if not d["intro"] and d["claim"]:
        d["intro"] = [d["claim"]]
    if not d["features"]:
        d["features"] = [{"title": g["title"], "text": g["text"]} for g in d["gallery"] if g["title"] and g["text"]]
    d["specs"] = [s for s in d["specs"] if s["rows"]][:6]
    d["features"] = d["features"][:14]
    return d


products = []
for pid, path, cat, sub, kind, height, img in PRODUCTS:
    info = extract(pid, path, kind)
    nv = nav_info.get(path, {})
    name = nv.get("label") or info["title"]
    badge = None
    if name.startswith("Add-on "):
        name, badge = name[len("Add-on "):], "Add-on"
    if pid == "equick":
        name = "»eQuick 200M«"
    if pid == "tooling":
        name = "Tooling Solutions"
    if kind == "package":
        name = info["title"].replace("Shopfloormanagement", "Shopfloor­management")
    teaser = nv.get("desc") or list_text.get(path) or ""
    claim = nv.get("claim") or info["claim"] or info["headline"]
    if pid == "tooling":
        teaser = cat_text.get("werkzeugaufnahmen", "")
        claim = "Über 2500 Werkzeugaufnahmen"
        info["intro"] = [
            "ZOLLER Tooling Solutions: Werkzeugaufnahmen für alle gängigen Schnittstellen – optional mit »idChip« "
            "für mehr Prozesssicherheit durch aktuelle Werkzeugdaten. Kompatibel zu ZOLLER TMS Tool Management Solutions.",
        ]
        info["links"] = [{"label": "Tooling-Shop auf myzoller.com", "href": "https://myzoller.com/de/de/shop/tooling"},
                         {"label": "Übersicht Werkzeugaufnahmen", "href": web(path)}]
        info["shop"] = "https://myzoller.com/de/de/shop/tooling"
        info["highlights"] = ["Über 2500 Werkzeugaufnahmen", "Optional mit »idChip«", "Kompatibel zu ZOLLER TMS"]
        info["header_img"] = copy_gallery("/fileadmin/_processed_/d/c/" + find_image("csm_header_tooling_").name) if find_image("csm_header_tooling_") else None
    entry = {
        "id": pid, "name": name, "badge": badge, "cat": cat, "sub": sub, "kind": kind, "h": height,
        "url": web(path), "path": path, "claim": claim, "teaser": teaser,
        "headline": info["headline"], "intro": info["intro"], "sections": info["sections"],
        "highlights": info["highlights"][:4], "features": info["features"], "models": info["models"][:10],
        "specs": info["specs"], "gallery": info["gallery"], "links": info["links"], "shop": info["shop"],
        "header": info["header_img"], "tools": tool_map.get(path, []),
        "also": [{"cat": c, "sub": s} for c, s in ALSO.get(pid, [])],
    }
    if kind == "package":
        entry["tier"] = PACKAGE_TIER[pid]
        entry["claim"] = entry["claim"] or info["headline"]
        entry["aspect"] = 1.0
    else:
        src = find_image(img)
        if not src:
            raise SystemExit(f"Bild fehlt für {pid}: {img}")
        meta = screen_image(src, pid) if kind == "screen" else cutout(src, pid)
        entry.update(meta)
        if not entry["header"]:
            entry["header"] = f"img/hd/{pid}.webp"
    products.append(entry)
    print(f"  {pid:18s} {entry['name'][:30]:30s} {len(entry['features']):2d} Merkmale  {len(entry['specs'])} Tabellen  {len(entry['models']):2d} Modelle  {len(entry['gallery'])} Bilder")

# Rückwände der Themenwelten
categories = []
for cid, name, wall in CATEGORIES:
    src = find_image(wall)
    if src:
        im = Image.open(src).convert("RGB")
        im.thumbnail((1400, 1400), Image.LANCZOS)
        im.save(OUT / "img" / "wall" / f"{cid}.webp", "WEBP", quality=84, method=6)
    subs = []
    for p in products:
        if p["cat"] == cid and p["sub"] not in subs:
            subs.append(p["sub"])
    categories.append({"id": cid, "name": name, "text": cat_text.get(cid, ""), "url": web(f"/produkte/{cid}"),
                       "wall": f"img/wall/{cid}.webp" if src else None, "subs": subs,
                       "count": sum(1 for p in products if p["cat"] == cid)})

data = {"generated_from": "https://www.zoller.info/produkte", "site": WEB + "/", "categories": categories,
        "toolTypes": tool_types, "products": products}
(OUT / "data" / "products.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
print(f"\n{len(products)} Produkte in {len(categories)} Kategorien, {len(copied)} Panel-Bilder kopiert.")
