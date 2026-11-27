# VLSAT-2 Label Verification Summary and Machine-Checked UNSAT Certificates for Three Instances

The VLSAT-2 reference labels and verification results agree for 97 of 100 instances. The published table lists 50 SAT and 50 UNSAT. The recorded results are 47 SAT and 53 UNSAT. The three disagreements have machine-checkable UNSAT certificates against the complete original CNFs.

The technical report is REPORT.pdf. VLSAT2_RESULTS_100.csv describes the whole suite. MANIFEST.json identifies the three proofs and original inputs. The certificate coverage is the three discrepant instances. The historical table is the CADP snapshot dated 14 November 2026.

## Verification

Use Python 3.11 or later, VeriPB 3.0.2 and CakePB CP2026 (cake_pb_cnf). Install the checkers from the upstream projects listed below. Allow approximately 8 GiB of memory for CakePB and at least 400 MB of temporary space for one case. The script sets the CakeML heap to 7,296 MiB and the stack to 768 MiB. Put the original .cnf.bz2 or unmodified .cnf files in a separate directory, or fetch them from the official CADP distribution using the third example. The first command checks integrity only. The other two replay the certificates with both checkers.

```text
python verify_certificates.py --checksums-only
python verify_certificates.py --original-dir originals
python verify_certificates.py --fetch-original
```

Use --case with one of the three benchmark names to replay a single case. Use --veripb or --cakepb to provide checker paths. On Windows, add --cakepb-wsl with cake_pb_cnf available in the default WSL distribution. If WSL uses a path outside PATH, also supply its Linux path using --cakepb. Run the checks one case at a time on hosts with limited memory.

Successful replays require both the tool's UNSAT verification marker and exit code zero. Proofs are gzip-compressed pseudo-Boolean files with cutting-planes steps. The official CNF source and all expected SHA-256 digests are in MANIFEST.json.

- [Original VLSAT-2 dataset](https://doi.org/10.18709/perscido.2021.11.ds357)
- [VLSAT-2 table and distribution](https://cadp.inria.fr/resources/vlsat/2.html)
- [VeriPB](https://gitlab.com/MIAOresearch/software/pboxide) and [CakePB](https://gitlab.com/MIAOresearch/software/cakepb)

The generated table, certificates, and documentation are CC BY 4.0. The verification script uses MIT. Original benchmark attribution is in THIRD_PARTY_NOTICES.md.
