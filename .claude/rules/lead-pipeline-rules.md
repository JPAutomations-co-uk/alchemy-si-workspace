---
paths:
  - ".claude/skills/scrape-leads/**"
  - ".claude/skills/gmaps-leads/**"
  - ".claude/skills/classify-leads/**"
  - ".claude/skills/casualize-names/**"
  - ".claude/skills/lead-pipeline/**"
---

# Lead Pipeline Rules

- Always run pipeline-verifier subagent before uploading leads to any campaign
- Test scrapes (25 leads) before full scrapes — never skip the test
- Classification match rate must be 80%+ before proceeding to full scrape
- Geographic partitioning for large scrapes (1000+): UK uses 4-way split (SE/N/Scotland-Wales/SW)
- Lead data passes between pipeline steps as structured JSON, not prose
- Only deliverable is the Google Sheet URL — all .tmp files are ephemeral
- Enrich emails AFTER classification, not before (saves API calls on rejected leads)
