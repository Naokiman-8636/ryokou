#!/usr/bin/env python3
"""Stage 1: every property listed on Jalan in Iwate & Miyagi (dateless). -> JSON list on stdout"""
import sys, re, json, time
sys.path.insert(0, __import__('os').path.dirname(__file__))
from common import get, JALAN_AREAS, PREF
import html as H
out = {}
for pc, lrgs in JALAN_AREAS.items():
    for lrg, aname in lrgs.items():
        idx = 0
        while True:
            url = f'https://www.jalan.net/{pc}/{lrg}/?dateUndecided=1&adultNum=2&roomCount=1&screenId=UWW1402&activeSort=0&mode=1&idx={idx}'
            s = get(url, 'cp932')
            n = 0; new = 0
            # small-area name per cassette
            for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
                try: j = json.loads(blk, strict=False)
                except Exception: continue
                for h in (j if isinstance(j, list) else [j]):
                    if not (isinstance(h, dict) and h.get('@type') == 'Hotel'): continue
                    m = re.search(r'yad(\d+)', h.get('url', ''))
                    if not m: continue
                    n += 1
                    new += m.group(1) not in out
                    a = h.get('address') or {}; ar = h.get('aggregateRating') or {}
                    out.setdefault(m.group(1), {
                        'jalanId': m.group(1), 'name': H.unescape(h.get('name', '')).strip(), 'pref': PREF[pc], 'area': aname,
                        'city': a.get('addressLocality'), 'address': (a.get('addressLocality') or '') + (a.get('streetAddress') or ''),
                        'image': h.get('image'), 'jalanRating': float(ar['ratingValue']) if ar.get('ratingValue') else None,
                        'jalanReviews': int(ar['ratingCount']) if ar.get('ratingCount') else None})
            print(lrg, idx, n, file=sys.stderr)
            if n < 30 or new == 0 or idx > 900: break
            idx += 30
json.dump(list(out.values()), sys.stdout, ensure_ascii=False)
