# VLSAT-2 Label Verification Summary and Machine-Checked UNSAT Certificates for Three Instances

The results for the 100 VLSAT-2 instances were 47 SAT and 53 UNSAT. They agree with 97 entries in the reference table archived on 14 November 2026. The three discrepancies have UNSAT certificates checked by VeriPB 3.0.2 and CakePB CP2026 against their original CNFs. The [100-instance table](zenodo/VLSAT2_RESULTS_100.csv) identifies the results and the cases with certificates.

The [Zenodo dataset](https://zenodo.org/records/24519898) is the canonical release. Cite [DOI 10.5281/zenodo.24519898](https://doi.org/10.5281/zenodo.24519898).

[Dataset documentation](zenodo/README.md) · [日本語の説明](zenodo/README.ja.md) · [Manifest](zenodo/MANIFEST.json)

## Files hosted on Zenodo

- [REPORT.pdf](https://zenodo.org/records/24519898/files/REPORT.pdf?download=1)
- [vlsat2_67996_13708722.pbp.gz](https://zenodo.org/records/24519898/files/vlsat2_67996_13708722.pbp.gz?download=1)
- [vlsat2_68760_13862744.pbp.gz](https://zenodo.org/records/24519898/files/vlsat2_68760_13862744.pbp.gz?download=1)
- [vlsat2_69524_14016766.pbp.gz](https://zenodo.org/records/24519898/files/vlsat2_69524_14016766.pbp.gz?download=1)

## Verify the release

Download every file linked above into the `zenodo/` directory of this repository. From the repository root, use Python 3.11 or later to check the complete release.

```sh
python zenodo/verify_certificates.py --bundle zenodo --checksums-only
```

For replay against the official benchmark inputs, follow the [verification instructions](zenodo/README.md).

## License and citation

Generated data and documentation are licensed under CC BY 4.0. The public verifier is MIT-licensed. See the [license](zenodo/LICENSE), [third-party notices](zenodo/THIRD_PARTY_NOTICES.md) and [citation file](CITATION.cff).
