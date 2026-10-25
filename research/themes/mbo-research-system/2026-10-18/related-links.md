# MBOリサーチシステムの出典とデータ制約

確認日：2026-10-18（日本時間）。以下は公式資料の内容であり、APIを認証して実データの欠測率や網羅性を試験した結果ではない。公表日を確認できないページは「記載なし」とした。工程・配点・予算上限の提案は [設計プラン](report.md) と [技術設計](technical-design.md) にある。

| ID | 公式資料 | 公表日等 | 確認した内容と設計への影響 |
|---|---|---|---|
| S01 | [JPX ヒストリカル情報](https://www.jpx.co.jp/markets/paid-info-equities/historical/) | 公表日記載なし | 現行比較表でLight月1,650円、Standard月3,300円、Premium月16,500円、税込。J-Quants APIは個人向けで法人利用・二次配布不可。個人の非公開利用を前提にする。 |
| S02 | [J-Quants プラン別データ範囲](https://jpx-jquants.com/ja/spec/data-spec) | 公表日記載なし | Freeは12週遅延。Lightは5年、Standardは10年、Premiumは20年までというプラン上限があるが、実際はデータ自体の収録開始にも制限される。Standardに財務サマリーと株主関連データがあり、詳細BS/PL/CFはPremium。TDnetは別アドオン、5年。 |
| S03 | [JPX TDnetアドオン開始](https://www.jpx.co.jp/corporate/news/news-releases/6020/20260518-01.html) | 2026-05-18 | Light以上に月11,000円税込を追加。過去5年の履歴を定額取得。個人向けで法人・学術用途不可。Standardとの合計は月14,300円。 |
| S04 | [J-Quants 上場銘柄一覧](https://jpx-jquants.com/ja/spec/eq-master) | 公表日記載なし | 過去日指定が可能。休業日を指定すると翌営業日の情報が返るため、検証では取引カレンダーで営業日を確定する。コードを固定の整数IDとして扱わない。 |
| S05 | [J-Quants 大株主状況](https://jpx-jquants.com/ja/spec/edinet-major-shareholders) | 公表日記載なし | 有価証券報告書の大株主情報。Standard以上、収録は2016-06-01以降。提出日・時刻、対象事業年度、株数・比率を取得する設計。名義と実質所有者は同一とは限らない。 |
| S06 | [J-Quants 政策保有株式](https://jpx-jquants.com/ja/spec/edinet-cross-shareholdings) | 公表日記載なし | 2020-03-31以降、Standard以上。提出会社・連結最大保有会社・連結第二最大保有会社のスコープを分ける。仕様にLLMによるデータ修正の注記があり、重要な金額や関係は原本照合する。 |
| S07 | [J-Quants 大量保有報告書](https://jpx-jquants.com/ja/spec/edinet-large-volume-shareholders) | 公表日記載なし | 提出日2021-07-01以降、Standard以上。大量保有・変更報告等の対象書類を構造化取得できる。共同保有と経済的利害・議決権の違いは原文も確認する。 |
| S08 | [J-Quants TDnetインデックス仕様](https://jpx-jquants.com/ja/spec/td-list) | 公表日記載なし | 5年分。題目の訂正は反映しない。ファイル訂正は新規開示番号。削除後も取得可能。現仕様はDiscStatusが常にNull、RevNoが常に1。これらの値だけで現時点の有効性を判定しない。 |
| S09 | [J-Quants API案内](https://jpx-jquants.com/ja/spec) | 公表日記載なし | V1は2026-06-01終了と記載。実装はV2を採用。古い認証・エンドポイント例を転用しない。 |
| S10 | [J-Quants レートリミット](https://jpx-jquants.com/ja/spec/rate-limits) | 公表日記載なし | プランとエンドポイントによる制限を実装時に確認し、差分取得・ページング・待機を組み合わせる。無制限並列取得を前提にしない。 |
| S11 | [EDINET API仕様書 Version 2](https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/download/ESE140206.pdf) | 表紙はVersion 2。改訂履歴あり | 第2章はAPIキー発行、第3章は一覧・書類取得。PDF p10は書類別の閲覧期間、p45〜46は一覧日付の指定、p80〜82はPDF/XBRL/CSV取得。最大10年という一覧指定範囲と各書類の取得可能期間を区別する。 |
| S12 | [EDINET 公式FAQ](https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/WZEK0090_001.html) | ページ内で案内 | API Q10〜12。訂正書類・同一IDの書類情報修正・取下げ・不開示等を考慮する。現在取得できる原本が当時と完全に同じとは仮定しない。 |
| S13 | [JPX 従来型TDnet API](https://www.jpx.co.jp/markets/paid-info-listing/tdnet/02.html) | 公表日記載なし | 基本料月7万円税抜と取得件数による追加料。個人MVPの標準構成には採用しない。個人向けTDnetアドオンと混同しない。 |
| S14 | [JPX MBO等の手続きに関するFAQ](https://faq.jpx.co.jp/disclo/tse/web/knowledge8686.html) | ページ内で案内 | MBO、支配株主による取引、これらに準ずる構造を区別。モデルのMBOラベルは当該取引の公式説明・経営陣の関与から人が確定する。 |
| S15 | [INFORICH MBO公表資料](https://monex-open-disclose.ifis.co.jp/6fd/140120260213562350.pdf) | 2026-02-13 | 会社開示の配信ミラー。MBOの動機・計画、価格評価の資料例。発表資料に初めて出る事業計画や交渉経緯を、発表前に知っていた情報として使わない。 |

## 取得開始時に確かめる項目

1. 各契約の最新価格、私的利用の範囲、データ・派生値の保存、クラウド上の本人用表示、契約終了後の保管、外部LLMでの処理が許容される範囲を確認する。本人用IAP認証だけで利用条件を満たしたと断定しない。
2. APIで返る公表日時・収録日時・訂正状態をサンプルで原本と照合する。存在するAPIでも、必要な履歴や全社の網羅性があるとは限らない。
3. 当時の上場企業一覧と上場廃止銘柄の価格・現金化の履歴を試す。欠けた企業を落として過去成績を計算しない。
4. 会社IRは未契約時の補完経路になるが、リンク切れ・保存年数・更新方式が企業ごとに異なる。全市場の開示取得を保証する経路として扱わない。

過去の別調査に設定されたX APIの300円上限は、このシステムの予算ではない。X APIは既使用額と単価が未確認のため使用しない。
