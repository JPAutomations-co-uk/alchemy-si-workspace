---
paths:
  - ".claude/skills/instagram-content/**"
  - ".claude/skills/youtube-script/**"
  - ".claude/skills/create-ad-creatives/**"
  - ".claude/skills/ai-news-stories/**"
  - ".claude/skills/create-proposal/**"
  - "execution/generate_*.py"
  - "execution/compile_*.py"
---

# Content Generation Rules

- Always use the analysis scratchpad (`<analysis>` tags) before generating any content
- Load client profile and brand voice before generation — never generate with default/generic voice
- Never generate images before the user approves the slide-by-slide breakdown
- Content must match the client's template and brand accent colours
- Proposals must reason against business_context.md — never fabricate pricing, case studies, or testimonials
- Strip all `<analysis>` blocks from final deliverables
- For batch generation, check token balance before starting (don't burn tokens on a run that will fail mid-way)
