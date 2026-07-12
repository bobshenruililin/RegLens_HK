# Stage A result

**Result:** PASS WITH LIMITATIONS

## Passed
- Official EN ZIP acquisition for Cap. 614 parent archives (601+) and Cap. 599-family parent archives (301–600 current / 401–600 past).
- Source registry with hashes, Terms v1.2, URLs, sizes.
- Secure ZIP/XML utilities + security tests (13 passed).
- Cap. 614 trimmed fixtures (12 XML versions) committed under `fixtures/lawtrace/cap_614/`.
- Cap. 599-family census over 772 extracted English XML files (gitignored extracts).
- Ranking produced (no showcase selected yet).

## Limitations
- Official HKLM XSD bundle could not be acquired non-interactively (`/file/get?openfile=hklm` returns client-config HTML). Offline XSD validation is **not** claimed.
- zh-Hant archives recorded as metadata-only (Content-Length); not downloaded.
- Cap. 599-family XML not committed (71 MiB extracts remain under `data/lawtrace/extracted/`).

## Safety
- Bulk ZIPs under gitignored `data/lawtrace/raw/`.
- No RegLens domain code modified for Stage A implementation.
