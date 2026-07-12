# Stage D — Cap. 599-family candidate matrix

LawTrace output is a transformation of official open data and is not a verified copy.

## Limiters

- Probe max versions/instrument: 40
- Stress max versions: 25
- Changed-pair target: ≥30 if available

## Matrix

| Instrument | Files | Eval versions | @id coverage | Changed | Ambiguous | Recon | Score | Complete share |
|------------|------:|--------------:|-------------:|--------:|----------:|------:|------:|---------------:|
| cap:599G | 101 | 40 | 0.9894 | 148 | 0 | 1.0 | 91.27 | 1.000 |
| cap:599F | 125 | 40 | 0.9867 | 171 | 0 | 1.0 | 89.9 | 0.903 |
| cap:599J | 231 | 40 | 0.9940 | 134 | 0 | 1.0 | 88.09 | 0.949 |

## Selection

- Technical stress-test: **cap:599J**
- Recommended showcase: **cap:599G**
- Same instrument: False
- Stress pass: **True**
- Stress changed pairs: 115
- Stress reconstruction: 1318/1318

### Rationale

- Showcase: cap:599G has the highest composite score (91.27), 100% complete renderability (no nontext metadata), 100% reconstruction, zero ambiguous events. @id coverage 98.94% on the bounded probe reflects genuine additions/removals in the sampled span, not ambiguous identity.
- Stress: cap:599J selected for technical stress: 231 available versions, highest probe @id coverage (99.40%), 100% reconstruction, and 115 changed pairs under the 25-version stress limiter (target ≥30).

Comparisons are algorithm-generated / not human-confirmed gold.

