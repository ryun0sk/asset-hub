# 2021年〜2026年10月18日のMBO調査

基準日：2026-10-18、日本時間。対象は日本の上場普通株の非公開化を目的として正式公表されたMBO。経営陣主導の非TOB株式併合2件は、MBOに準ずる行為として内数を分離する。期間は2021-01-01〜2026-10-18、年はTOB開始日・結果公表日・上場廃止日ではなく正式な初回公表日にそろえる。再実施はエピソードを分け、当初から予定した二段階の買付けは一つの計画として扱う。

東証の公式件数と、名証等の他市場を含む全国の件数は別に照合する。会社がMBOと説明していても上場維持を目的とする買付けは本表の外で記録する。非拘束提案・報道確認だけの案件、親会社による完全子会社化、経営陣が参加しない通常のTOBを正式MBOと混ぜない。

上場廃止一覧だけでは不成立や進行中の案件が欠ける。JPXの年次集計、年別TOB探索名簿、会社・買付者の公表・変更・結果開示を照合し、採否理由と未確認を保存する。二次資料の見出しは発見用に限り、理由の認定は原本本文・当事者の説明を確認して行う。

原本を読めていない項目はunknownとし、空欄を「動機なし」「障害なし」「MBOなし」に変換しない。公表後に開示された内部検討を、公表前に予測できた根拠に置き換えない。過去MBOの動機の頻度は、全上場企業に対する予測力・因果効果とは別の値である。

- [115案件・112社の分析レポート](report.md)・[全案件索引](episode-index.md)・[統合JSON](census.json)
- [Astraの独立レビュー](astra-review.md)・[採否と反映結果](adoption-notes.md)
- [他市場52行の一次確認](other-markets-audit.md)・[分類の未解消6件](scope-gap-candidates.json)・[同一入力による現在候補の再評価](current-evaluation.json)
- [2021〜2022年の台帳](years-2021-2022.json)・[確認メモ](notes-2021-2022.md)
- [2023〜2024年の台帳](years-2023-2024.json)・[確認メモ](notes-2023-2024.md)
- [2025〜2026年の台帳](years-2025-2026.json)・[確認メモ](notes-2025-2026.md)
- [JPX上場廃止の探索入口](jpx-delisting-seeds.json)・[全廃止行](jpx-all-delisting-rows.json)

公式の2026-01-26資料（[JPX原本](https://www.jpx.co.jp/equities/follow-up/nlsgeu000006gevo-att/t13vrt000000njd5.pdf)、PDF3頁）では、東証のMBO開示件数は2021年17、2022年11、2023年17、2024年18、2025年31。全国の件数や年度を変えた値と機械的に一致させず、差異の理由を記録する。

## 再生成と確認

```sh
python3 scripts/build_mbo_census.py
python3 -m unittest tests.test_mbo_census tests.test_mbo_assessment tests.test_mbo_dashboard
node --test tests/test_mbo_census.cjs tests/test_mbo_cases.cjs tests/test_mbo_ui.cjs tests/test_mbo_tab.cjs
```

集約スクリプトは年別台帳、旧8件の保存JSON、INFORICH追補、参考例・境界確認を読み、`census.json`と`web/mbo-census-data.js`を生成する。原本日付・引用位置・正式公表の確認状態・参照ID・重複・将来の実績日を検証する。旧資料の結果は上書きしない。旧詳細との時点補強は企業コードと正式公表日が一致するエピソードに限る。

独立の再評価スクリプトは新規runを作り、同じ入力ID・株価・財務・DCF/LBO・イベント・手動区分、旧runのバイト列保持をassertする。既に同ルールで成功したrunがあれば再利用する。株価の再取得は行わない。
