# 実企業による初回MBO候補調査

調査日：2026-10-18（日本時間）。公開IRと保存した株価を使う初回の限定調査。日本の全上場企業を網羅したスクリーニングではない。上場・公表案件の確認から始め、財務を原本照合できた企業だけ価値を試算する。

- [調査結果・評価・不足情報](report.md)
- [計算結果と評価条件](analysis.json)
- [検証済み転記データ](research-inputs.json)・[再現用の入力作成](prepare_inputs.py)・[独立照合と結果書出し](analyze.py)
- [Macでの週次運用](../../../../docs/mbo-weekly.md)
- [Asset HubのMBO調査](https://asset-hub-pvgbytjsqa-an.a.run.app/#mbo/candidates)

実績は各社の通期決算、最新の中間・四半期資料、株主・自己株式の開示と照合する。会社予想と独自仮定は実績から分ける。保存株価の日付は銘柄別に明示する。株数は自己株控除後とし、確認可能な希薄化要因・分割基準・その後の自己株取得を点検する。

原本、確認用テキスト、取込CSV、SQLite、凍結runはGit対象外の `data/private/mbo-inbox/2026-10-18/` と `data/private/mbo/` に保存する。原本はSHA-256で照合する。クラウドへは閲覧用に選別したJSONだけを反映する。

余剰現金は会社の会計実績ではない。現金同等物の実績とは別に、留保額と根拠を記した `own_scenario` の調整として扱う。未確認の負債・非支配持分をゼロで埋めず、数値が揃わないときは評価を保留する。

DCFは通期の実績CF構成要素からの簡易外挿で、MBOの買付価格予測ではない。LBOの資金調達条件も独自の感応度試算。候補の優先度をMBO発生確率と解釈しない。公表済み案件・上場廃止企業を新しい発見から分け、外部環境・事業変化・創業家の意思が未確認であることを残す。

再現：`python3 research/themes/mbo-candidates/2026-10-18/prepare_inputs.py` で保存済み原本ハッシュを検証しCSVを作成する。`python3 -m backend.mbo weekly data/private/mbo-inbox/2026-10-18 --as-of 2026-10-18 --dry-run` で入力点検後、別の保存先で取込・buildできる。`analyze.py --data-dir <凍結runの保存先>` は基準DCFを閉形式でも照合し `analysis.json` へ保存する。原本はローカル専用のため、別環境では不足ファイルを保存してから実行する。
