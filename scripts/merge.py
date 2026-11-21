#!/usr/bin/env python3
"""Merge Jalan master + details + Rakuten list -> site/hotels.json"""
import sys, json, os, re, difflib
sys.path.insert(0, os.path.dirname(__file__))
from common import norm
ml, det, rk, outp = sys.argv[1:5]
ml = json.load(open(ml)); det = json.load(open(det)); rk = json.load(open(rk))
STRIP = ['温泉', 'ホテル', '旅館', 'hotel', 'the', 'inn']
def core(n):
    n = norm(n).replace('ヾ', 'ゞ').replace('ヽ', 'ゝ')
    n = re.sub(r'(岩手|宮城|盛岡|仙台|秋保|作並|花巻|松島|鳴子|つなぎ|繋|遠刈田|蔵王)', '', n)
    for w in STRIP: n = n.replace(w, '')
    return n
rk_by = {}
for r in rk:
    rk_by.setdefault((r['pref'], norm(r['name'])), r)
rk_core = {}
for r in rk:
    rk_core.setdefault((r['pref'], core(r['name'])), []).append(r)
used = set(); hotels = []
for h in ml:
    r = rk_by.get((h['pref'], norm(h['name'])))
    if not r:
        c = core(h['name'])
        cand = rk_core.get((h['pref'], c), []) if len(c) >= 3 else []
        if len(cand) == 1: r = cand[0]
    if not r:
        nh = norm(h['name'])
        cs = [x for x in rk if x['pref'] == h['pref'] and len(norm(x['name'])) >= 5 and (norm(x['name']) in nh or nh in norm(x['name']))]
        if len(cs) == 1: r = cs[0]
    if not r:
        nh = core(h['name']); best = None
        for x in rk:
            if x['pref'] != h['pref'] or x['rakutenNo'] in used: continue
            nx = core(x['name'])
            if min(len(nh), len(nx)) < 3: continue
            m = difflib.SequenceMatcher(None, nh, nx).find_longest_match(0, len(nh), 0, len(nx)).size
            sc = m / min(len(nh), len(nx))
            if m >= 4 and sc >= 0.75 and (best is None or sc > best[0]): best = (sc, x)
        if best: r = best[1]
    if r and r['rakutenNo'] in used: r = None
    d = det.get(h['jalanId']) or {}
    e = {'id': 'j' + h['jalanId'], 'jalanId': h['jalanId'], 'name': h['name'], 'pref': h['pref'], 'area': h['area'],
         'city': h.get('city'), 'address': h.get('address'), 'image': h.get('image'),
         'jr': h.get('jalanRating'), 'jn': h.get('jalanReviews')}
    for k in ['type', 'rooms', 'roomTypes', 'roomNote', 'roomEquip', 'wifi', 'baths', 'onsen', 'kakenagashi', 'rotenburo', 'kashikiri',
              'amenities', 'facilities', 'services', 'checkin', 'checkout', 'parking', 'access', 'notes', 'scores', 'catch', 'kidNotes']:
        if d.get(k) not in (None, '', [], {}): e[k] = d[k]
    if r:
        used.add(r['rakutenNo'])
        e.update({'rakutenNo': r['rakutenNo'], 'rr': r.get('rkRating'), 'rn': r.get('rkReviews'), 'rmin': r.get('rkMinPrice'),
                  'rfeat': r.get('features'), 'rspecial': r.get('special')})
        if not e.get('access') and r.get('access'): e['access'] = r['access']
    hotels.append(e)
AREA_KW = [('雫石', '雫石'), ('安比|八幡平|二戸|松尾|七時雨|岩手町|沼宮内|一戸|葛巻', '安比・八幡平・二戸'), ('盛岡|つなぎ|繋|鶯宿|滝沢|紫波|矢巾', '盛岡'),
 ('花巻|北上|遠野|志戸平|大沢温泉|夏油|台温泉|鉛温泉|新鉛|金ケ崎|西和賀|湯田|湯本', '花巻・北上・遠野'), ('奥州|水沢|江刺|平泉|一関|一ノ関|厳美渓|須川', '奥州・平泉・一関'),
 ('宮古|釜石|大船渡|久慈|陸前高田|大槌|山田|田野畑|普代|野田|岩泉|龍泉洞|三陸|洋野|住田', '三陸海岸'),
 ('秋保|作並|仙台|泉区|太白|青葉|宮城野|若林|名取|岩沼|富谷|利府', '仙台・秋保・作並'), ('松島|塩竈|塩釜|多賀城|七ヶ浜|東松島|奥松島', '松島・塩竈'),
 ('鳴子|大崎|古川|中山平|東鳴子|川渡|加美|色麻|涌谷|美里', '鳴子・大崎'), ('白石|蔵王|遠刈田|青根|鎌先|小原|大河原|角田|亘理|山元|村田|柴田|川崎|丸森|船岡', '白石・蔵王'),
 ('石巻|気仙沼|南三陸|女川|牡鹿|鮎川|唐桑', '石巻・気仙沼'), ('栗原|登米|くりこま|栗駒|若柳|佐沼|築館', '栗原・登米')]
def guess_area(r):
    s = (r.get('name') or '') + ' ' + (r.get('access') or '') + ' ' + (r.get('special') or '')
    for kw, a in AREA_KW:
        if re.search(kw, s): return a
    return 'その他'
for r in rk:
    if r['rakutenNo'] in used: continue
    hotels.append({'id': 'r' + r['rakutenNo'], 'rakutenNo': r['rakutenNo'], 'name': r['name'], 'pref': r['pref'], 'area': guess_area(r),
                   'rr': r.get('rkRating'), 'rn': r.get('rkReviews'), 'rmin': r.get('rkMinPrice'), 'rfeat': r.get('features'),
                   'rspecial': r.get('special'), 'access': r.get('access'), 'onsenFlag': r.get('onsen')})
json.dump(hotels, open(outp, 'w'), ensure_ascii=False, separators=(',', ':'))
print('hotels', len(hotels), 'matched', len(used), 'rakuten-only', len(rk) - len(used), file=sys.stderr)
