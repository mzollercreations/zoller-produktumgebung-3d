#!/usr/bin/env python3
"""Erzeugt die Sprachfassungen der Produktumgebung 3D für alle Länderseiten (content/sites.json der Webseite).

Quelle sind die Länderfassungen im Projekt ``zoller-webseite`` (content/sites/<sprachpfad>/, siehe dort
content/sites.json). Aufbau der Halle, Produktbilder und Reihenfolge kommen aus der deutschen Fassung
(docs/data/products.json, erzeugt von tools/build.py), alle Texte aus den Produktseiten des Landes.

    python3 tools/build_locale.py [pfad/zu/zoller-webseite]

Ergebnis je Sprache (Ordner = Sprachcode, z. B. docs/en-ca/):
    index.html             Oberfläche in der Landessprache (Texte: tools/i18n.json)
    data/products.json     Produkte, Themenwelten, Werkzeugtypen in der Landessprache
Bilder der Detail-Panels landen gemeinsam in docs/img/g/. Benötigt nur die Python-Standardbibliothek.

Der Länder-Knopf (Weltkugel + Flagge) und die Länderliste kommen ebenfalls aus content/sites.json; sie werden
in jede Fassung eingesetzt, auch in die deutsche docs/index.html (zwischen <!--lang-flag--> bzw. <!--lang-sites-->).
"""
import hashlib
import html
import json
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT.parent / "zoller-webseite"
DOCS = ROOT / "docs"
UI = json.loads((ROOT / "tools" / "i18n.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(SRC / "tools"))
import flags as web_flags  # noqa: E402  Flaggen der Länderseiten
import i18n as web_i18n  # noqa: E402  feste Texte der Webseite (u. a. Unterkategorien)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ar  # noqa: E402  AR-/3D-Ansicht (Modelle und Texte der Webseite)
import names as web_names  # noqa: E402  Produktnamen der maschinellen Übersetzung (»titanium« -> »titan«)

# Schaltflächen und Teaser, die nicht in die Produkttexte gehören (alle Sprachen)
CTA = {"1:1 Expertengespräch", "Jetzt kaufen", "Jetzt anfragen", "Paketvergleich", "Mehr erfahren", "Angebot anfordern",
       "Kontakt aufnehmen", "Zum Shop", "Learn more", "Read more", "Request a quote", "Request now", "Buy now",
       "Contact us", "Get in touch", "To the shop", "Package comparison", "Inquire now", "En savoir plus",
       "Demander une offre", "Acheter maintenant", "Nous contacter", "Vers la boutique", "Más información",
       "Leer más", "Solicitar cotización", "Comprar ahora", "Contáctenos", "Ir a la tienda", "Solicitar información"}
MORE = ("Mehr erfahren", "Learn more", "Read more", "En savoir plus", "Más información", "Leer más")
TEASER_HREFS = ("myzoller.com", "/expert", "kontakt", "contact", "contacto", "ihr-erfolg", "your-success",
                "votre-reussite", "su-exito", "academy", "academie", "academia")
# Weitere Sprachen: Knöpfe und »Mehr erfahren« der Länderfassungen von zoller.info und die festen Texte der Webseite
MORE += ("Scopri di più", "Per saperne di più", "Saber mais", "Saiba mais", "Läs mer", "Dowiedz się więcej", "Więcej o tym",
         "Več informacij", "Več o tem", "Zjistěte více", "Více informací", "További információk", "Zistiť viac",
         "Viac informácií", "了解更多", "詳細はこちら", "詳しく見る", "자세히 알아보기", "자세히 보기", "Подробнее",
         "Daha fazla bilgi")
CTA |= set(MORE) | {
    "Richiedi ora", "Fissa subito un appuntamento", "Acquista ora", "Solicitar agora", "Solicite agora", "Marque agora uma consulta",
    "Agende uma conversa agora", "Encontrar um contacto", "Entrar em contato", "Begär information nu", "Fråga nu", "Begär offert nu",
    "Köp nu", "Zapytaj teraz", "Kup teraz", "Umów się na wizytę już teraz", "Pošljite povpraševanje", "Prikaži izdelke",
    "Določite termin zdaj", "Zahtevajte zdaj", "Požádat o informace", "Požádat o nabídku", "Koupit nyní", "Kérjen ajánlatot most",
    "Kérjen most", "Termékek megtekintése", "Vásároljon most", "Most foglaljon időpontot", "Požiadať o informácie",
    "Požiadať teraz", "Požiadajte o informácie", "Kúpiť teraz", "立即咨询", "立即预约", "立即购买", "查找联系人", "显示产品",
    "今すぐお問い合わせください", "今すぐお問い合わせ", "製品を見る", "今すぐ予約する", "지금 문의하기", "제품 보기",
    "지금 예약하기", "1:1 전문가 상담", "지금 구매하기",
    "Отправить запрос", "Запросить", "Купить", "Встреча с экспертом 1:1", "Беседа с экспертом 1:1", "Связаться с нами",
    "Сравнение пакетов", "Записаться на демонстрацию", "Показать продукты", "Hemen bilgi isteyin", "Hemen talep edin",
    "Hemen satın alın", "1:1 uzman görüşmesi", "Hemen bizimle iletişime geçin", "Paket karşılaştırması", "Teklif isteyin",
    "Demo randevusu alın", "Ürünleri göster"}
for _lang, _texts in web_i18n.T.items():
    CTA |= {_texts[k] for k in ("Jetzt anfragen", "Mehr erfahren", "Jetzt kaufen", "Kontakt aufnehmen") if k in _texts}


TR_SKIP = {"src", "href", "id", "ftype", "bg", "space", "pos", "type", "kind", "path", "url", "de_path", "src_path",
           "og_image", "value", "tag", "date", "lat", "lng", "languages", "breadcrumb"}


def tr_nodes(obj, tr, skip=TR_SKIP):
    """Wie translate() in tools/build.py der Webseite: ganze Texte oder Textstellen zwischen HTML-Tags ersetzen."""
    if isinstance(obj, dict):
        return {k: (v if k in skip else tr_nodes(v, tr, skip)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [tr_nodes(v, tr, skip) for v in obj]
    if not isinstance(obj, str) or not obj.strip():
        return obj

    def node(t, in_html):
        k = html.unescape(t).strip()
        if k not in tr or tr[k] == k:
            return t
        lead, trail = t[:len(t) - len(t.lstrip())], t[len(t.rstrip()):]
        return lead + (html.escape(tr[k], quote=False) if in_html else tr[k]) + trail
    if "<" in obj and re.search(r"<[a-zA-Z/][^>]*>", obj):
        return re.sub(r"(?<=>)([^<]+)(?=<)", lambda m: node(m.group(1), True), ">" + obj + "<")[1:-1]
    return node(obj, False)


def clean(s):
    if not s:
        return ""
    s = re.sub(r"<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("\ufeff", "").replace("\u200b", "").replace("\u202f", " ").replace("❘", "|")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([.,;:!?])", r"\1", s)
    return s.replace("»»", "»").replace("««", "«")


def clean_name(s):
    return re.sub(r"\s+«", "«", re.sub(r"»\s+", "»", clean(s)))


def paragraphs(body):
    if not body:
        return []
    body = re.sub(r'<a class="btn"[^>]*>.*?</a>', "", body, flags=re.S)
    out = []
    for m in re.finditer(r"<(p|li)[^>]*>(.*?)</\1>", body, flags=re.S):
        t = clean(m.group(2))
        if t and len(t) > 2 and not t.startswith("●") and t not in CTA:
            out.append(t)
    if not out and clean(body):
        out.append(clean(body))
    return out


def headings(header):
    return [(m.group(1), clean(m.group(2))) for m in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", header or "", flags=re.S)]


def iter_blocks(blocks):
    for b in blocks:
        yield b
        if b.get("type") == "cols":
            for col in b.get("columns", []):
                yield from iter_blocks(col)


def without_more(t):
    for m in MORE:
        t = t.replace(m, "")
    return t.strip()


class Locale:
    def __init__(self, site, loc):
        self.site, self.loc, self.lang = site, loc, loc["lang"]
        self.dir = loc["code"].lower()
        self.base_url = site["url"] + (loc["dir"] + "/" if loc["dir"] else "")
        self.prefix = "/" + loc["src"]
        folder = SRC / "content" / "sites" / loc["src"]
        self.pages, self.de2loc, self.loc2de = {}, {}, {}
        for f in sorted((folder / "pages").glob("*.json")):
            p = json.loads(f.read_text(encoding="utf-8"))
            p["path"] = web_names.rename_path(loc["src"], p["path"])   # …/titanium -> …/titan
            self.pages[p["path"]] = p
            if p.get("de_path"):
                self.de2loc.setdefault(p["de_path"], p["path"])
                self.loc2de[p["path"]] = p["de_path"]
        tr_file = folder / "translations.json"
        self.tr = json.loads(tr_file.read_text(encoding="utf-8")) if tr_file.exists() else {}
        if self.tr:   # Textstellen zwischen HTML-Tags vorab übersetzen, wie tools/build.py der Webseite (geklonte Fassungen, z. B. ru/tr)
            self.pages = {k: tr_nodes(v, self.tr) for k, v in self.pages.items()}
        self.reps = {}   # Ersetzungen in Texten, z. B. »génie« -> »genius« (auch aus dem Overlay der Länderseite)
        overlay = [SRC / "content" / "sites" / loc["overlay"]] if loc.get("overlay") else []
        for rep_file in [f / "replace.json" for f in [folder] + overlay]:
            if rep_file.exists():
                self.reps.update(json.loads(rep_file.read_text(encoding="utf-8")))
        corr_file = folder / "corrections.json"   # Korrektorat der Länderseite (ganze Texte, wie auf der Webseite)
        self.corr = json.loads(corr_file.read_text(encoding="utf-8")) if corr_file.exists() else {}
        rules_file = folder / "corrections_rules.json"   # Fachbegriffe, greifen auch in zusammengesetzten Texten
        self.rules = json.loads(rules_file.read_text(encoding="utf-8")) if rules_file.exists() else []
        self.nav = json.loads((folder / "nav.json").read_text(encoding="utf-8"))
        self.files = [SRC / site["out"], SRC / "docs"]   # gespiegelte Dateien der Länderseite, sonst der deutschen
        self.copied = {}
        self.teaser = TEASER_HREFS + tuple(self.de2loc[d] for d in ("/ihr-erfolg", "/akademie", "/unternehmen/kontakt") if d in self.de2loc)

    # ---------------------------------------------------------------- Hilfen
    def t(self, s):
        """Text übersetzen: unübersetzte Reste (translations.json der Webseite), Ersetzungen (replace.json) und
        Produktnamen (tools/names.py der Webseite) wie auf der Länderseite."""
        if not isinstance(s, str):
            return s
        s = self.tr.get(s.strip(), s)
        for a, b in self.reps.items():
            s = s.replace(a, b)
        s = web_names.drop_alternatives(s)   # »basculante|orientable« -> »basculante«, wie auf der Länderseite
        s = web_names.fix(s, self.lang)
        c = self.corr.get(s.strip())
        if c is not None and s.strip():
            return s.replace(s.strip(), c)
        for a, b in self.rules:
            s = s.replace(a, b)
        return s

    def ui(self, s):
        return UI.get(self.lang, {}).get(s, s)

    def local(self, href):
        """/ca/products/… -> /products/…"""
        href = html.unescape(href or "").split("#")[0].split("?")[0].rstrip("/")
        if href.startswith(self.prefix + "/"):
            href = href[len(self.prefix):]
        return web_names.rename_path(self.loc["src"], href)

    def page(self, de_path):
        lp = self.de2loc.get(de_path)
        return self.pages.get(lp) if lp else None

    def url(self, local_path):
        return self.base_url + ("" if local_path in ("", "/startseite") else local_path.strip("/") + "/")

    def web_de(self, de_path):
        lp = self.de2loc.get(de_path)
        return self.url(lp) if lp else None

    def copy_img(self, src):
        if not src or not src.startswith("/fileadmin/"):
            return None
        rel = urllib.parse.unquote(src.split("?")[0]).lstrip("/")
        p = next((d / rel for d in self.files if (d / rel).exists()), None)
        if not p:
            return None
        if p.name not in self.copied:
            dst = DOCS / "img" / "g" / p.name
            if not dst.exists():
                shutil.copyfile(p, dst)
            self.copied[p.name] = f"img/g/{p.name}"
        return self.copied[p.name]

    # ---------------------------------------------------------------- Produkt
    def extract(self, de_path):
        page = self.page(de_path)
        if not page:
            return None
        blocks = json.loads(json.dumps(page["blocks"]))
        d = {"title": clean_name(self.t(page["title"])), "headline": "", "claim": "", "intro": [], "sections": [],
             "highlights": [], "features": [], "gallery": [], "header_img": None, "links": [], "shop": None,
             "specs": [], "models": []}
        T = lambda s: self.t(clean(s))
        own = page["path"]
        subpages = []
        sub = next((b for b in blocks if b["type"] == "subnav"), None)
        if sub:
            for it in sub.get("items", []):
                lp = self.local(it.get("href"))
                if lp and lp != own and lp.startswith(own + "/"):
                    subpages.append((clean(self.t(it["label"])).lstrip("/ ").strip(), lp))
        hdr = next((b for b in blocks if b["type"] == "product_header"), None)
        if hdr:
            d["claim"] = " ".join(T(x) for x in paragraphs(hdr.get("text")))
            if hdr.get("img"):
                d["header_img"] = self.copy_img(hdr["img"]["src"])
        for b in iter_blocks(blocks):
            typ = b.get("type")
            if typ == "textmedia":
                hs = [(l, T(h)) for l, h in headings(b.get("header"))]
                ps = [T(x) for x in paragraphs(b.get("body"))]
                imgs = [i for i in b.get("images", []) if not any(k in urllib.parse.unquote(i.get("href") or "") for k in self.teaser)
                        and "teaser" not in (i.get("src") or "").lower()]
                if hs and not d["headline"] and not hdr:
                    h1 = [h for lvl, h in hs if lvl in ("1", "2")]
                    d["headline"] = h1[0] if h1 else hs[-1][1]
                    d["intro"] = ps[:3]
                elif ps and (hs or len(" ".join(ps)) > 120):
                    title = next((h for lvl, h in hs if lvl in ("1", "2")), hs[0][1] if hs else "")
                    if not d["intro"]:
                        if hdr or not d["headline"]:
                            d["headline"] = d["headline"] or title
                        d["intro"] = ps[:3]
                    elif title and len(d["sections"]) < 4 and not re.match(r"Servic", title):
                        d["sections"].append({"title": title, "text": ps[:2]})
                for i in imgs:
                    cap = i.get("caption") or ""
                    ctitle = T(i.get("title")) or (T(headings(cap)[0][1]) if headings(cap) else "")
                    ctext = without_more(" ".join(T(x) for x in paragraphs(re.sub(r"<h[1-6][^>]*>.*?</h[1-6]>", "", cap))))
                    src = self.copy_img(i["src"]) if len(d["gallery"]) < 8 else None
                    if src:
                        d["gallery"].append({"src": src, "title": ctitle, "text": ctext})
            elif typ == "highlight":
                d["highlights"] += [T(x) for x in b.get("items", []) if clean(x)]
            elif typ == "hotspots":
                for s in b.get("spots", []):
                    txt = " ".join(T(x) for x in paragraphs(re.sub(r"<h[1-6][^>]*>.*?</h[1-6]>", "", s.get("text", ""))))
                    d["features"].append({"title": clean_name(self.t(s.get("label", ""))), "text": txt})
            elif typ == "quotes":
                for s in b.get("slides", []):
                    hs, ps = headings(s.get("text")), [T(x) for x in paragraphs(s.get("text"))]
                    if hs and ps and len(d["sections"]) < 5:
                        d["sections"].append({"title": clean_name(self.t(hs[0][1])), "text": ps[:2]})
            elif typ == "overlay":
                if b.get("img") and len(d["gallery"]) < 8:
                    src = self.copy_img(b["img"]["src"])
                    if src:
                        d["gallery"].append({"src": src, "title": T(b.get("title")), "text": " ".join(T(x) for x in paragraphs(b.get("text")))})
            elif typ == "tiles":
                for tl in b.get("tiles", []):
                    hs = headings(tl.get("text"))
                    if hs:
                        d["features"].append({"title": T(hs[0][1]), "text": " ".join(T(x) for x in paragraphs(tl.get("text")))})
        m = re.search(r'href=\\"(https://myzoller\.com/[a-z]{2,3}/[a-z]{2}/shop/[^"\\]+)', json.dumps(blocks, ensure_ascii=False))
        if m:
            d["shop"] = m.group(1)
        d["specs"] = self.tables(blocks)
        for label, lp in subpages:
            if self.loc2de.get(lp, "").endswith("/technische-daten") and lp in self.pages:
                d["specs"] += self.tables(self.pages[lp]["blocks"])
        for label, lp in subpages:
            if not self.loc2de.get(lp, "").endswith("/modelle") or lp not in self.pages:
                continue
            for b in iter_blocks(self.pages[lp]["blocks"]):
                for i in b.get("images", []) if b.get("type") == "textmedia" else []:
                    if not i.get("title") or any(k in urllib.parse.unquote(i.get("href") or "") for k in self.teaser):
                        continue
                    cap = i.get("caption") or ""
                    text = without_more(" ".join(T(x) for x in paragraphs(re.sub(r"<h[1-6][^>]*>.*?</h[1-6]>", "", cap))))
                    href = self.local(i.get("href"))
                    d["models"].append({"name": clean_name(self.t(i["title"])), "text": text, "img": self.copy_img(i["src"]),
                                        "href": self.url(href) if href in self.pages else None})
        d["links"] = [{"label": self.ui("Produktseite"), "href": self.url(own)}]
        d["links"] += [{"label": label, "href": self.url(lp)} for label, lp in subpages if lp in self.pages]
        if not d["intro"] and d["claim"]:
            d["intro"] = [d["claim"]]
        if not d["features"]:
            d["features"] = [{"title": g["title"], "text": g["text"]} for g in d["gallery"] if g["title"] and g["text"]]
        d["specs"] = [s for s in d["specs"] if s["rows"]][:6]
        d["features"] = d["features"][:14]
        return d

    def tables(self, blocks):
        specs = []
        for b in iter_blocks(blocks):
            if b.get("type") != "table":
                continue
            rows = []
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", b.get("table", ""), flags=re.S):
                cells = [self.t(clean(c)) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S)]
                if any(cells):
                    rows.append(cells)
            if rows:
                specs.append({"title": self.t(clean(b.get("header", ""))), "rows": rows[:24]})
        return specs

    # ---------------------------------------------------------------- Ganze Fassung
    def build(self, de_data):
        nav_info = {}

        def walk(n):
            lp = self.local(n.get("href"))
            dp = self.loc2de.get(lp, "")
            if dp.startswith("/produkte"):
                nav_info.setdefault(dp, {"claim": self.t(clean(n.get("claim"))), "desc": self.t(clean(n.get("desc"))),
                                         "label": clean_name(self.t(n.get("label", "")))})
            for c in n.get("children", []):
                walk(c)
        for m in self.nav["main"]:
            walk(m)
        overview = self.page("/produkte")
        plist = next((b for b in overview["blocks"] if b["type"] == "productlist"), {"rows": [], "filters": {}})
        cat_text, list_text = {}, {}
        for row in plist.get("rows", []):
            for it in row.get("items", []):
                dp = self.loc2de.get(self.local(it.get("href")), "")
                if dp.count("/") == 2:
                    cat_text.setdefault(dp.split("/")[-1], self.t(clean(it.get("text"))))
                list_text.setdefault(dp, self.t(clean(it.get("text"))))
        # Werkzeugtypen: gleiche Reihenfolge wie im deutschen Filter
        de_plist = next(b for b in json.loads((SRC / "content" / "pages" / "produkte.json").read_text())["blocks"] if b["type"] == "productlist")
        de_tools = [o["label"] for o in de_plist["filters"].get("tool", [])]
        loc_tools = [self.t(o["label"]) for o in plist.get("filters", {}).get("tool", [])]
        tool_map = dict(zip(de_tools, loc_tools)) if len(de_tools) == len(loc_tools) else {}
        if tool_map:
            TOOL_MAPS.setdefault(self.lang, tool_map)
        else:   # Filterliste dieser Fassung unvollständig: Werkzeugtypen einer anderen Fassung derselben Sprache
            tool_map = TOOL_MAPS.get(self.lang, {})
        tool_name = lambda t: tool_map.get(t, t)
        sub_name = lambda s: web_i18n.T.get(self.lang, {}).get(s, s)

        products = []
        for p in de_data["products"]:
            info = self.extract(p["path"])
            fb = FALLBACK.get(p["id"], {}).get(self.lang)
            if info is None and fb:
                # Seite fehlt auf zoller.info in dieser Sprache: eigene Kurzinfo (tools/software_fallback.json), Bilder ohne Texte
                info = {"title": p["name"], "headline": p.get("headline", ""), "claim": fb["claim"], "intro": [fb["intro"]],
                        "sections": [], "highlights": fb["highlights"], "features": [], "gallery": [dict(g, title="", text="") for g in p.get("gallery", [])],
                        "header_img": None, "links": [], "shop": None, "specs": [], "models": [], "teaser": fb["teaser"]}
            elif info is None:
                print(f"   {self.dir}: keine Seite für {p['id']} ({p['path']}) – deutsche Texte bleiben")
                info = {"title": p["name"], "headline": p.get("headline", ""), "claim": p.get("claim", ""), "intro": p.get("intro", []),
                        "sections": [], "highlights": [], "features": [], "gallery": [], "header_img": None,
                        "links": [], "shop": None, "specs": [], "models": []}
            nv = nav_info.get(p["path"], {})
            name = p["name"]
            if p["kind"] == "package":
                name = info["title"].replace("Shopfloormanagement", "Shopfloor­management")
            elif nv.get("label") and p["id"] not in ("equick", "tooling"):
                name = nv["label"][len("Add-on "):] if nv["label"].startswith("Add-on ") else nv["label"]
            e = dict(p)
            e.update({
                "name": name, "badge": p.get("badge"), "sub": sub_name(p["sub"]),
                "url": self.web_de(p["path"]) or (EN_INT.web_de(p["path"]) if fb else None) or self.web_de("/unternehmen/kontakt") or self.base_url, "claim": nv.get("claim") or info["claim"] or info["headline"],
                "teaser": nv.get("desc") or list_text.get(p["path"], "") or info.get("teaser", ""), "headline": info["headline"], "intro": info["intro"],
                "sections": info["sections"], "highlights": info["highlights"][:4], "features": info["features"],
                "models": info["models"][:10], "specs": info["specs"], "gallery": info["gallery"], "links": info["links"],
                "shop": info["shop"], "header": info["header_img"] or p.get("header"),
                "tools": [tool_name(t) for t in p.get("tools", [])],
                "also": [{"cat": a["cat"], "sub": sub_name(a["sub"])} for a in p.get("also", [])],
            })
            if p["id"] == "tooling":
                e["teaser"] = cat_text.get("werkzeugaufnahmen", e["teaser"])
                e["claim"] = self.ui("Über 2500 Werkzeugaufnahmen")
                e["intro"] = [self.ui(p["intro"][0])] if p.get("intro") else e["intro"]
                e["highlights"] = [self.ui(h) for h in p.get("highlights", [])]
                e["links"] = [{"label": self.ui("Tooling-Shop auf myzoller.com"), "href": p["shop"]},
                              {"label": self.ui("Übersicht Werkzeugaufnahmen"), "href": e["url"]}]
            products.append(e)
        categories = []
        for c in de_data["categories"]:
            nv = nav_info.get(f"/produkte/{c['id']}", {})
            lp = self.de2loc.get(f"/produkte/{c['id']}")
            name = nv.get("label") or (clean_name(self.t(self.pages[lp]["title"])) if lp else c["name"])
            categories.append(dict(c, name=name, text=cat_text.get(c["id"]) or web_i18n.T.get(self.lang, {}).get(c["text"], c["text"]),
                                   url=self.web_de(f"/produkte/{c['id']}") or self.base_url, subs=[sub_name(s) for s in c["subs"]]))
        data = {"generated_from": f"zoller-webseite/content/sites/{self.loc['src']}", "site": self.base_url,
                "contact": self.web_de("/unternehmen/kontakt") or self.base_url,
                "categories": categories, "toolTypes": [tool_name(t) for t in de_data["toolTypes"]], "products": products}
        ar.patch(data, self.lang, self.loc["code"], ar.PLANER + self.dir + "/")   # AR-/3D-Ansicht (tools/ar.py)
        return data

    def index_html(self):
        s = (DOCS / "index.html").read_text(encoding="utf-8")
        s = s.replace('<html lang="de">', f'<html lang="{self.loc["code"]}">')
        s = re.sub(r'(href|src)="assets/', r'\1="../assets/', s)
        s = s.replace('"./assets/vendor/', '"../assets/vendor/')
        s = s.replace('"./assets/js/', '"../assets/js/')     # Import-Map (ar.js)
        s = s.replace("https://mzollercreations.github.io/zoller-webseite/produkte/", self.web_de("/produkte") or self.base_url)
        s = s.replace("https://mzollercreations.github.io/zoller-webseite/", self.base_url)
        texts = UI.get(self.lang, {})
        s = re.sub(r'\b(title|aria-label|placeholder|content)="([^"]+)"', lambda m: f'{m.group(1)}="{texts.get(m.group(2), m.group(2))}"', s)
        s = re.sub(r">([^<>]+)<", lambda m: ">" + texts.get(m.group(1), m.group(1)) + "<", s)
        js = {k: v for k, v in texts.items()}
        inject = f'<script>window.ZI18N={json.dumps(js, ensure_ascii=False)};window.ZBASE="../";</script>\n  '
        s = re.sub(r'<script type="module" src="\.\./assets/js/main\.js', lambda m: inject + m.group(0), s, count=1)
        return lang_menu(s, self.loc["code"], "../")


SITES = json.loads((SRC / "content" / "sites.json").read_text(encoding="utf-8"))
EN_INT = None
TOOL_MAPS = {}   # Sprache -> {deutscher Werkzeugtyp: Übersetzung}, aus der ersten Fassung mit vollständiger Filterliste
FALLBACK = json.loads((ROOT / "tools" / "software_fallback.json").read_text(encoding="utf-8"))


def lang_menu(page, code, base):
    """Länder-Knopf (Flagge der Fassung) und Länderliste in eine index.html einsetzen. base = Weg zur deutschen Fassung."""
    flag, items = "", []
    for site in SITES.values():
        for loc in site["locales"]:
            cur = loc["code"] == code
            svg = web_flags.FLAGS.get(site["flag"], "")
            flag = svg if cur else flag
            href = (base + (loc["code"].lower() + "/" if loc["src"] else "")) or "./"
            items.append(f'<a class="lang-site{" is-current" if cur else ""}" href="{href}" hreflang="{loc["code"]}" lang="{loc["lang"]}"'
                         f'{" aria-current=true" if cur else ""}>{svg}<span><b>{html.escape(loc["name"])}</b>'
                         f'<small>{html.escape(loc["label"])}</small></span></a>')
    page = re.sub(r"<!--lang-flag-->.*?<!--/lang-flag-->", lambda m: f"<!--lang-flag-->{flag}<!--/lang-flag-->", page, flags=re.S)
    return re.sub(r"<!--lang-sites-->.*?<!--/lang-sites-->", lambda m: f"<!--lang-sites-->{''.join(items)}<!--/lang-sites-->", page, flags=re.S)


def with_version(page):
    """?v=… an app.css und main.js hängen (Prüfsumme der Oberfläche), damit Browser keine alte Fassung aus dem Cache nehmen."""
    js = DOCS / "assets" / "js"
    ver = hashlib.sha1(b"".join(p.read_bytes() for p in (DOCS / "assets" / "css" / "app.css", js / "main.js", js / "world.js", js / "ar.js"))).hexdigest()[:10]
    page = re.sub(r'(assets/(?:css/app\.css|js/main\.js))(\?v=\w+)?"', rf'\1?v={ver}"', page)
    # Module, die main.js importiert (ar.js): Version über die Import-Map
    return re.sub(r'("\./assets/js/ar\.js": "\./assets/js/ar\.js)(\?v=\w+)?"', rf'\1?v={ver}"', page)


def main():
    sites = SITES
    de_data = json.loads((DOCS / "data" / "products.json").read_text(encoding="utf-8"))
    de_index = DOCS / "index.html"
    de_index.write_text(with_version(lang_menu(de_index.read_text(encoding="utf-8"), "de-DE", "")), encoding="utf-8")
    global EN_INT   # internationale englische Fassung: Ziel für Produkte ohne Seite in der Landessprache
    EN_INT = next(Locale(s_, l_) for s_ in sites.values() for l_ in s_["locales"] if l_["src"] == "en_DE" and not l_.get("overlay"))
    order = [(site, loc) for site in sites.values() for loc in site["locales"] if loc["src"]]
    for site, loc in order:   # Werkzeugtypen je Sprache vorab sammeln (TOOL_MAPS)
        Locale(site, loc).build(de_data)
    for site, loc in order:
        L = Locale(site, loc)
        out = DOCS / L.dir
        (out / "data").mkdir(parents=True, exist_ok=True)
        data = L.build(de_data)
        (out / "data" / "products.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        (out / "index.html").write_text(L.index_html(), encoding="utf-8")
        print(f"{L.dir}: {len(data['products'])} Produkte, {len(L.copied)} Bilder, Webseite {L.base_url}")


if __name__ == "__main__":
    main()
