#!/usr/bin/env python3
"""Rebuild site/avail/index.json from the snapshot files."""
import json, glob, os
root = os.path.join(os.path.dirname(__file__), '..', 'site', 'avail')
idx = []
for f in sorted(glob.glob(os.path.join(root, '20*.json'))):
    d = json.load(open(f))
    idx.append({'date': d['date'], 'nights': d['nights'], 'fetchedAt': d['fetchedAt'],
                'toddler': len(d['modes']['toddler']), 'soine': len(d['modes']['soine'])})
json.dump(idx, open(os.path.join(root, 'index.json'), 'w'), ensure_ascii=False)
print(idx)
