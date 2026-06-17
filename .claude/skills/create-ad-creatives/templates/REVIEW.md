## Summary
Three of the four templates are clean; two have real issues — a missing CTA placeholder and a logo element that is rendered into an empty container.

## Issues

- **[severity: high]** Correctness (`ig_photo_frame.html`): The `{cta}` placeholder is never used. No CTA button exists anywhere in the HTML. Every other template renders `{cta}` inside a `.cta-btn` element, but this one omits it entirely. If the caller passes a CTA string it will be silently ignored and no button will appear in the output. Suggested fix: add a CTA element inside `.content`, e.g. `<div class="cta-btn">{cta}</div>`, and add the corresponding `.cta-btn` CSS rule.

- **[severity: high]** Correctness (`ig_circle_photo.html`, line 167): The `.logo-bottom` div is empty — `{logo_html}` is never placed inside it. Compare with `ig_corner_photo.html` which correctly renders `{logo_html}` inside `.logo-bottom`. The result is that the bottom-of-frame logo/brand watermark will always be invisible regardless of what `logo_html` resolves to. Suggested fix: change line 167 from `<div class="logo-bottom"></div>` to `<div class="logo-bottom">{logo_html}</div>`.

- **[severity: low]** Correctness (`ig_photo_frame.html`): `{bg_color}` is declared as a CSS variable (`--bg`) but is never consumed by any rule in this template. The body background is set directly to `var(--primary)` and all other surfaces use `var(--primary)` / `var(--secondary)`. This is not a breaking issue but the variable is dead, which is inconsistent with the other three templates where `--bg` is actively used. No action required unless a background-color variant is intended.

## Verdict
NEEDS CHANGES — two high-severity issues (missing CTA output in `ig_photo_frame.html`, empty logo container in `ig_circle_photo.html`) must be fixed before these templates produce correct output.
