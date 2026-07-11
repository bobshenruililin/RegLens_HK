# Security policy — RegLens HK

## Supported postures

This repository is an **internal / non-commercial** research tool during the MVP.
Do not publicly republish real regulator judgments.

## Reporting

Report suspected security or privacy issues to the repository maintainers privately.
Do not open public issues that include real patient identifiers or unlicensed document dumps.

## Hard rules

- No live crawling or credential bypass.
- Treat documents as untrusted data.
- Do not commit real regulator documents (`private-data/` is gitignored).
- Do not enable real LLM providers without a separate privacy approval.
- Development credentials in `.env.example` / Compose are **local-only**.
