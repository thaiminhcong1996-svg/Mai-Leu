# -*- coding: utf-8 -*-
"""Sinh website tĩnh từ thư mục content/. GitHub tự chạy file này sau mỗi lần lưu."""
import json, os, io, glob, html, urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(ROOT, "_site")
SITE = os.environ.get("SITE_URL", "").rstrip("/")
# GitHub Pages hay đặt web trong thư mục con (…github.io/mai-leu/),
# nên mọi đường dẫn phải gắn tiền tố này, nếu không sẽ 404 hết.
import urllib.parse as _up
BASE = (_up.urlparse(SITE).path or "/")
if not BASE.endswith("/"): BASE += "/"

rd = lambda p: json.load(io.open(p, encoding="utf-8"))
def wr(rel, s):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8").write(s)

DD = sorted([rd(p) for p in glob.glob(os.path.join(ROOT, "content/diem-den/*.json"))],
            key=lambda d: d["ten"])
SP = sorted([rd(p) for p in glob.glob(os.path.join(ROOT, "content/san-pham/*.json"))],
            key=lambda p: p["ma"])
SHOP = rd(os.path.join(ROOT, "content/shop.json"))
DD = [d for d in DD if d.get("hien", True)]
SP = [p for p in SP if p.get("hien", True)]

# đặc điểm địa hình, dùng để gợi ý đồ
LEECH = {"bach-ma", "hang-dong-tu-lan", "ta-nang-phan-dung", "nam-cat-tien"}
SUN = {"ban-dao-son-tra","cu-lao-cham","nui-chua","bai-xep-phu-yen","dao-binh-hung",
 "chu-dang-ya","nui-ba-den","ho-dau-tieng","con-dao","nui-cam","nui-co-to",
 "vuon-quoc-gia-tram-chim","quan-dao-nam-du","hon-son","dat-mui-ca-mau",
 "binh-chau-ho-coc","ho-tram","nganh-tam-tan-lagi","mui-ke-ga","bau-trang",
 "bai-da-co-thach","cu-lao-cau","dao-phu-quy","binh-lap","vinh-hy-hang-rai",
 "mui-dinh","dao-binh-ba"}
SEA = {"vinh-lan-ha-cat-ba","cu-lao-cham","bai-xep-phu-yen","dao-binh-hung","con-dao",
 "rung-sac-can-gio","quan-dao-nam-du","hon-son","dat-mui-ca-mau","binh-chau-ho-coc",
 "ho-tram","nganh-tam-tan-lagi","mui-ke-ga","bai-da-co-thach","cu-lao-cau",
 "dao-phu-quy","binh-lap","vinh-hy-hang-rai","mui-dinh","dao-binh-ba"}

def gear_for(d):
    t, alt, ma = d["loai"], d["do_cao_m"], d["ma"]
    g = set()
    if t == "Trekking":  g |= {4, 7, 10, 8, 6, 11}
    if t == "Hiking":    g |= {7, 8, 6}
    if t == "Camping":   g |= {1, 9, 5, 6, 16}
    if t == "Glamping":  g |= {16, 5, 6, 3, 1}
    if t in ("Trekking", "Camping"):
        g |= {1, 9, 5}; g.add(2 if alt >= 1500 else 3)
    if alt >= 2000:      g |= {2, 14}; g.discard(3)
    if alt < 400 and d["vung"] in ("Miền Tây", "Miền Nam"): g.add(12)
    if ma in SUN:        g.add(15)
    if ma in LEECH:      g.add(13)
    if t == "Camping" and alt > 1200: g.discard(16)
    return sorted(g)

pnum = lambda ma: int("".join(c for c in ma if c.isdigit()) or 0)
byid = {pnum(p["ma"]): p for p in SP}
vnd  = lambda n: "{:,}".format(int(n or 0)).replace(",", ".") + "\u20ab"
E    = lambda s: html.escape(str(s or ""), quote=True)

# ── dữ liệu cho trang chủ ──
wr("data.json", json.dumps({"diem_den": DD, "san_pham": SP, "shop": SHOP},
                           ensure_ascii=False))

# ── trang chủ ──
def rebase(s):
    return (s.replace('"/data.json"', '"%sdata.json"' % BASE)
             .replace("'/data.json'", "'%sdata.json'" % BASE)
             .replace('/static/', BASE + 'static/')
             .replace('/diem-den/', BASE + 'diem-den/')
             .replace('href="/"', 'href="%s"' % BASE)
             .replace("href='/'", "href='%s'" % BASE))

wr("index.html", rebase(io.open(os.path.join(ROOT, "templates/home.html"), encoding="utf-8").read()))

# ── từng điểm đến ──
TPL = io.open(os.path.join(ROOT, "templates/diem-den.html"), encoding="utf-8").read()
Q6 = [("q1_so_lan_di", "Anh \u0111\u00e3 \u0111i m\u1ea5y l\u1ea7n"),
      ("q2_xuat_phat_gui_xe", "Xu\u1ea5t ph\u00e1t v\u00e0 g\u1eedi xe \u1edf \u0111\u00e2u"),
      ("q3_nuoc", "N\u01b0\u1edbc l\u1ea5y \u1edf \u0111\u00e2u"),
      ("q4_ngu_lanh_gio", "Ng\u1ee7 \u1edf \u0111\u00e2u, l\u1ea1nh v\u00e0 gi\u00f3 c\u1ee1 n\u00e0o"),
      ("q5_ai_khong_nen_di", "Ai kh\u00f4ng n\u00ean \u0111i cung n\u00e0y"),
      ("q6_thieu_thua", "Hay mang thi\u1ebfu v\u00e0 hay mang th\u1eeba")]

for d in DD:
    ma, ten = d["ma"], d["ten"]
    url = "%s/diem-den/%s/" % (SITE, ma) if SITE else "/diem-den/%s/" % ma
    months = "".join('<span class="%s">%d</span>' % ("go" if i in d["thang_di_duoc"] else "", i)
                     for i in range(1, 13))
    thangs = ", ".join(str(i) for i in d["thang_di_duoc"])
    desc = "%s (%s) — %s. Đi được tháng %s. Danh sách đồ nên mang." % (
        ten, d["tinh"], d["loai"].lower(), thangs)
    desc = desc[:180]

    chips = "".join('<span class="chip f">%s</span>' % E(d["loai"])
                    + '<span class="chip">%d m</span>' % d["do_cao_m"]
                    + '<span class="chip">Độ khó: %s</span>' % E(d["do_kho"])
                    + '<span class="chip">%d tháng đi được</span>' % len(d["thang_di_duoc"]))

    anh = ""
    if d.get("anh"):
        anh = '<section class="shots">%s</section>' % "".join(
            '<div><img src="%s" alt="%s" loading="lazy"></div>' % (E(a), E(ten)) for a in d["anh"])

    got = [(k, q) for k, q in Q6 if (d.get(k) or "").strip()]
    if got:
        kn = ('<section><h2>Kinh nghiệm đi thật</h2>'
              '<span class="by">%s ghi lại · cập nhật khi có chuyến mới</span>' % E(SHOP["chu"])
              + "".join('<div class="qa%s"><span class="q">%s</span><p class="a">%s</p></div>'
                        % (" warn" if k == "q5_ai_khong_nen_di" else "", E(q), E(d[k])) for k, q in got)
              + "</section>")
    else:
        kn = ('<section><h2>Kinh nghiệm đi thật</h2><p style="color:var(--muted);max-width:60ch">'
              'Cung này %s chưa viết lại. Nếu anh cần tư vấn gấp, nhắn Zalo — '
              'shop trả lời trong ngày.</p></section>' % E(SHOP["chu"]))

    cards = ""
    for i in gear_for(d):
        p = byid.get(i)
        if not p: continue
        im = ('<img src="%s" alt="%s" loading="lazy">' % (E(p["anh"][0]), E(p["ten"]))
              if p.get("anh") else "<span>chưa có ảnh</span>")
        cards += ('<div class="cd"><div class="im">%s</div><h3>%s</h3><p>%s</p>'
                  '<span class="pr">%s%s</span></div>') % (
            im, E(p["ten"]), E(p["mo_ta"]), vnd(p["gia_ban"]),
            '<span class="rt">thuê %s/ngày</span>' % vnd(p["gia_thue_ngay"]) if p["gia_thue_ngay"] else "")

    near = "".join('<a href="/diem-den/%s/">%s</a>' % (o["ma"], E(o["ten"]))
                   for o in DD if o["vung"] == d["vung"] and o["ma"] != ma)[:4000]

    zmsg = "Chào shop, mình định đi %s (%s). Cho mình hỏi nên chuẩn bị gì ạ?" % (ten, d["tinh"])
    zalo = "https://zalo.me/%s?text=%s" % (SHOP["zalo_1"], urllib.parse.quote(zmsg))
    maps = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(
        "%s, %s, Việt Nam" % (ten, d["tinh"]))

    ld = json.dumps({"@context": "https://schema.org", "@type": "TouristAttraction",
        "name": ten, "description": d.get("gioi_thieu", ""),
        "address": {"@type": "PostalAddress", "addressRegion": d["tinh"], "addressCountry": "VN"}},
        ensure_ascii=False)

    ogimg = ('<meta property="og:image" content="%s%s">' % (SITE, d["anh"][0])
             if d.get("anh") and SITE else "")

    page = TPL
    for k, v in [("__TITLE__", "%s — đi tháng mấy, mang gì | MÁI LỀU" % ten),
                 ("__DESC__", desc), ("__URL__", url), ("__OGIMG__", ogimg),
                 ("__JSONLD__", ld), ("__VUNG__", E(d["vung"])), ("__TINH__", E(d["tinh"])),
                 ("__TEN__", E(ten)), ("__CHIPS__", chips),
                 ("__GIOITHIEU__", E(d.get("gioi_thieu", ""))), ("__MAPS__", maps),
                 ("__ANH__", anh), ("__MONTHS__", months), ("__KINHNGHIEM__", kn),
                 ("__GEAR__", cards), ("__ZALO__", zalo), ("__NEAR__", near)]:
        page = page.replace(k, v)
    wr("diem-den/%s/index.html" % ma, rebase(page))

# ── ảnh và css đi kèm ──
import shutil
for src, dst in [("static", "static")]:
    s = os.path.join(ROOT, src)
    if os.path.isdir(s):
        shutil.copytree(s, os.path.join(OUT, dst), dirs_exist_ok=True)

# ── sitemap + robots ──
urls = [SITE + "/"] + ["%s/diem-den/%s/" % (SITE, d["ma"]) for d in DD]
wr("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
   '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
   + "".join("  <url><loc>%s</loc></url>\n" % u for u in urls) + "</urlset>\n")
wr("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE)
wr(".nojekyll", "")

print("Đã sinh %d trang điểm đến + trang chủ" % len(DD))
