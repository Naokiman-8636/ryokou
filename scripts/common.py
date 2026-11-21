import subprocess, time, os, hashlib, re, html, unicodedata
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
CACHE = os.environ.get('RYOKOU_CACHE', '/tmp/ryokou_cache')
os.makedirs(CACHE, exist_ok=True)

def get(url, enc='utf-8', cache=True, minlen=3000):
    p = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest())
    if cache and os.path.exists(p):
        return open(p, 'rb').read().decode(enc, 'ignore')
    for i in range(3):
        r = subprocess.run(['curl', '-sL', '-A', UA, '-m', '60', url], capture_output=True)
        if r.returncode == 0 and len(r.stdout) > minlen:
            if cache: open(p, 'wb').write(r.stdout)
            return r.stdout.decode(enc, 'ignore')
        time.sleep(3 + i * 3)
    return ''

def text(s):
    s = re.sub(r'<script.*?</script>|<style.*?</style>', '', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()

def norm(name):
    n = unicodedata.normalize('NFKC', name or '')
    n = re.sub(r'[\s　・･\-‐－ー〜~（）()【】\[\]「」『』〈〉<>＜＞!！?？.,、。&＆]', '', n)
    return n.lower()

JALAN_AREAS = {
 '030000': {'LRG_030200':'盛岡','LRG_030100':'雫石','LRG_030300':'安比・八幡平・二戸','LRG_030500':'花巻・北上・遠野','LRG_031100':'奥州・平泉・一関','LRG_030800':'三陸海岸'},
 '040000': {'LRG_040200':'仙台・秋保・作並','LRG_040500':'松島・塩竈','LRG_041100':'鳴子・大崎','LRG_041400':'白石・蔵王','LRG_040800':'石巻・気仙沼','LRG_041200':'栗原・登米'},
}
PREF = {'030000': '岩手県', '040000': '宮城県'}
