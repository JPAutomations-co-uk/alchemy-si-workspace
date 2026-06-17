---
name: product-launch
description: Plan and execute a SaaS product launch — Product Hunt, Hacker News, Reddit, Twitter/X, newsletter, and email. Generates all launch assets, copy, and a day-by-day execution plan. Use when asked to launch a product, prepare for Product Hunt, plan a launch, or create launch assets.
allowed-tools: Bash, Read, Write, WebFetch, WebSearch
---

# Product Launch

Full launch playbook for a SaaS product. Covers pre-launch, launch day, and post-launch across Product Hunt, Hacker News, Reddit, Twitter/X, newsletters, email, and community.

## When to Use

- Planning a Product Hunt launch
- Generating launch copy (taglines, descriptions, maker comments, tweets)
- Building a launch waitlist strategy
- Planning a "Show HN" post
- Coordinating a multi-channel launch day

---

## Input

Gather from user:
- Product name and URL
- One-sentence description
- Target ICP (who it's for)
- Primary pain it solves
- Key differentiator vs existing tools
- Launch date / timeline
- Existing audience (none / small newsletter / social following / community)
- Maker profiles on Product Hunt (need these for the launch)

---

## Launch Strategy Selection

| Audience size | Recommended strategy |
|---|---|
| No audience | HN "Show HN" first → PH 4-6 weeks later |
| Small newsletter (<1k) | Email blast + HN + PH same week |
| Social following (>2k) | Twitter launch + PH + HN |
| Existing community | Community first → PH for amplification |

---

## Product Hunt Launch

### What Makes a PH Launch Win

1. **Launch on Tuesday–Thursday** — higher traffic. Avoid Monday and Friday.
2. **Launch at 12:01 AM Pacific** — maximises 24-hour window
3. **First comment from maker** — post immediately after launch with your story
4. **Upvote early** — the algorithm weights early velocity heavily
5. **Notify your list in batches** — don't send one blast at 12:01; stagger it
6. **Reply to EVERY comment** — same-day engagement signals activity to the algorithm
7. **No buying upvotes** — PH removes them and can ban the product

### PH Assets to Generate

**Tagline:** Under 60 characters. Problem-solution in one line. No verbs like "lets you" or "helps you".
- Format: `[Outcome] for [ICP]` or `[Do X] without [pain]`

**Description (260 chars):**
- What it does → who it's for → why it's different
- Include the core use case, not a feature list

**Maker Comment (first comment after launch):**
```
Hey PH! I'm [Name], maker of [Product].

[1-2 sentences: what problem you saw, why you built this]

[What [Product] does — specific, concrete]

[Who it's for — be specific: "solo founders running outbound", not "small businesses"]

[One specific differentiator]

[Ask for feedback — makes people feel invited to engage]

[CTA: where to sign up / try it]

Thanks for any upvotes, comments, or questions — I'll be here all day 🙏
```

**Gallery images (5 recommended):**
- Slide 1: Hero — product name + tagline on clean background
- Slide 2: Core workflow — before/after or key screen
- Slide 3: Feature highlight 1 (most impactful)
- Slide 4: Feature highlight 2
- Slide 5: Social proof or metric

### PH Outreach Templates

**Personal network message:**
```
Hey [Name] — launching [Product] on Product Hunt today. 
It [one-line description].

If you've ever [pain point], it might be useful.

Would mean a lot if you'd check it out: [PH link]

No obligation at all — just a quick look and upvote if you like it.
```

**Community message:**
```
Just launched [Product] on Product Hunt — built it because [specific reason].

It [does X] for [Y]. If that's a problem you face, I'd love your feedback.

[PH link]
```

---

## Hacker News "Show HN"

### Format
```
Show HN: [Product Name] – [one-line description, plain English, no marketing]
```

Good examples:
- "Show HN: Postmark – Transactional email that actually delivers"
- "Show HN: Linear – Issue tracker that doesn't get in your way"

Bad:
- "Show HN: Revolutionary AI platform that transforms your workflow"

### Post Body (keep under 300 words)
```
[Why you built it — specific story, not mission statement]

[What it does — concrete: "You paste a URL, it scrapes X, returns Y"]

[Technical stack — HN appreciates this]

[What feedback you're looking for — specific: pricing, UX, missing features]

[Current state: alpha / beta / launched / paying customers]

[Link]
```

**Rules for HN:**
- Don't ask for upvotes — will be downvoted
- Engage every comment immediately
- Accept criticism graciously (don't defend; ask follow-up questions)
- Be a real person, not a marketer

---

## Twitter/X Launch Thread

**Thread structure:**
```
Tweet 1 (hook — the announcement):
After [timeframe] of building, [Product] is live.

[One specific outcome it delivers]

[Link]

🧵

Tweet 2 (problem):
[The exact painful situation your ICP is in]
[Make it feel real and specific]

Tweet 3 (solution):
[Product] does [X] so you don't have to [Y]
[Key workflow in 2-3 steps]

Tweet 4 (proof):
[Early result / user quote / metric]
"[Direct quote if possible]"

Tweet 5 (how to get it):
Starting today, [Product] is [free / $X/month / free tier + paid]
[Link] ← try it

[Ask: what would you use this for?]
```

---

## Launch Email to List

**Subject options (A/B these):**
- `[Product] is live — here's what we built`
- `You asked for X. We built it.`
- `The thing I've been building for [X months]`

**Email body:**
```
[Name],

Today's the day — [Product] is live.

[2-sentence problem statement — make the reader nod]

[What [Product] does, in plain English. 2-3 sentences, no jargon]

[One specific thing that makes it different]

[CTA button: "Try [Product] free"]

If you try it, I'd genuinely love to hear what you think — 
just reply to this email.

[Signature]
```

---

## Pre-Launch Waitlist Strategy

If building a waitlist before launch:

1. **Landing page** — headline + sub + email capture. Nothing else needed.
2. **Referral mechanic** — "Share your link to move up the queue" (reduces CPL)
3. **Content flywheel** — post build-in-public updates weekly to keep list warm
4. **Waitlist email sequence** (see `saas-email-sequences` skill for detail):
   - Day 0: Confirmation + what's coming
   - Day 7: Behind-the-scenes update
   - Day 14: Early access preview / screenshot
   - Launch day: "You're in"

---

## Launch Day Schedule

```
12:01 AM PT  — Publish PH listing
12:05 AM PT  — Post maker comment
12:15 AM PT  — Send first email batch (close network)
08:00 AM PT  — Twitter/X launch thread
09:00 AM PT  — Second email batch (full list)
10:00 AM PT  — Post "Show HN" on Hacker News
12:00 PM PT  — Mid-day update tweet (share any early traction)
03:00 PM PT  — Third email batch (cold/newsletter list)
06:00 PM PT  — Evening update (thank early supporters, address top questions)
```

---

## Post-Launch

Within 48 hours:
- Reply to every PH comment
- DM everyone who upvoted and left a comment (thank them + ask for feedback)
- Write a post-launch retrospective (for Twitter/blog) — what worked, what didn't

Week 1:
- Onboard every early user personally if < 100 signups
- Capture quotes for testimonials
- Fix the top 3 complaints from launch day feedback
- Update landing page with any new social proof
