#!/usr/bin/env python3
"""Stage 2: facility details from each Jalan hotel page. in: master_list.json  out: details.json"""
import sys, re, json, os
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from common import get, text

def between(t, a, b):
    i = t.find(a)
    if i < 0: return ''
    j = t.find(b, i + len(a))
    return t[i + len(a): j if j > 0 else i + 1500].strip()

def parse(jid):
    s = get(f'https://www.jalan.net/yad{jid}/', 'cp932')
    if not s: return jid, None
    t = text(s)
    d = {}
    m = re.search(r'\[(旅館|ホテル|ペンション|民宿|貸別荘|公共の宿|ロッジ|その他[^\]]*|[^\]]{1,10})\]' + r'[^\[]{0,80}じゃらんnet 他のホテル', t)
    d['type'] = m.group(1) if m else None
    m = re.search(r'総部屋数 (\d+)室 (\d+)室 (\d+)室 (\d+)室 (\d+)室', t)
    if m: d['rooms'] = dict(zip(['洋室', '和室', '和洋室', 'その他', '合計'], map(int, m.groups())))
    room_names = between(t, '部屋・部屋施設 情報の見方・説明', '部屋の写真')
    d['roomTypes'] = [x for x in re.findall(r'(【[^】]*】[^【]*)', room_names)][:6] or ([room_names[:200]] if room_names else [])
    d['roomTypes'] = [x.strip() for x in d['roomTypes']]
    d['roomEquip'] = between(t, '標準的な部屋設備', 'インターネット関連')[:200] or None
    d['wifi'] = re.split(r' 温泉・風呂| ・基本情報', between(t, 'インターネット関連', '・基本情報'))[0][:120] or None
    d['roomNote'] = between(t, '部屋補足 ', ' 標準的な部屋設備')[:200] or None
    bath = between(t, '温泉・風呂 情報の見方・説明', '風呂の写真')
    d['baths'] = bath[:300] or None
    m = re.search(r'温泉 (.{0,60}?) (?:温泉掛け流し|露天風呂)', t)
    d['onsen'] = m.group(1).strip() if m else None
    d['kakenagashi'] = '温泉掛け流し' in between(t, '風呂の写真', '露天風呂')
    m = re.search(r'露天風呂 (あり[^)）]*[)）]?|なし)', t); d['rotenburo'] = m.group(1) if m else None
    m = re.search(r'貸切風呂 (あり[^)）]*[)）]?|なし)', t); d['kashikiri'] = m.group(1) if m else None
    am = between(t, '施設の写真', '施設内容')
    d['amenities'] = re.findall(r'○ ([^○×]+?)(?= ○| ×| &nbsp;|$)', am)
    d['amenities'] = [a.strip('  ') for a in d['amenities'] if a.strip()]
    d['facilities'] = between(t, '施設内容', 'サービス&')[:300] or between(t, '施設内容', '現地で利用可能')[:300] or None
    d['services'] = between(t, '（手配含む）', '現地で利用可能')[:300] or None
    m = re.search(r'チェックイン時間 ([0-9:：～〜]+)', t); d['checkin'] = m.group(1) if m else None
    m = re.search(r'チェックアウト時間 ([～〜0-9:：]+)', t); d['checkout'] = m.group(1) if m else None
    m = re.search(r'パーキング (有り[^ ]*|無し[^ ]*|なし[^ ]*)', t); d['parking'] = m.group(1) if m else None
    acc = between(t, '大きな地図をみる アクセス ', ' パーキング')
    d['access'] = re.split(r' (?:仙台|東京|盛岡|大阪)： ', acc)[0][:200] or None
    d['notes'] = between(t, 'チェックアウト時間に関する補足', '・基本情報')[:300] or (re.search(r'補足 (■[^・]{0,300})', t) or [None,None])[1]
    sc = {}
    for k in ['部屋', '風呂', '料理（朝食）', '料理（夕食）', '接客・サービス', '清潔感']:
        m = re.search(re.escape(k) + r' ([\d.]+) ', between(t, 'クチコミ評価の見方・説明', '普通＝3.0'))
        if m: sc[k] = float(m.group(1))
    d['scores'] = sc
    m = re.search(r'<p class="[^"]*jlnpc-yado__subTitle[^"]*">([^<]+)', s)
    d['catch'] = between(t, 'すべての写真をみる ', ' 宿泊のご予約')[:250] or None
    sents = re.split(r'[。！!☆★♪■※◆●]| 施設の写真| 部屋の写真| 風呂の写真|【|】', t)
    kw = re.compile(r'お子様|お子さま|子供|子ども|こども|幼児|キッズ|ベビー|赤ちゃん|添い寝|添寝|ファミリー')
    kid = [x.strip() for x in sents if kw.search(x) and 6 <= len(x.strip()) <= 110 and '子供 0名' not in x and '○' not in x and '×' not in x]
    d['kidNotes'] = list(dict.fromkeys(kid))[:5]
    return jid, d

if __name__ == '__main__':
    ml = json.load(open(sys.argv[1]))
    with ThreadPoolExecutor(4) as ex:
        res = dict(ex.map(lambda h: parse(h['jalanId']), ml))
    json.dump(res, open(sys.argv[2], 'w'), ensure_ascii=False)
    print('done', sum(1 for v in res.values() if v), file=sys.stderr)
