#!/usr/bin/env python3
"""All Rakuten Travel properties in Iwate & Miyagi (from listing pages' embedded JSON)."""
import sys, re, json, time, os
sys.path.insert(0, os.path.dirname(__file__))
from common import get
import html as H
PREFS = {'iwate': '岩手県', 'miyagi': '宮城県'}

def objs(s):
    res = []
    parts = re.split(r'<li id="(\d+)_list"', s)
    for k in range(1, len(parts), 2):
        no, b = parts[k], parts[k+1]
        g = lambda p: (re.search(p, b, re.S) or [None, None])[1]
        name = g(r'id="%s_link"[^>]*>([^<]+)<' % no)
        if not name: continue
        res.append({'rakutenNo': no, 'name': H.unescape(name).strip(),
                    'rkRating': float(g(r'<strong>([\d.]+)</strong>') or 0) or None,
                    'rkReviews': int(g(r'（(\d+)件）') or 0) or None,
                    'onsen': 'onsen-yado__tag' in b,
                    'special': H.unescape(g(r'class="htlSpecial">([^<]*)<') or '').strip() or None,
                    'access': H.unescape(g(r'class="htlAccess">\s*<span>([^<]*)<') or '').replace('アクセス　：', '').strip() or None,
                    'features': re.findall(r'<label>([^<]+)</label>', g(r'hotelInfo_features">(.*?)</div>') or ''),
                    'rkMinPrice': int((g(r'消費税込([\d,]+)円') or '0').replace(',', '')) or None})
    return res

out = {}
for slug, pname in PREFS.items():
    p = 1
    while p < 40:
        url = f'https://travel.rakuten.co.jp/yado/{slug}/' if p == 1 else f'https://search.travel.rakuten.co.jp/ds/yado/{slug}/p{p}'
        s = get(url)
        hs = objs(s); new = 0
        for h in hs:
            h['pref'] = pname
            if h['rakutenNo'] not in out: out[h['rakutenNo']] = h; new += 1
        print(slug, p, len(hs), new, file=sys.stderr)
        if not hs or not new: break
        p += 1; time.sleep(1)
json.dump(list(out.values()), sys.stdout, ensure_ascii=False)
