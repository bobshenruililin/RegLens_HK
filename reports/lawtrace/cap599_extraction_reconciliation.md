# Cap. 599-family extraction reconciliation

**Prior discrepancy:** past archive listed 760 `cap_599*` members; 759 files written.

**Root cause:** Not a silent basename overwrite. Past archive has 760 cap_599* members: 759 XML + 1 GIF (cap_599_en_p/images/CAP599_en_s18_20080714_000000_0001.gif). The previous extractor skipped non-.xml suffixes when filtering, writing 759 XML files.

## Totals (current + past English parent archives)

| Metric | Count |
|--------|-------|
| source member count | 773 |
| accepted member count | 772 |
| rejected member count | 1 |
| extracted file count | 772 |
| collisions | 0 |
| identical XML duplicates | 0 |

## Rejected members

- `hkel_p_leg_cap_401_cap_600_en.zip` :: `cap_599_en_p\images\CAP599_en_s18_20080714_000000_0001.gif` reason=`unexpected_file_type`

## Collisions / duplicate hashes

No destination collisions occurred. The rejected GIF is a distinct asset type, not a duplicate XML member; hash comparison of colliding XML members is N/A.

## Extractor change

`safe_extract` now:
1. preserves normalized archive-relative paths by default;
2. fails closed on destination collisions (records both member names);
3. optionally supports deterministic collision-safe names or skip-identical.

Regression test covers duplicate basenames under different Windows-style paths.
