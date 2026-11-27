# VLSAT-2 全100件の検証集計と3件のUNSAT証明

公式表のラベルはSAT 50件、UNSAT 50件です。検証結果はSAT 47件、UNSAT 53件で、97件が公式表と一致しました。残る3件について、無加工展開した完全DIMACS CNFに対するUNSAT証明を収録しています。全100件の集計はVLSAT2_RESULTS_100.csv、技術報告はREPORT.pdf、原本と証明のハッシュはMANIFEST.jsonにあります。

## 再検証

Python 3.11以降、VeriPB 3.0.2、CakePB CP2026のcake_pb_cnfを使います。CakePBのヒープは7,296 MiB、スタックは768 MiBです。1件ずつの実行に約8 GiBのメモリと400 MB以上の一時領域を用意してください。公式の.cnf.bz2か無加工の.cnfをoriginalsに置くか、公式配布元からの取得を選べます。

```text
python verify_certificates.py --checksums-only
python verify_certificates.py --original-dir originals
python verify_certificates.py --fetch-original
```

WindowsでCakePBをWSLから使うときは --cakepb-wsl を追加します。必要に応じて --veripb と --cakepb でチェッカーを指定してください。

原データセットは[公式DOI](https://doi.org/10.18709/perscido.2021.11.ds357)、帰属はTHIRD_PARTY_NOTICES.mdを参照してください。生成した証明、集計、文書はCC BY 4.0、公開検証スクリプトはMITです。
