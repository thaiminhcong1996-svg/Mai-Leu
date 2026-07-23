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

DD = sorted([rd(p) for p in glob.glob(os.path.join(ROOT, "diem-den/*.json"))],
            key=lambda d: d["ten"])
SP = sorted([rd(p) for p in glob.glob(os.path.join(ROOT, "san-pham/*.json"))],
            key=lambda p: p["ma"])
SHOP = rd(os.path.join(ROOT, "shop.json"))
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


# ══════════ Ô TÌM KIẾM (chèn vào mọi trang) ══════════
SEARCH_CSS = """
<style>
.tim{position:relative;flex:1;max-width:250px;margin-left:auto}
.tim input{width:100%;border:1px solid var(--line);background:#fff;padding:8px 12px;
 font-size:13.5px;border-radius:2px;font-family:var(--fb);font-weight:300;color:var(--pine)}
.tim input:focus{border-color:var(--pine);outline:none}
.tim-kq{position:absolute;top:calc(100% + 7px);left:0;right:0;min-width:260px;background:#fff;
 border:1px solid var(--line);max-height:62vh;overflow-y:auto;z-index:90;
 box-shadow:0 14px 34px rgba(16,30,27,.16)}
.tim-kq a{display:block;padding:10px 13px;border-bottom:1px solid var(--line)}
.tim-kq a:last-child{border-bottom:none}
.tim-kq a:hover{background:var(--paper)}
.tim-kq .t{font-size:13.5px;font-weight:500;display:block;line-height:1.3;color:var(--pine)}
.tim-kq .s{font-size:11px;color:var(--muted);font-family:var(--fm)}
.tim-kq .non{padding:18px 13px;font-size:13px;color:var(--muted)}
.tim-kq .nh{font-family:var(--fm);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;
 color:var(--muted);padding:9px 13px 5px;background:var(--paper)}
@media(max-width:560px){.tim{max-width:130px}.tim-kq{right:auto;width:78vw}}
</style>
"""

SEARCH_HTML = """<div class="tim">
  <input id="tim-o" type="search" placeholder="T\u00ecm cung \u0111\u01b0\u1eddng ho\u1eb7c m\u00f3n \u0111\u1ed3\u2026" autocomplete="off" aria-label="T\u00ecm ki\u1ebfm">
  <div class="tim-kq" id="tim-kq" hidden></div>
</div>"""

SEARCH_JS = """
<script>
(function(){
  var o=document.getElementById('tim-o'), k=document.getElementById('tim-kq'), DATA=null;
  if(!o||!k) return;
  var B='__BASE__';
  function bo(s){return String(s||'').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'')
    .replace(/\\u0111/g,'d').replace(/\\u0110/g,'D').toLowerCase();}
  function tien(n){return (n||0).toLocaleString('vi-VN')+'\\u20ab';}
  function load(){
    if(DATA) return Promise.resolve(DATA);
    return fetch(B+'data.json').then(function(r){return r.json();})
      .then(function(j){DATA=j;return j;})
      .catch(function(){DATA={diem_den:[],san_pham:[]};return DATA;});
  }
  o.addEventListener('focus',load);
  function ve(){
    var q=bo(o.value.trim());
    if(!q){k.hidden=true;k.innerHTML='';return;}
    load().then(function(d){
      var dd=(d.diem_den||[]).filter(function(x){
        return bo(x.ten+' '+x.tinh+' '+x.vung+' '+x.loai).indexOf(q)>-1;}).slice(0,7);
      var sp=(d.san_pham||[]).filter(function(p){
        return bo(p.ten+' '+p.nhom+' '+(p.ly_do||'')).indexOf(q)>-1;}).slice(0,5);
      var h='';
      if(dd.length){h+='<div class="nh">\\u0110i\\u1ec3m \\u0111\\u1ebfn</div>'+dd.map(function(x){
        return '<a href="'+B+'diem-den/'+x.ma+'/"><span class="t">'+x.ten+'</span>'+
        '<span class="s">'+x.tinh+' \\u00b7 '+x.loai+' \\u00b7 '+x.do_cao_m+'m</span></a>';}).join('');}
      if(sp.length){h+='<div class="nh">S\\u1ea3n ph\\u1ea9m</div>'+sp.map(function(p){
        return '<a href="'+B+'san-pham/'+String(p.ma).toLowerCase()+'/"><span class="t">'+p.ten+'</span>'+
        '<span class="s">'+p.nhom+' \\u00b7 '+tien(p.gia_ban)+
        (p.gia_thue_ngay?' \\u00b7 thu\\u00ea '+tien(p.gia_thue_ngay)+'/ng\\u00e0y':'')+'</span></a>';}).join('');}
      if(!h) h='<div class="non">Kh\\u00f4ng t\\u00ecm th\\u1ea5y g\\u00ec kh\\u1edbp v\\u1edbi t\\u1eeb n\\u00e0y.</div>';
      k.innerHTML=h;k.hidden=false;
    });
  }
  o.addEventListener('input',ve);
  o.addEventListener('keydown',function(e){if(e.key==='Escape'){k.hidden=true;o.blur();}});
  document.addEventListener('click',function(e){
    if(!k.contains(e.target)&&e.target!==o) k.hidden=true;});
})();
</script>
"""

def gan_tim_sp(html):
    html = html.replace("</head>", SEARCH_CSS + "</head>", 1)
    html = html.replace("__TIM__", SEARCH_HTML, 1)
    html = html.replace("</body>", SEARCH_JS + "</body>", 1)
    return html

def gan_tim(html, home=False):
    """Chèn ô tìm kiếm + link Sản phẩm vào thanh điều hướng."""
    html = html.replace("</head>", SEARCH_CSS + "</head>", 1)
    if home:
        old = '<div class="nav-links">'
        new = SEARCH_HTML + '<div class="nav-links" style="margin-left:20px">'
        html = html.replace(old, new, 1)
        html = html.replace('<a href="#lienhe">Li\u00ean h\u1ec7</a>',
                            '<a href="/san-pham/">S\u1ea3n ph\u1ea9m</a><a href="#lienhe">Li\u00ean h\u1ec7</a>', 1)
    else:
        old = '<a class="nb" href="/">'
        new = SEARCH_HTML + '<a class="nb" href="/san-pham/">S\u1ea3n ph\u1ea9m</a><a class="nb" style="margin-left:16px" href="/">'
        html = html.replace(old, new, 1)
    html = html.replace("</body>", SEARCH_JS + "</body>", 1)
    return html


# ── dữ liệu cho trang chủ ──
wr("data.json", json.dumps({"diem_den": DD, "san_pham": SP, "shop": SHOP},
                           ensure_ascii=False))

# ── trang chủ ──
def rebase(s):
    return (s.replace("__BASE__", BASE)
             .replace('"/data.json"', '"%sdata.json"' % BASE)
             .replace("'/data.json'", "'%sdata.json'" % BASE)
             .replace('/static/', BASE + 'static/')
             .replace('/diem-den/', BASE + 'diem-den/')
             .replace('/san-pham/', BASE + 'san-pham/')
             .replace('href="/"', 'href="%s"' % BASE)
             .replace("href='/'", "href='%s'" % BASE))

wr("index.html", rebase(gan_tim(io.open(os.path.join(ROOT, "templates/home.html"), encoding="utf-8").read(), home=True)))

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
    wr("diem-den/%s/index.html" % ma, rebase(gan_tim(page)))


# ══════════ TRANG SẢN PHẨM ══════════
# đảo ngược: mỗi món được gợi ý cho những cung nào
DUNG_CHO = {}
for d in DD:
    for i in gear_for(d):
        DUNG_CHO.setdefault(i, []).append(d)

NAV_SP = """<nav class="nav"><div class="wrap nav-in">
  <a href="/" class="brand"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"><path d="M12 3 2 21h20L12 3zM12 3v18M8 21l4-7 4 7"/></svg>M\u00c1I L\u1ec0U<span class="sig">Th\u00e1i Minh C\u00f4ng</span></a>
  __TIM__<a class="nb" href="/san-pham/">S\u1ea3n ph\u1ea9m</a><a class="nb" style="margin-left:16px" href="/">\u2190 L\u1ecbch m\u00f9a</a>
</div></nav>"""

FOOT_SP = """<footer class="foot"><div class="wrap foot-in">
  <span class="brand">M\u00c1I L\u1ec0U<span class="sig">Th\u00e1i Minh C\u00f4ng</span></span>
  <span>%s \u00b7 %s</span>
  <span><a href="tel:%s">%s</a></span>
</div></footer>""" % (E(SHOP["dia_chi"]), E(SHOP["gio"]), SHOP["zalo_1"], SHOP["zalo_1"])

def khung(title, desc, url, than, extra_css=""):
    return """<!DOCTYPE html>
<html lang="vi"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;900&family=Be+Vietnam+Pro:wght@300;400;500;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/trang.css">%s
</head><body>%s%s%s</body></html>""" % (title, desc, url, title, desc, extra_css, NAV_SP, than, FOOT_SP)

# ---- trang liệt kê tất cả ----
nhoms = []
for p in SP:
    if p["nhom"] not in nhoms: nhoms.append(p["nhom"])

loc = '<button class="fl on" data-n="">T\u1ea5t c\u1ea3</button>' + "".join(
    '<button class="fl" data-n="%s">%s</button>' % (E(n), E(n)) for n in nhoms)

the = ""
for p in SP:
    ma = p["ma"].lower()
    im = ('<img src="%s" alt="%s" loading="lazy">' % (E(p["anh"][0]), E(p["ten"]))
          if p.get("anh") else "<span>ch\u01b0a c\u00f3 \u1ea3nh</span>")
    dc = len(DUNG_CHO.get(pnum(p["ma"]), []))
    the += """<a class="cd sp" data-n="%s" href="/san-pham/%s/">
      <div class="im">%s</div><h3>%s</h3><p>%s</p>
      <span class="pr">%s%s</span>
      <span class="dc">%d cung d\u00f9ng t\u1edbi</span></a>""" % (
        E(p["nhom"]), ma, im, E(p["ten"]), E(p["mo_ta"]), vnd(p["gia_ban"]),
        '<span class="rt">thu\u00ea %s/ng\u00e0y</span>' % vnd(p["gia_thue_ngay"]) if p["gia_thue_ngay"] else "",
        dc)

than = """<header class="hero"><div class="wrap">
  <span class="eyebrow">C\u1eeda h\u00e0ng</span>
  <h1>%d m\u00f3n \u0111\u1ee7 cho<br>m\u1ecdi cung \u0111\u01b0\u1eddng</h1>
  <p class="lead">M\u1ed7i m\u00f3n \u1edf \u0111\u00e2y \u0111\u1ec1u \u0111\u01b0\u1ee3c ch\u1ecdn cho m\u1ed9t vi\u1ec7c c\u1ee5 th\u1ec3.
  Ph\u1ea7n l\u1edbn thu\u00ea \u0111\u01b0\u1ee3c theo ng\u00e0y \u2014 \u0111i l\u1ea7n \u0111\u1ea7u th\u00ec thu\u00ea r\u1ebb h\u01a1n mua nhi\u1ec1u.</p>
</div></header>
<main class="wrap body">
  <div class="locs">%s</div>
  <div class="cards" id="ds">%s</div>
</main>
<script>
document.querySelectorAll('.fl').forEach(function(b){
  b.addEventListener('click',function(){
    document.querySelectorAll('.fl').forEach(function(x){x.classList.remove('on');});
    b.classList.add('on');
    var n=b.dataset.n;
    document.querySelectorAll('.cd.sp').forEach(function(c){
      c.style.display=(!n||c.dataset.n===n)?'':'none';});
  });
});
</script>""" % (len(SP), loc, the)

CSS_SP = """<style>
.locs{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:20px}
.fl{border:1px solid var(--line);background:#fff;padding:8px 14px;font-size:13px;cursor:pointer;
 font-family:var(--fb);color:var(--pine)}
.fl:hover{border-color:var(--pine)}
.fl.on{background:var(--pine);color:var(--paper);border-color:var(--pine)}
.cd.sp{min-height:0}
.cd .dc{font-family:var(--fm);font-size:10.5px;color:var(--muted);margin-top:6px;display:block}
.spec2{border-top:1px solid var(--line);font-size:14px;max-width:520px}
.spec2 div{display:flex;justify-content:space-between;gap:20px;padding:11px 0;border-bottom:1px solid var(--line)}
.spec2 dt{color:var(--muted)}
.spec2 dd{font-family:var(--fm);font-size:13px;text-align:right}
.gia{display:flex;flex-wrap:wrap;gap:26px;margin-top:18px}
.gia div{border-left:2px solid var(--lime);padding-left:13px}
.gia .lb{font-family:var(--fm);font-size:10px;letter-spacing:.14em;text-transform:uppercase;
 color:rgba(220,227,222,.55);display:block}
.gia .vl{font-family:var(--fm);font-size:22px;font-weight:600;color:var(--paper)}
</style>"""

wr("san-pham/index.html", rebase(gan_tim_sp(khung(
    "T\u1ea5t c\u1ea3 s\u1ea3n ph\u1ea9m \u2014 mua v\u00e0 thu\u00ea \u0111\u1ed3 trek, c\u1eafm tr\u1ea1i | M\u00c1I L\u1ec0U",
    "%d m\u00f3n \u0111\u1ed3 trekking v\u00e0 c\u1eafm tr\u1ea1i, mua ho\u1eb7c thu\u00ea theo ng\u00e0y. Giao to\u00e0n qu\u1ed1c." % len(SP),
    (SITE + "/san-pham/") if SITE else "/san-pham/", than, CSS_SP))))

# ---- trang riêng từng món ----
for p in SP:
    ma = p["ma"].lower()
    i = pnum(p["ma"])
    cungs = DUNG_CHO.get(i, [])
    anh = ""
    if p.get("anh"):
        anh = '<section class="shots">%s</section>' % "".join(
            '<div><img src="%s" alt="%s" loading="lazy"></div>' % (E(a), E(p["ten"])) for a in p["anh"])
    spec = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (E(t.split(":")[0].strip()),
                   E(":".join(t.split(":")[1:]).strip())) for t in p.get("thong_so", []) if ":" in t)
    ds = "".join('<a href="/diem-den/%s/">%s</a>' % (c["ma"], E(c["ten"])) for c in cungs[:14])
    them = "" if len(cungs) <= 14 else '<p style="color:var(--muted);font-size:13px;margin-top:9px">v\u00e0 %d cung kh\u00e1c</p>' % (len(cungs) - 14)
    zm = "Ch\u00e0o shop, m\u00ecnh mu\u1ed1n h\u1ecfi v\u1ec1 %s ." % p["ten"]
    zl = "https://zalo.me/%s?text=%s" % (SHOP["zalo_1"], urllib.parse.quote(zm))
    if p["gia_thue_ngay"]:
        zt = "Ch\u00e0o shop, m\u00ecnh mu\u1ed1n thu\u00ea %s (%s/ng\u00e0y). Cho m\u00ecnh h\u1ecfi th\u1ee7 t\u1ee5c c\u1ecdc v\u1edbi \u1ea1." % (p["ten"], vnd(p["gia_thue_ngay"]))
        nut_thue = '<a class="btn out" target="_blank" rel="noopener" href="https://zalo.me/%s?text=%s">Thu\u00ea m\u00f3n n\u00e0y</a>' % (
            SHOP["zalo_2"], urllib.parse.quote(zt))
    else:
        nut_thue = ""

    than = """<header class="hero"><div class="wrap">
  <span class="eyebrow">%s \u00b7 %s</span>
  <h1>%s</h1>
  <p class="lead">%s</p>
  <div class="gia"><div><span class="lb">Gi\u00e1 b\u00e1n</span><span class="vl">%s</span></div>%s</div>
</div></header>
<main class="wrap body">
  %s
  %s
  <section><h2>D\u00f9ng cho nh\u1eefng cung n\u00e0o</h2>
    <p style="color:var(--muted);max-width:60ch;margin-bottom:14px">M\u00f3n n\u00e0y n\u1eb1m trong danh s\u00e1ch \u0111\u1ed3 g\u1ee3i \u00fd c\u1ee7a %d cung.</p>
    <div class="nl">%s</div>%s</section>
  <section><div class="cta">
    <a class="btn dark" target="_blank" rel="noopener" href="%s">H\u1ecfi mua qua Zalo</a>%s
    <a class="btn out" href="/san-pham/">\u2190 T\u1ea5t c\u1ea3 s\u1ea3n ph\u1ea9m</a>
  </div></section>
</main>""" % (
        E(p["nhom"]), E(p["ly_do"]), E(p["ten"]), E(p["mo_ta"]), vnd(p["gia_ban"]),
        '<div><span class="lb">Thu\u00ea theo ng\u00e0y</span><span class="vl">%s</span></div>' % vnd(p["gia_thue_ngay"]) if p["gia_thue_ngay"] else "",
        anh,
        '<section><h2>Th\u00f4ng s\u1ed1</h2><dl class="spec2">%s</dl></section>' % spec if spec else "",
        len(cungs), ds, them, zl, nut_thue)

    desc = "%s \u2014 %s%s. %s" % (p["ten"], vnd(p["gia_ban"]),
            ", thu\u00ea %s/ng\u00e0y" % vnd(p["gia_thue_ngay"]) if p["gia_thue_ngay"] else "", p["mo_ta"])
    wr("san-pham/%s/index.html" % ma, rebase(gan_tim_sp(khung(
        "%s \u2014 mua v\u00e0 thu\u00ea | M\u00c1I L\u1ec0U" % p["ten"], desc[:180],
        (SITE + "/san-pham/%s/" % ma) if SITE else "/san-pham/%s/" % ma, than, CSS_SP))))


# ── ảnh và css đi kèm ──
import shutil
for src, dst in [("static", "static"), ("admin", "admin")]:
    s = os.path.join(ROOT, src)
    if os.path.isdir(s):
        shutil.copytree(s, os.path.join(OUT, dst), dirs_exist_ok=True)

# ── sitemap + robots ──
urls = ([SITE + "/", SITE + "/san-pham/"]
        + ["%s/diem-den/%s/" % (SITE, d["ma"]) for d in DD]
        + ["%s/san-pham/%s/" % (SITE, p["ma"].lower()) for p in SP])
wr("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
   '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
   + "".join("  <url><loc>%s</loc></url>\n" % u for u in urls) + "</urlset>\n")
wr("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE)
wr(".nojekyll", "")

print("Đã sinh %d trang điểm đến + trang chủ" % len(DD))
