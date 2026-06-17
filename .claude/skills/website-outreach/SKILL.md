---
name: website-outreach
description: Scrape leads from URLs and generate personalised outreach messages for the website pitch (pre-built website for leads with outdated/broken/no website). Use when user asks to generate outreach messages for website leads, write DMs for design prospects, or craft cold messages around a pre-built website.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch
---

# Website Outreach — Pre-Built Site Pitch

## Goal

Given one or more leads with their URLs and outreach channel, scrape each lead's online presence, extract the strongest proof point and website weakness, then generate a tailored outreach message pitching the pre-built website JP has already made for them.

---

## Input Format

The user provides leads in this format (paste directly in the chat):

```
Lead: Mark Thompson
Website: https://example.com
Google Maps: https://maps.google.com/...
Facebook: https://facebook.com/...
Instagram: https://instagram.com/...
Channel: facebook_dm
---
Lead: Sam Davies
Website: broken
Google Maps: https://maps.google.com/...
Channel: instagram_dm
```

**Rules:**
- Any URL field can be `none` or `broken` if not applicable
- Channel options: `facebook_dm`, `instagram_dm`, `whatsapp`, `email`, `linkedin_dm`
- Process ALL leads before outputting — batch them, then present all messages together

---

## Scraping Process

For each lead, use WebFetch to pull from each URL provided. Extract the following:

### From Google Maps URL
- Business name + owner first name (from reviews responses or "owner" label)
- Trade/category (roofer, plumber, landscaper, etc.)
- Rating (e.g. 4.8) + review count (e.g. 142)
- How long they've been established (from listing or reviews mentioning years)
- Location → city and region (critical for local hook decision)
- Any standout signals (e.g., "responds quickly", "24/7", "family-run", "emergency callouts")
- Notable review themes (mentioned quality, professionalism, speed)

### From Website URL
- Is it working? (If WebFetch fails → "not working")
- Platform/builder (look for `wix.com`, `squarespace.com`, `weebly.com`, `godaddy.com`, `mysite.com`, `jimdo`, `1and1`, `yell.com/biz`, free builders)
- How outdated it looks (old copyright year, old design patterns, no HTTPS)
- Key detail: is it a free subdomain (e.g., `businessname.wixsite.com`) vs a proper domain

### From Facebook Page
- Business name + first name of owner
- Rating + review count
- Location
- Any posts showing dedication (working late, emergencies, weekend jobs)
- How long they've been trading (About section)

### From Instagram
- Business name, handle
- Follower count
- Bio signals (trade, location, contact info)
- Post themes

---

## Observation Hierarchy

When crafting the opening observation, prioritise in this order:

1. **Exceptional reviews** — unusually high count OR perfect/near-perfect rating (e.g., "5.0 across 38 reviews", "400+ reviews across three platforms")
2. **Years/experience** — decades in the trade (e.g., "40 years in the trade")
3. **Dedication signal** — something that shows they go above and beyond (emergency callouts on weekends, late-night responses, etc.)
4. **Growth signal** — impressive growth in short time (e.g., "38 reviews in 3 years")
5. **Niche speciality** — something specific and impressive about what they do
6. **Generic fallback** — only if nothing else stands out: reference their trade and location

**The observation must be specific. Never say "I came across your business" or generic compliments.**

---

## Website Problem Hierarchy

Match the website weakness to their actual situation:

| Situation | Line to use |
|---|---|
| Free builder (Wix/Weebly/Squarespace free plan) | "Your website's on one of those free builders at the moment though" |
| Free subdomain (wixsite.com, myfreesites.com) | "You're on a free subdomain at the moment — doesn't look great when someone Googles you" |
| Not working / 404 / DNS error | "Tried to find your website but it doesn't seem to be working at the moment" |
| Very outdated (pre-2018 design, old copyright) | "Your current website doesn't really reflect that though" or "it's looking a bit outdated" |
| No website found at all | "Couldn't find a website for you anywhere online" |
| Decent site but doesn't match their reputation | "Your website doesn't really do those reviews justice though" |

---

## Message Formula

Follow this structure **exactly** — the examples below are the gold standard:

```
Hi [FirstName], [LOCAL HOOK IF APPLICABLE]

[Specific observation — one or two sentences about something impressive or notable]

[Website weakness — one sentence, tied to the observation as a contrast]

I've [gone ahead and built / built] a [modern / proper] [version / one] for you already, want me to send [it over / the link]?
```

**Local hook** (ONLY if the lead is from Birmingham, Sutton Coldfield, Solihull, Lichfield, Tamworth, Walsall, Wolverhampton, West Bromwich, Coventry, or broadly the West Midlands):
> `I'm JP - based down the road in Sutton Coldfield.`

If the lead is from outside the West Midlands, drop this line entirely — do not replace it with another location hook.

**CTA variants** (pick the most natural):
- `want me to send it over?`
- `want me to send the link?`
- `want me to send the link so you can see it?`
- `want me to send you a quick video walkthrough so you can see it?`

**No first name available:** Use `Hi there,` — do not guess or use the business name as a substitute.

---

## Gold Standard Examples

Use these as the benchmark. Match their structure, length, and tone precisely.

**Example 1 — Years of experience + outdated site:**
> Hi Mark, I'm JP - based down the road in Sutton Coldfield.
> Saw you've been in the trade for over 40 years, that's serious experience.
> Your current website doesn't really reflect that though.
> I've gone ahead and built a modern version for you, want me to send the link so you can see it?

**Example 2 — Perfect reviews + free builder:**
> Hi Matt, I'm JP - based down the road in Sutton Coldfield.
> Saw you've got a perfect 5.0 on Google across 38 reviews in just 3 years (never seen that before, so clearly doing something right.)
> Your website's on one of those free builders at the moment though, which doesn't really do the reviews justice.
> I've built a proper one for you already, want me to send it over?

**Example 3 — Dedication signal + broken site:**
> Hi Sam, I'm JP - based down the road in Sutton Coldfield.
> Saw your reviews and the fact you're out doing emergency boiler repairs on Sunday evenings says a lot.
> Tried to find your website but it doesn't seem to be working at the moment - I've gone ahead and put one together for you.
> Want me to send the link?

**Example 4 — Exceptional review count + outdated site (longer variant):**
> Hi Matt, I'm JP - based in Sutton Coldfield (just down the road).
>
> Saw you've got over 400 top-rated reviews across Google, Facebook and Yell - for a small family-run business that's insanely impressive.
>
> Your website doesn't really do those reviews justice though, it's looking a bit outdated.
>
> When someone's looking for a local lawn service, they'll go with whoever looks most professional online, and with your reputation you should be winning every time.
>
> I've built a proper site for you already, want me to send it over?

Note: The longer variant (Example 4) adds one extra line to reinforce the business case. Use this only when the observation is strong enough to justify it — e.g., exceptional review count or a clear conversion argument.

**Example 5 — Multiple signals stacked + outdated site (no name, outside West Midlands):**
> Hi there,
>
> 30 years in the trade with a 10-year guarantee and a price-beat promise, that's serious experience backed up in writing.
>
> Your website doesn't really reflect that though, it's looking a bit dated now.
>
> I've built a proper one for you already, want me to send you a quick video walkthrough so you can see it?

**Example 6 — Multiple signals stacked + site doesn't do them justice (outside West Midlands):**
> Hi James,
>
> 30+ years in the trade, drone roof inspections, 7 days a week and no call-out charges - there's a lot there for a customer to like.
>
> Your website doesn't really do any of that justice though.
>
> I've built a proper one for you already, want me to send you a quick video walkthrough so you can see it?

Note: When a lead has several strong signals (years + guarantees + standout service features), stack them in a single opening line rather than picking just one. The contrast with the weak website lands harder when there's more to contrast against.

---

## Channel-Specific Adjustments

| Channel | Adjustments |
|---|---|
| `facebook_dm` | Standard formula. Paragraphs separated by a blank line. |
| `instagram_dm` | Shorter — max 4 sentences total. Cut any "extra" middle line. |
| `whatsapp` | Same as facebook_dm. Very casual. |
| `email` | Add subject line: `[FirstName] - quick one` or `your website, [FirstName]`. Can be slightly longer. |
| `linkedin_dm` | More professional tone but still short. Skip trade-specific casual language. |

---

## Tone Rules

- Short. Punchy. Every sentence earns its place.
- Never: "I came across your business", "I noticed you", "just reaching out"
- Never: "seamless", "solution", "innovative", "cutting-edge"
- Always: conversational, like a text from someone local who noticed something
- British English: "proper", "sorted", "send it over"
- Dry humour where it fits (e.g., "never seen that before" as a throwaway)
- Do NOT use forced slang
- Do NOT use short punchy sentence fragments as a stylistic crutch
- One CTA only. No follow-up offer, no alternative ask.

---

## Output Format

For each lead, output:

```
### [Lead Name] — [Channel]

[MESSAGE]

---
**Scraped signals used:**
- Observation: [what you found]
- Website issue: [what you found]
- Local hook: [yes/no — reason]
```

Process all leads in one pass before presenting output.

---

## Edge Cases

- **Can't scrape a URL** (blocked, no content): Note it, use what's available from other URLs. If no data at all, flag for manual research.
- **No first name found**: Ask the user before generating — do not guess.
- **Business has no website at all**: Use "Couldn't find a website for you anywhere online" variant.
- **Reviews are low or unremarkable**: Don't mention them. Find another hook (experience, speciality, dedication signal). Fall back to the website problem itself as the opener if needed.
- **Outside West Midlands**: Drop local hook. No replacement line needed — just start with the observation.
