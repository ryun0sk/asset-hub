# MBO過去事例の一次資料確認 — 2026-10-18

8社を論点比較のために選んだケース集です。母集団からの無作為抽出ではなく、成立率、頻度、予測精度、因果効果の推定には使いません。構造化データは[cases-research.json](cases-research.json)。

正式MBO公表時の説明と、それより前の公開情報を分けました。**初報（報道・公式確認）より前の独立資料による未発見候補の事前予測は未確認**です。一方、スノーピークには正式MBO公表前の2024/2/16に、報道後の会社による検討確認が存在します。正式公表前の情報があったことと、初報前に予測できたことは別です。

## 公表前の境界

- **初報前**：報道または公式確認によって検討が初めて公知になる前。各案件の最初の報道は網羅的に特定しておらず、今回のケース集はこの段階の予測を検証していません。
- **最初の公式確認**：今回特定した最初の会社・買い手の公式資料。検討確認や非拘束提案受領を含み、正式実施決定とは限りません。
- **正式MBO公表前**：具体的なMBO実施決定・TOB開始予定の公表より前。既報案件の会社確認を含みうるため、初報前と分けます。
- JSONの `at_announcement` は正式MBO公表時を指します。正式MBOがないセブン＆アイでは非拘束提案受領の公式確認時です。

## 取引の区分

| 企業・コード | 最初の公式公表 | 確認した結果 |
|---|---|---|
| 大正製薬ホールディングス（4581） | 2023-11-24 | 経営陣側MBOのTOB成立、上場廃止済み。 |
| ベネッセホールディングス（9783） | 2023-11-10 | TOB成立後に上場廃止。初回正式公表は2024年ではなく2023年。 |
| スノーピーク（7816） | 2024-02-16（検討確認。正式MBOは2/20） | 経営陣＋BainのTOB成立、上場廃止。 |
| ローランド ディー.ジー.（6789） | 2024-02-09 | 競合側への買収移行ではない。Taiyo/XYZ側MBOが成立し上場廃止。 |
| ソフト99コーポレーション（4464） | 2025-08-06 | 2025のMBOは不成立。ECM側取引後、別の非公開化手続へ。10/18時点で11月総会・12月上場廃止は予定。 |
| セブン＆アイ・ホールディングス（3382） | 2024-11-13（非拘束提案の受領確認） | 当該創業家案は正式提案の資金調達見通しを失い、会社が検討しうる提案がない状態。公表済TOBの不成立例には数えない。 |
| 日本アジアグループ（3751） | 2020-11-05 | 当初MBOは不成立。その後の別買収者によるTOB・株式併合で上場廃止。 |
| アールビバン（7523） | 2025-08-29 | 2025不成立、2026再TOB成立・決済済。10/18時点で10/20総会・11/11上場廃止は未到来。 |

初回公表は、ベネッセは2023年、セブン＆アイの提案受領確認は2024年です。日本アジアGは2020年公表・2021年不成立の補助例。アールビバンとソフト99は2026年まで追跡しました。

## 個別事例

### 1. 大正製薬ホールディングス（4581）

取引主体：上原明・上原茂ら／上原茂100%の大手門。最初の公式公表：2023-11-24。

公開説明の動機：

- 営業体制・EC、生産設備、海外OTC、新薬開発、人事制度の改革を、短期業績の悪化リスクを許容しつつ中長期で進める。 根拠：[大正製薬HD MBO公表](https://www.taisho.co.jp/content/dam/corporate-site/jp/ja/news/2023/2023pdf/20231124-01.pdf)（PDF p8-13）。
- 当面の株式資金調達需要が乏しく、既存の知名度・信用があるとの説明。これは提案者の判断であり独立検証した事実ではない。 根拠：[大正製薬HD MBO公表](https://www.taisho.co.jp/content/dam/corporate-site/jp/ja/news/2023/2023pdf/20231124-01.pdf)（PDF p9, p13）。

確認できた障害・争点：

- 利益相反と買付価格の交渉。初期提示7400円から8620円まで引上げ。少数株主の同意を自動的に仮定できない。 根拠：[大正製薬HD MBO公表](https://www.taisho.co.jp/content/dam/corporate-site/jp/ja/news/2023/2023pdf/20231124-01.pdf)（PDF p10-12, p22-26）。

確認できた成立条件・経路：

- 応募60034194株が下限54650900株を上回りTOB成立。関連株主の応募・再出資合意も公表されていた。 根拠：[大正製薬HD TOB結果](https://www.taisho.co.jp/content/dam/corporate-site/jp/ja/news/2024/2024pdf/20240116-01.pdf)・[大正製薬HD MBO公表](https://www.taisho.co.jp/content/dam/corporate-site/jp/ja/news/2023/2023pdf/20231124-01.pdf)（結果PDF p1, p7／公表PDF p4-5）。

最終確認：経営陣側MBOのTOB成立、上場廃止済み。 根拠：[大正製薬HD TOB結果](https://www.taisho.co.jp/content/dam/corporate-site/jp/ja/news/2024/2024pdf/20240116-01.pdf)・[大正製薬HD 株式について](https://www.taisho.co.jp/company/taisho-holdings/stock/)。

- 分類上の注意：資金が豊富という説明だけで成立したとはいえない。応募下限到達と上場廃止を別の段階で確認。

参照factor_ids：`management_alignment`, `ownership_path`, `transformation`, `listing_tradeoff`, `funding_capacity`, `operating_uncertainty`, `listing_benefits`。

原文の短い抜粋：[原資料](https://www.taisho.co.jp/content/dam/corporate-site/jp/ja/news/2023/2023pdf/20231124-01.pdf)（PDF p1-5, p8-13, p22-26）「所有と経営を一致」。

初報前の独立資料による事前観測：未確認。正式MBO公表前の意向・資金確約も今回の確認範囲では未確認。公表資料が遡って述べる内部交渉は除外。

### 2. ベネッセホールディングス（9783）

取引主体：福武創業家グループ＋EQT／ブルーム1。最初の公式公表：2023-11-10。

公開説明の動機：

- 教育のデジタル化・海外展開、介護M&Aなどの変革をEQTの経営資源と進める。短期利益と変革投資の両立の難しさを説明。 根拠：[ベネッセ MBO開始予定の意見表明](https://www.benesse.co.jp/benesseinfo/ir/doc/library/OSH5.pdf)・[EQTによる創業家との共同非公開化公表](https://eqtgroup.com/news/bpea-eqt-to-commence-tender-offer-to-privatize-benesse-holdings-inc-in-partnership-with-its-founding-family-2023-11-10)（公表PDF p19-21, p27-28／EQT本文）。

確認できた障害・争点：

- 日本・中国の競争法、日本の外為法に係るクリアランス等を開始の前提とし、公表時点で開始日・完了を保証していない。 根拠：[ベネッセ MBO開始予定の意見表明](https://www.benesse.co.jp/benesseinfo/ir/doc/library/OSH5.pdf)（PDF p1-2）。

確認できた成立条件・経路：

- 応募67738016株が下限47818900株を超え成立。創業家のロールオーバーを組み込む所有経路が公表されていた。 根拠：[ベネッセ TOB結果](https://www.benesse.co.jp/benesseinfo/ir/doc/library/sKgs.pdf)・[ベネッセ MBO開始予定の意見表明](https://www.benesse.co.jp/benesseinfo/ir/doc/library/OSH5.pdf)（結果PDF p1／公表PDF p4-5）。

最終確認：TOB成立後に上場廃止。初回正式公表は2024年ではなく2023年。 根拠：[ベネッセ TOB結果](https://www.benesse.co.jp/benesseinfo/ir/doc/library/sKgs.pdf)・[ベネッセ 上場廃止決定](https://www.jpx.co.jp/news/1023/20240429-11.html)。

- 分類上の注意：2023/11/10の開始予定公表、2024/1/29の開始決定、1/30の開始を混同しない。
- 分類上の注意：会社FAQの成立日表現より、TOB結果原本2024/3/5の日付と応募数を優先した。

参照factor_ids：`management_alignment`, `ownership_path`, `transformation`, `listing_tradeoff`, `operating_uncertainty`。

原文の短い抜粋：[原資料](https://www.benesse.co.jp/benesseinfo/ir/doc/library/OSH5.pdf)（PDF p1-5, p19-21, p27-28）「長期的・持続的な事業変革」。

初報前の独立資料による事前観測：未確認。正式MBO公表前の意向・資金確約も今回の確認範囲では未確認。公表資料が遡って述べる内部交渉は除外。

### 3. スノーピーク（7816）

取引主体：山井太＋Bain／BCJ-80。最初の公式確認：2024-02-16（報道後の検討確認）。正式MBO公表：2024-02-20。

正式公表前の公式確認：2024/2/16、会社は同日の報道を受けて非公開化の検討を認め、決定した事実はないと説明しました。根拠：[報道後の検討確認](https://ir.snowpeak.co.jp/news/files/140120240216538923.pdf)（PDF p1）。この確認は既報案件の公式確認であり、初報前の未発見候補の予測根拠には使いません。

公開説明の動機：

- 非公開化で機動的な経営体制を作り、国内外マーケティング、海外販路、人財・組織基盤、M&A/PMIを強化する。 根拠：[スノーピーク TOB説明資料](https://ir.snowpeak.co.jp/news/files/20240220162958280s.pdf)（PDF p2-4）。

確認できた障害・争点：

- 買付下限を満たすことが成立条件。確認資料から、投資施策の合理性だけで成立が保証されたとは判断できない。 根拠：[スノーピーク TOB説明資料](https://ir.snowpeak.co.jp/news/files/20240220162958280s.pdf)（PDF p2）。

確認できた成立条件・経路：

- 応募22708815株が下限14539700株以上となった。 根拠：[スノーピーク TOB結果](https://ir.snowpeak.co.jp/news/files/140120240412570240.pdf)（PDF p1, p3）。

最終確認：経営陣＋BainのTOB成立、上場廃止。 根拠：[スノーピーク TOB結果](https://ir.snowpeak.co.jp/news/files/140120240412570240.pdf)・[スノーピーク 上場廃止決定](https://www.jpx.co.jp/news/1023/20240619-11.html)。

- 分類上の注意：2/16の公式検討確認、2/20の正式MBO公表を分ける。報道記事自体・有料配信にはアクセスしていない。

参照factor_ids：`management_alignment`, `ownership_path`, `transformation`, `listing_tradeoff`。

原文の短い抜粋：[原資料](https://ir.snowpeak.co.jp/news/files/20240220162958280s.pdf)（PDF p2-4）「マーケティング強化」。

初報前の独立資料による事前予測：未確認。正式MBO公表前には2/16の公式検討確認あり（報道後）。資金確約の事前確認は未実施。

### 4. ローランド ディー.ジー.（6789）

取引主体：田部耕平＋Taiyo Pacific／XYZ。競合提案はブラザー工業。最初の公式公表：2024-02-09。

公開説明の動機：

- 公表時（2024/2/9）：社長がMBO後も経営を継続し、公開買付者へ出資する予定と説明。 根拠：[ローランドDG MBO公表](https://corporate.rolanddg.com/ja/investors/ir-news/rdg20240209_mbo_jp/main/0/link/rdg20240209_mbo_jp.pdf)（PDF p3）。
- 公表後の説明（2024/11/29）：機動的な意思決定、既存事業の収益性改善、新市場・新事業の推進をMBOの目的として説明。 根拠：[ローランドDG 親会社との合併説明](https://corporate.rolanddg.com/ja/news/241129-Notice-regarding-the-Merger-with-Parent-Company-XYZ.html)（HTML 1.本合併について）。この後続説明は公表時点の証拠に含めません。

確認できた障害・争点：

- ブラザーによる競合TOBの開始予告があった。XYZは成立確度向上のため買付価格5035→5370円に改定。競合出現が即MBO失敗を意味しない例。 根拠：[ローランドDG MBOとブラザー提案の見解](https://corporate.rolanddg.com/ja/investors/ir-news.html)・[ローランドDG 買付価格変更](https://corporate.rolanddg.com/ja/investors/ir-news/rdg20240426_tender_offer_jp/main/0/link/rdg20240426_tender_offer_jp.pdf)（IR一覧2024/3/13, 4/26／価格変更PDF p2）。

確認できた成立条件・経路：

- 最終応募9247711株が下限8151100株を超え、元のXYZ側MBOが成立。 根拠：[ローランドDG TOB結果](https://corporate.rolanddg.com/ja/investors/ir-news/rdg20240516_jp/main/0/link/rdg20240516_jp.pdf)（PDF p1, p5）。

最終確認：競合側への買収移行ではない。Taiyo/XYZ側MBOが成立し上場廃止。 根拠：[ローランドDG TOB結果](https://corporate.rolanddg.com/ja/investors/ir-news/rdg20240516_jp/main/0/link/rdg20240516_jp.pdf)・[ローランドDG 親会社との合併説明](https://corporate.rolanddg.com/ja/news/241129-Notice-regarding-the-Merger-with-Parent-Company-XYZ.html)。

- 分類上の注意：ブラザーの開始予告を、実際にTOBを開始・成立させたという意味で記録しない。
- 分類上の注意：応募・値上げ・成立の時系列を記録し、値上げだけの因果効果を推定しない。

参照factor_ids：`management_alignment`, `ownership_path`, `transformation`, `listing_tradeoff`, `competing_policy`。

初報前の独立資料による事前観測：未確認。正式MBO公表前の意向・資金確約も今回の確認範囲では未確認。公表資料が遡って述べる内部交渉は除外。

### 5. ソフト99コーポレーション（4464）

取引主体：田中秀明100%の堯アセットマネジメント。競合はECM SPV3。最初の公式公表：2025-08-06。

公開説明の動機：

- 固有技術・老朽設備、サービス・海外市場、デジタル化、M&Aへの投資を進め、短期利益・株価への影響を回避したいとの説明。 根拠：[ソフト99 MBO公表](https://www.soft99.co.jp/img/250806_1.pdf)（PDF p12-16, p22-23）。
- 自己資金と銀行借入で必要資金を賄え、当面株式資金調達は不要との提案者判断。買収用資金の拘束的コミットメントを独立確認した意味ではない。 根拠：[ソフト99 MBO公表](https://www.soft99.co.jp/img/250806_1.pdf)（PDF p16）。

確認できた障害・争点：

- MBO側は期間延長・価格改定後も、応募5601461株が下限7566400株未達。最終2680円で取得ゼロ。 根拠：[ソフト99 経営陣側TOB結果](https://www.soft99.co.jp/img/251114.pdf)（PDF p3）。
- 競合ECM側は別のTOBを成立させた。同じ対象会社の非公開化でも、経営陣側MBOと競合投資家の取引を同一結果ラベルにしない。 根拠：[ソフト99 ECM側TOB結果](https://www.soft99.co.jp/img/251114-2.pdf)（PDF p1-2）。

確認できた成立条件・経路：

- 2026/9の別計画ではECMと創業家等を残す株式併合を提案。残存株主の合意経路が変更された。 根拠：[ソフト99 別の株式併合計画](https://www.soft99.co.jp/img/260911h.pdf)（PDF p1-2）。

最終確認：2025のMBOは不成立。ECM側取引後、別の非公開化手続へ。10/18時点で11月総会・12月上場廃止は予定。 根拠：[ソフト99 経営陣側TOB結果](https://www.soft99.co.jp/img/251114.pdf)・[ソフト99 ECM側TOB結果](https://www.soft99.co.jp/img/251114-2.pdf)・[ソフト99 別の株式併合計画](https://www.soft99.co.jp/img/260911h.pdf)。

- 分類上の注意：会社が初回原本で明示的にMBOと定義しており、MBO分類は確認済み。
- 分類上の注意：後続のECM主導取引・創業家との合意を、初回MBOの成立へ読み替えない。

参照factor_ids：`management_alignment`, `ownership_path`, `transformation`, `listing_tradeoff`, `funding_capacity`, `shareholder_resistance`, `operating_uncertainty`, `listing_benefits`, `competing_policy`。

原文の短い抜粋：[原資料](https://www.soft99.co.jp/img/250806_1.pdf)（PDF p1-2, p12-16, p22-23）「自己資金及び金融機関」。

初報前の独立資料による事前観測：未確認。正式MBO公表前の意向・資金確約も今回の確認範囲では未確認。公表資料が遡って述べる内部交渉は除外。

### 6. セブン＆アイ・ホールディングス（3382）

取引主体：伊藤順朗・伊藤興業。別提案者はACT。最初の公式公表：2024-11-13。

正式なMBO/TOB実施決定日は未確認。提案受領の公表日を、正式TOB発表日と扱っていません。

公開説明の動機：

- 会社は創業家案、ACT案、独立継続案を株主価値の観点で比較すると説明。創業家案固有の詳細な事業計画・動機は確認資料では非公表。 根拠：[セブン＆アイ 創業家提案受領の確認](https://www.7andi.com/library/dbps_data/_material_/localhost/ja/release_pdf/2024_1113_ir01.pdf)（PDF p1）。

確認できた障害・争点：

- 正式提案に必要な資金調達の目途が立たなくなったとの提案者連絡を会社が受領。正式TOBの応募不足とは異なる。 根拠：[セブン＆アイ 資金調達見通し消失の公表](https://www.7andi.com/library/dbps_data/_material_/localhost/ja/release_pdf/2025_0227_ir01.pdf)（PDF p1）。

最終確認：当該創業家案は正式提案の資金調達見通しを失い、会社が検討しうる提案がない状態。公表済TOBの不成立例には数えない。 根拠：[セブン＆アイ 創業家提案受領の確認](https://www.7andi.com/library/dbps_data/_material_/localhost/ja/release_pdf/2024_1113_ir01.pdf)・[セブン＆アイ 資金調達見通し消失の公表](https://www.7andi.com/library/dbps_data/_material_/localhost/ja/release_pdf/2025_0227_ir01.pdf)。

- 分類上の注意：初回公式確認は2024/11/13、資金未達の公式確認は2025/2/27。
- 分類上の注意：ACT側の米国競争法課題を、創業家案の資金調達失敗原因だと断定しない。
- 分類上の注意：提案受領の公表はあったが、拘束的な正式MBO/TOB実施決定とは区別する。

参照factor_ids：`management_alignment`, `ownership_path`, `funding_gap`, `competing_policy`。

原文の短い抜粋：[原資料](https://www.7andi.com/library/dbps_data/_material_/localhost/ja/release_pdf/2024_1113_ir01.pdf)（PDF p1）「法的拘束力のない」。

初報前の独立資料による事前観測：未確認。正式MBOは未公表のため、その前という基準での観測は対象外。公表資料が遡って述べる内部交渉は除外。

### 7. 日本アジアグループ（3751）

取引主体：山下哲生＋カーライル。後続はシティインデックスイレブンス。最初の公式公表：2020-11-05。

公開説明の動機：

- 各事業の成長段階に応じた再編、子会社の成長支援と経営者が残存事業に集中する体制を説明。 根拠：[日本アジアG MBO公表](https://www.carlyle.com/ja/media-room/news-release-archive/%E6%97%A5%E6%9C%AC%E3%82%A2%E3%82%B8%E3%82%A2%E3%82%B0%E3%83%AB%E3%83%BC%E3%83%97%E4%BB%A3%E8%A1%A8%E5%8F%96%E7%B7%A0%E5%BD%B9%E4%BC%9A%E9%95%B7%E5%85%BC%E7%A4%BE%E9%95%B7%E3%81%AE%E5%B1%B1%E4%B8%8B%E5%93%B2%E7%94%9F%E6%B0%8F%E3%81%AB%E3%82%88%E3%82%8B%E6%97%A5%E6%9C%AC%E3%82%A2%E3%82%B8%E3%82%A2%E3%82%B0%E3%83%AB%E3%83%BC%E3%83%97%E3%81%AEmbo%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6)（HTML本文）。
- 失敗後の説明では金融債務整理・ネットデット解消と赤字残存事業再建、金融機関の条件付き支援を挙げた。公表前情報ではない。 根拠：[日本アジアG MBO不成立と背景の説明](https://www.carlyle.com/sites/default/files/press_releases/CJP_2021-007JP.pdf)（PDF p1-2）。

確認できた障害・争点：

- 買付条件改定後も2021/2/9終了でMBO不成立。買い手は残存事業価値や資金配分・価格をめぐる株主との見解相違を説明。正否や寄与度の独立検証は未実施。 根拠：[日本アジアG MBO不成立と背景の説明](https://www.carlyle.com/sites/default/files/press_releases/CJP_2021-007JP.pdf)（PDF p1-2）。

確認できた成立条件・経路：

- 別のシティ側TOBは11970492株を取得し、同社の親会社への異動を会社が報告。 根拠：[日本アジアG シティ側TOB結果](https://www2.jpx.co.jp/disc/37510/140120210730475674.pdf)（PDF p1, p3, p5）。

最終確認：当初MBOは不成立。その後の別買収者によるTOB・株式併合で上場廃止。 根拠：[日本アジアG MBO不成立と背景の説明](https://www.carlyle.com/sites/default/files/press_releases/CJP_2021-007JP.pdf)・[日本アジアG シティ側TOB結果](https://www2.jpx.co.jp/disc/37510/140120210730475674.pdf)・[日本アジアG 上場廃止決定](https://www.jpx.co.jp/news/1023/20210831-11.html)。

- 分類上の注意：最終的な上場廃止を、当初カーライル支援MBOの成功に分類しない。
- 分類上の注意：funding_commitmentタグは買い手が述べた成立前提の金融機関支援の論点。拘束力・全実行条件の確認済みを意味しない。

参照factor_ids：`management_alignment`, `ownership_path`, `transformation`, `funding_commitment`, `shareholder_resistance`, `operating_uncertainty`, `competing_policy`。

初報前の独立資料による事前観測：未確認。正式MBO公表前の意向・資金確約も今回の確認範囲では未確認。公表資料が遡って述べる内部交渉は除外。

### 8. アールビバン（7523）

取引主体：野澤克巳100%のOrsay／カツコーポレーション。最初の公式公表：2025-08-29。

公開説明の動機：

- 新アーティスト発掘、美術品・オンライン販路拡充、ヨガ事業のマーケティング・新業態等の先行投資。短期収益・CFの悪化を許容する非公開化を説明。 根拠：[アールビバン 初回MBO公表](https://www.artvivant.co.jp/wp-content/uploads/2025/08/b75cc27caf7451954882a07cade8f07f.pdf)（PDF p7-9）。

確認できた障害・争点：

- 2025は1670円のTOBで応募1947759株が下限2987200株未達。2026公表資料では前回中・後に増加した大株主との協議も説明。 根拠：[アールビバン 初回TOB結果](https://www.artvivant.co.jp/wp-content/uploads/2025/10/b036bcdd61b1200463b5fdb54d40c9e5.pdf)・[アールビバン 再MBO公表](https://www.artvivant.co.jp/wp-content/uploads/2026/07/e925ac0f5f710dbfedf978eeef37852f.pdf)（結果PDF p3／再公表PDF p10以降）。

確認できた成立条件・経路：

- 2026に1900円で再実施し、応募5466270株が下限3845584株を超過。9/17資料で9/1決済とOrsay59.73%保有を確認。価格・持分・合意条件が変わった再試行である。 根拠：[アールビバン 再TOB結果](https://www.artvivant.co.jp/wp-content/uploads/2026/08/73ac8c8fe109284b5b83a21e09fb5f9b.pdf)・[アールビバン 株式併合総会計画](https://www.artvivant.co.jp/wp-content/uploads/2026/09/5530acd4feee6490c4dec8a1399110c0.pdf)（結果PDF p1, p5／総会計画PDF p1）。

最終確認：2025不成立、2026再TOB成立・決済済。10/18時点で10/20総会・11/11上場廃止は未到来。 根拠：[アールビバン 初回TOB結果](https://www.artvivant.co.jp/wp-content/uploads/2025/10/b036bcdd61b1200463b5fdb54d40c9e5.pdf)・[アールビバン 再TOB結果](https://www.artvivant.co.jp/wp-content/uploads/2026/08/73ac8c8fe109284b5b83a21e09fb5f9b.pdf)・[アールビバン 株式併合総会計画](https://www.artvivant.co.jp/wp-content/uploads/2026/09/5530acd4feee6490c4dec8a1399110c0.pdf)。

- 分類上の注意：同一企業の複数試行であり、互いに独立した成功例・失敗例として扱わない。
- 分類上の注意：主力アーティストの高齢化は経営者の承継問題と異なる。successionの証拠にはしていない。
- 分類上の注意：2026/7/10公表原本は7/13訂正版がある。結果と最新株式併合資料で価格・応募数を再確認。

参照factor_ids：`management_alignment`, `ownership_path`, `transformation`, `listing_tradeoff`, `shareholder_resistance`, `operating_uncertainty`, `listing_benefits`。

原文の短い抜粋：[原資料](https://www.artvivant.co.jp/wp-content/uploads/2025/08/b75cc27caf7451954882a07cade8f07f.pdf)（PDF p1-3, p7-9）「新規性の高い取り組み」。

初報前の独立資料による事前観測：未確認。正式MBO公表前の意向・資金確約も今回の確認範囲では未確認。公表資料が遡って述べる内部交渉は除外。

## 評価項目へ引き継ぐときの範囲

- `factor_ids`はケースが示す検討論点のタグです。要因の効果方向・重み・予測力を推定した値ではありません。
- 経営陣の参加、持分・不応募株、買付下限、資金調達の見通し、競合方針を別々に確認します。経営陣の参加や金融機関の条件付き支援だけでは成立を保証しません。
- ローランドDGは競合提案後も元のMBOが成立した例。日本アジアGとソフト99は、当初MBOの不成立と後続の別買収を区別する例です。
- アールビバンの2025と2026は同一企業の再試行です。条件が変わった2つの独立観測として集計しません。
- `succession`は、今回の一次確認から経営承継動機の確証を置けませんでした。創業家、経営者の年齢、主力アーティストの高齢化を、その代わりにしません。
- セブン＆アイについて会社は資金調達見通し消失を明示していますが、創業家案の詳細事業計画・必要資金構成・最終融資条件は確認資料からは不明です。
- 2026-10-18より後の株主総会・上場廃止は予定として記録し、完了実績へ先取りしません。

## 出所と確認方法

公式企業IR、買い手・スポンサー、JPXの一次資料のみを根拠に採用しました。企業・買い手の説明は当事者の見解として記載し、検証済みの因果説明へ置き換えていません。原本の公開日・URL・PDFページまたはHTML項目・短い引用はJSONのsources辞書に収録しています。今回の成果物に原本全文を転載していません。

PDFは本文と表のページを確認し、選択した動機説明・結果ページは描画して年度・条件・数値を照合しました。資料取得は公開原本の読み取りに限り、有料API、X、課金CLI、commit/pushは使用していません。編集したリポジトリファイルは本MDとJSONのみです。
