# ryokou — 岩手・宮城 子連れ宿リスト

大人2名＋3歳児1名で泊まれる岩手県・宮城県の宿を一覧にし、空室・料金・設備・部屋タイプを比較するページ。

- 公開ページ: https://claude.ai/artifact/62CGi8T4zkFBfaxvhUbtJL
- ページ本体: `site/index.html`（`site/hotels.json` と `site/avail/*.json` を読み込む）

## データの出どころ

| サイト | 取得内容 | 方法 |
|---|---|---|
| じゃらんnet | 宿一覧、部屋数・部屋タイプ、風呂、アメニティ、IN/OUT、評価、**日付指定の空室・料金（3名合計）** | `jalan_master_list.py` / `jalan_detail.py` / `jalan_date.py` |
| 楽天トラベル | 宿一覧、評価、最安値、設備タグ | `rakuten_list.py`（空室は自動取得不可のためリンクのみ） |
| Booking.com / Expedia / Agoda / Trip.com / 一休 / Yahoo!トラベル / Googleホテル | 日付・人数入りの検索リンク | ページ内で生成 |

## 空室データを別の日付で追加する

```sh
python3 -I scripts/jalan_date.py 2027-02-13 1 > site/avail/2027-02-13.json   # 日付, 泊数
python3 scripts/build_index.py                                               # avail/index.json を再生成
```
その後、`site/` をアーティファクトに再公開する。

`jalan_date.py` は2条件で検索する：
- `toddler` … 大人2＋幼児（食事・布団あり）1
- `soine` … 大人2のみ（3歳児が添い寝で泊まれる宿向け）

## 宿マスタを作り直す

```sh
export RYOKOU_CACHE=/tmp/ryokou_cache
python3 -I scripts/jalan_master_list.py > data/master_list.json
python3 -I scripts/jalan_detail.py data/master_list.json data/details.json
python3 -I scripts/rakuten_list.py > data/rk_list.json
python3 -I scripts/merge.py data/master_list.json data/details.json data/rk_list.json site/hotels.json
```
