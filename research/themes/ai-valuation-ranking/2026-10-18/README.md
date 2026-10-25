# AIサプライチェーン46社の将来利益・割安度比較｜2026-10-18

依頼：先の8社の利益・EPS試算をAsset HubのAI関連上場企業全体へ広げ、株価の割安度順の表を作成し、Asset Hubへ反映する。

対象は[AIサプライチェーンの掲載46社](../../ai-supply-chain/2026-10-18/README.md)。2026-10-18 JSTまでの公表資料を確認し、株価は10月16日終値でそろえる。OpenAI/Anthropic等の非上場企業は株価順位の対象外。

2028・2029年の暦年相当の年間利益を、弱気・基準・強気の独自シナリオで計算する。業種ごとに需要・事業構成・数量/価格・費用・税・希薄化株数を分け、実績・会社見通し・外部調査と独自仮定を区別する。

順位の基準は `将来EPS×仮定PER÷1.12^年数÷現在株価−1`。この値は条件付きの価格比較であり、確率付き期待収益率や完全なDCFではない。配当・税金・将来為替の変化を含まず、現金蓄積等の扱いにも限界がある。仮定の強さ・モデル確度・弱気ケースを併記する。

- [先の8社の詳細モデル](../../ai-forward-valuation/2026-10-18/report.md)
- [共通の市場規模から利益へつなぐ方法](../../ai-growth-outlook/2026-10-18/gdp-share-model.md)
- [全調査の入口](../../../../README.md)

## 成果物

- [上位5社：私の試算とアナリスト予想の比較（10/18追補）](analyst-comparison.md) · [比較計算](analyst-comparison.json) · [外部予想の時点・基準](analyst-comparison-sources.json)

- [上位5社の利益確度・リスク・私が買う順（10/18追補・台湾CB訂正）](top-five-review.md) · [感応度計算](top-five-calculations.json)

- [46社の比較レポート・基準と反証](report.md)
- [表示用データ](ranking.json) · [全276ケースJSON](results.json) · [CSV](results.csv)
- [10/16株価・為替・公開取得先・ハッシュ](prices.json)
- [装置・材料等12社の入力](inputs/japan.json) · [計算・メモリ・サーバー14社の入力](inputs/compute.json) · [光・電力・クラウド等12社の入力](inputs/infrastructure.json)
- [入力ハッシュ](input-manifest.json) · [検証記録](validation.json) · [統合再計算](build_model.py)

46社すべてを掲載し、EatonはMobility分離価値を未評価のため順位比較対象外の参考行。比較可能な45社を並べる。「詳細モデル」「事業別試算」「限定的な試算」は確認範囲の区分で、予測確率ではない。市場シェアが不明な企業は事業売上を起点とした校正であることを表示する。

価格とEPSは同じ通貨・普通株・分割基準。TSMCは旧8社表の米国ADRから台湾普通株2330.TWへ統一し、EPSはADR÷5×USD/TWDへ換算。株価は実際の台湾終値を使うため、ADR表とは価格余地が異なる。Samsungは普通株・利益参加優先株の等価分母、LenovoはUSD財務からHKD普通株へ一度換算する。

## 再現

リポジトリのルートから実行する。下記の再計算は保存済み入力だけを読み、ネットワーク・追加パッケージを使わない。8社は既存の詳細モデル入力を再計算し、38社は事業売上倍率・シェア/取り分・費用・税・分母から照合する。

```sh
python3 research/themes/ai-valuation-ranking/2026-10-18/inputs/japan.py
python3 research/themes/ai-valuation-ranking/2026-10-18/inputs/compute.py
python3 research/themes/ai-valuation-ranking/2026-10-18/inputs/infrastructure.py
python3 research/themes/ai-valuation-ranking/2026-10-18/build_model.py
node --test tests/test_ai_forward_ranking.cjs
python3 scripts/build_catalog.py
python3 scripts/archive_snapshots.py --write
python3 scripts/build_catalog.py --check
python3 scripts/archive_snapshots.py --check
```

株価の取得処理は[fetch_prices.py](fetch_prices.py)。日次Closeは分割調整後・配当未調整。取得日時と原本SHA-256をprices.jsonへ保存する。FXは同日値で、各株式市場の引けと同じ瞬間ではない。再調査は新しい日付フォルダへ保存し、この価格・仮定を後日の値で上書きしない。

## 画面

Asset Hubの「AI関連銘柄・サプライチェーン」→「将来利益・割安度」（`#ai/forward`）。工程・企業検索・年・ケース・要求年率・確認範囲を切り替え、価格余地または将来利益倍率で並べ替えられる。各行の前提・6ケース・出典を展開して確認する。

過去のスナップショットと無関係なローカル変更を保護し、今回の調査と画面だけを非公開Asset Hubへ反映する。売買・commit・push・IAMや閲覧者の変更は行わない。

## 10/18追補の訂正記録

台湾2社の既存CBの潜在株織込み不足を訂正した。Wiwynnは現在株＋両CB原発行全元本の潜在株を上限として将来株数増を加え、Quantaも同様に計算する。最新残存元本は確定照合できず既転換の重複があり得るため、正確なGAAP分母ではなく保守的な経済EPSの仮定。売上・純利益・株価を変更せず、旧公開版を[revisions/initial-published](revisions/initial-published/manifest.json)へ保存した。再計算は既存compute.py→build_model.pyのあと、`python3 research/themes/ai-valuation-ranking/2026-10-18/top-five-calculations.py`。
