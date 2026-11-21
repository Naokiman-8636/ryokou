#!/usr/bin/env python3
"""Per-date availability for 2 adults + 1 toddler from Jalan area search (all of Iwate & Miyagi).
Usage: jalan_date.py YYYY-MM-DD [nights] > avail.json
Runs two party modes:
  toddler : 大人2 + 幼児(食事・布団あり) 1   (child3Num=1)
  soine   : 大人2のみ (3歳児は添い寝・食事なしで無料/現地精算の宿向け)"""
import sys, re, json, time, os
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from common import get, text, JALAN_AREAS
MODES = {'toddler': '&child3Num=1', 'soine': ''}
MEALS = ['朝・夕', '朝のみ', '夕のみ', '食事なし']

def plans(block):
    rows = []
    for seg in block.split('class="p-searchResultItem__planNameCell"')[1:]:
        g = lambda p: (re.search(p, seg, re.S) or [None, None])[1]
        name = g(r'jsc-planDetailLink"[^>]*>\s*([^<]+?)\s*<')
        href = g(r'href="(/uw/uwp3200/uww3201init\.do\?[^"]+)"')
        tot = g(r'class="p-searchResultItem__total">\s*(?:<[^>]+>\s*)*?<em>([\d,]+)</em>')
        rest = text(g(r'class="p-searchResultItem__restCell">(.*?)</td>') or '')
        rt = g(r'c-label--room[^>]*>([^<]+)<')
        meal = g(r'c-label--meal[^>]*>([^<]+)<')
        if tot:
            rows.append({'plan': (name or '').strip(), 'room': rt, 'meal': meal,
                         'total': int(tot.replace(',', '')), 'rest': rest or None,
                         'url': 'https://www.jalan.net' + href.replace('&amp;', '&') if href else None})
    return rows

def area(args):
    pc, lrg, mode, y, m, d, n = args
    res = []; idx = 0; seen = set()
    while idx <= 300:
        url = (f'https://www.jalan.net/{pc}/{lrg}/?stayYear={y}&stayMonth={m}&stayDay={d}&stayCount={n}'
               f'&roomCount=1&adultNum=2{MODES[mode]}&dateUndecided=&mode=1&screenId=UWW1402&activeSort=0&idx={idx}')
        s = get(url, 'cp932', cache=False)
        pr = {}
        for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try: j = json.loads(blk, strict=False)
            except Exception: continue
            for h in (j if isinstance(j, list) else [j]):
                if isinstance(h, dict) and h.get('@type') == 'Hotel':
                    mm = re.search(r'yad(\d+)', h.get('url', '')); v = (h.get('priceRange') or '').replace(',', '').rstrip('-')
                    if mm and v.isdigit(): pr[mm.group(1)] = int(v)
        parts = re.split(r'<li id="yadNo(\d+)" class="p-yadoCassette', s)
        new = 0
        for k in range(1, len(parts), 2):
            jid = parts[k]
            if jid in seen: continue
            seen.add(jid); new += 1
            b = parts[k + 1]
            ps = plans(b)
            res.append({'jalanId': jid, 'minTotal': pr.get(jid) or (min(p['total'] for p in ps) if ps else None),
                        'plans': ps[:3]})
        if new < 30: break
        idx += 30
    return mode, res

if __name__ == '__main__':
    date = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    y, m, d = date.split('-')
    jobs = [(pc, lrg, mode, y, int(m), int(d), n) for pc, l in JALAN_AREAS.items() for lrg in l for mode in MODES]
    out = {'date': date, 'nights': n, 'fetchedAt': time.strftime('%Y-%m-%dT%H:%M:%S+09:00', time.gmtime(time.time() + 9 * 3600)),
           'source': 'jalan', 'modes': {k: {} for k in MODES}}
    with ThreadPoolExecutor(4) as ex:
        for mode, res in ex.map(area, jobs):
            for r in res: out['modes'][mode][r.pop('jalanId')] = r
    json.dump(out, sys.stdout, ensure_ascii=False)
    print({k: len(v) for k, v in out['modes'].items()}, file=sys.stderr)
