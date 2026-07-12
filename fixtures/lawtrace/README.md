# LawTrace HK — open-data fixtures for feasibility spike

## Legal status

LawTrace displays transformations of open data obtained through DATA.GOV.HK.
LawTrace output is for information and research only and is not a verified copy
of legislation. Users requiring an official verified copy should consult Hong
Kong e-Legislation.

## Layout

| Path | Contents |
|------|----------|
| `cap_614/` | Trimmed English Cap. 614 XML extracts (current + past) |
| `manifests/` | Source registry + corpus census JSON |
| `schema/` | Data-dictionary metadata + XSD bundle status |
| `security_samples/` | Tiny malicious fixtures for security tests (synthetic) |
| `ATTRIBUTION.md` | Required attribution |

Bulk official ZIP archives are **not** committed. They are stored under
gitignored `data/lawtrace/raw/` after manual/programmatic download from
DATA.GOV.HK / `resource.data.one.gov.hk`.

## Acquisition

See `manifests/source_registry.jsonl` for URLs, hashes, Terms version, and
download timestamps. Do not scrape HKeL. Do not use unofficial mirrors.
