# Blog Publish Skill — Empowered Fitness UK

**Trigger:** User pastes a raw blog draft and says "publish this blog" or "run /blog-publish"

**Project path:** `/Users/jp/VS Code Workspace/empowered-fitness/`

---

## What This Skill Does

Takes a raw blog draft written by H. Regan (Empowered Fitness UK), SEO-optimises the structure and metadata **without changing her voice**, generates all required Next.js files, updates the post registry, and outputs two Grok image prompts.

---

## Step 1 — Read the Draft

Accept the draft as pasted text. If no draft is pasted, ask:
> "Please paste your blog draft — I'll take care of the rest."

---

## Step 2 — Analyse the Draft

Before generating anything, think through the following in `<analysis>` tags (strip from final output):

- **Primary keyword:** what is this post fundamentally about? Find the 1–2 word phrase a woman in her target audience would Google. Examples: "exercise during menopause", "lower back pain exercises", "how to lose weight without dieting UK"
- **Secondary keywords:** 3–5 related phrases that belong in the same post
- **Target audience:** which of her audiences does this serve? (menopause, rehab, weight loss, beginners, busy women)
- **Her voice markers:** note any phrases, sentence structures, or recurring patterns that are distinctly hers — these must survive the SEO pass unchanged
- **Missing structure:** what H2 headings does the post need that aren't there? What's the logical flow?
- **FAQ candidates:** 2–3 questions a reader would ask after reading this post

---

## Step 3 — SEO Optimise

### Rules — what you CAN change:
- Rewrite or improve the H1 title (keyword-first, under 65 chars, still natural and her style)
- Add, rename, or reorder H2 subheadings to improve semantic coverage
- Add a FAQ section at the end (2–3 questions) drawn from the post content
- Add a one-line intro hook if the opening is weak (but it must sound like her)
- Add location signal once naturally ("based in Sutton Coldfield", "across the Midlands") if not already present

### Rules — what you CANNOT change:
- Her sentences — do not rewrite what she wrote, only structure around it
- Her tone — direct, British, no fluff, occasionally blunt, conversational
- Her facts, numbers, or specific claims
- Her examples or client anecdotes

### Output of this step:
Show the optimised post copy in a code block (markdown format) for JP to review before any files are written. Label it:
```
## Optimised Copy (review before publishing)
```
Wait for JP to say "looks good" or request changes before proceeding to Step 4.

---

## Step 4 — Generate Metadata

Generate the following. Show it for review alongside the copy:

```
Slug:             [kebab-case, keyword-rich, under 60 chars]
SEO Title:        [keyword first · under 60 chars · natural, not stuffed]
Meta Description: [150–160 chars · includes primary keyword · ends with a soft hook or benefit]
Tag:              [one of: Women's Health / Training / Nutrition / Rehabilitation / Motivation]
Read Time:        [estimate: 200 words/min, round up to nearest minute]
Publish Date:     [today's date in YYYY-MM-DD]
```

---

## Step 5 — Write the Files

After JP approves the copy and metadata, write **two files** and **update one**:

### File 1: `app/blog/[slug]/page.tsx`

```tsx
import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

export const metadata: Metadata = {
  title: "[SEO Title] | Empowered Fitness UK",
  description: "[Meta Description]",
  keywords: ["[keyword1]", "[keyword2]", "[keyword3]"],
  alternates: {
    canonical: "https://www.empoweredfitnessuk.com/blog/[slug]",
  },
  openGraph: {
    title: "[SEO Title]",
    description: "[Meta Description]",
    url: "https://www.empoweredfitnessuk.com/blog/[slug]",
    type: "article",
    publishedTime: "[YYYY-MM-DDT00:00:00Z]",
    authors: ["H. Regan"],
    images: [{ url: "[coverImage URL]", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "[SEO Title]",
    description: "[Meta Description]",
    images: ["[coverImage URL]"],
  },
};

export default function BlogPost() {
  return (
    <main className="min-h-screen bg-background-primary">

      {/* Hero image */}
      <div className="relative w-full h-[40vh] md:h-[55vh] overflow-hidden">
        <Image
          src="[heroImage URL]"
          alt="[descriptive alt text]"
          fill
          className="object-cover object-center"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background-primary/20 via-transparent to-background-primary/80" />
      </div>

      {/* Article */}
      <article className="max-w-3xl mx-auto px-5 pt-10 md:pt-16 pb-20 md:pb-32">

        {/* Back link */}
        <Link
          href="/blog"
          className="inline-flex items-center gap-2 text-sm text-text-tertiary hover:text-accent transition-colors mb-8 font-medium"
        >
          <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2}>
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          All posts
        </Link>

        {/* Post header */}
        <header className="mb-10 md:mb-14">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-accent bg-accent/[0.06] px-3 py-1 rounded-full border border-accent/10">
              [Tag]
            </span>
            <span className="text-[12px] text-text-tertiary font-medium">[Read Time]</span>
            <span className="text-text-tertiary/40">·</span>
            <span className="text-[12px] text-text-tertiary font-medium">[Formatted Date e.g. 21 Apr 2026]</span>
          </div>

          <h1 className="text-[28px] md:text-5xl font-space-grotesk font-bold text-text-primary leading-tight mb-6">
            [Full Display Title]
          </h1>

          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-accent to-[#E8B4A2] flex items-center justify-center text-white font-bold text-sm">
              H
            </div>
            <div>
              <p className="text-sm font-semibold text-text-primary font-space-grotesk">H. Regan</p>
              <p className="text-xs text-text-tertiary">Level 4 PT · Empowered Fitness UK</p>
            </div>
          </div>
        </header>

        {/* Post body */}
        <div className="prose prose-lg max-w-none
          prose-headings:font-space-grotesk prose-headings:text-text-primary prose-headings:font-bold
          prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4
          prose-h3:text-xl prose-h3:mt-8 prose-h3:mb-3
          prose-p:text-text-secondary prose-p:leading-relaxed prose-p:text-base
          prose-strong:text-text-primary prose-strong:font-semibold
          prose-a:text-accent prose-a:no-underline hover:prose-a:underline
          prose-ul:text-text-secondary prose-li:marker:text-accent
          prose-blockquote:border-l-accent prose-blockquote:text-text-secondary prose-blockquote:italic
        ">
          {/* ── POST CONTENT STARTS HERE ── */}

          [PASTE OPTIMISED CONTENT AS JSX HERE]

          {/* ── POST CONTENT ENDS HERE ── */}

          {/* FAQ */}
          <h2>Frequently Asked Questions</h2>

          [FAQ ITEMS AS JSX — <h3> question, <p> answer]

        </div>

        {/* CTA */}
        <div className="mt-16 md:mt-20 p-7 md:p-10 bg-background-secondary rounded-2xl border border-accent/10 text-center">
          <h3 className="text-xl md:text-2xl font-space-grotesk font-bold text-text-primary mb-3">
            Ready to get started?
          </h3>
          <p className="text-text-secondary text-sm md:text-base mb-6 max-w-sm mx-auto leading-relaxed">
            Free consultation. No hard sell. Just a conversation about what would actually work for you.
          </p>
          <a
            href="mailto:info@empoweredfitnessuk.com"
            className="inline-flex items-center gap-2 bg-accent text-white font-bold rounded-full px-7 py-3.5 text-sm hover:bg-accent-hover transition-colors shadow-accent-glow"
          >
            Book a Free Consultation
          </a>
        </div>

      </article>

      {/* JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Article",
            headline: "[SEO Title]",
            description: "[Meta Description]",
            datePublished: "[YYYY-MM-DDT00:00:00Z]",
            dateModified: "[YYYY-MM-DDT00:00:00Z]",
            author: {
              "@type": "Person",
              name: "H. Regan",
              url: "https://www.empoweredfitnessuk.com",
            },
            publisher: {
              "@type": "Organization",
              name: "Empowered Fitness UK",
              url: "https://www.empoweredfitnessuk.com",
            },
            image: "[coverImage URL]",
            keywords: "[keyword1], [keyword2], [keyword3]",
            mainEntityOfPage: {
              "@type": "WebPage",
              "@id": "https://www.empoweredfitnessuk.com/blog/[slug]",
            },
          }),
        }}
      />

      {/* FAQPage schema */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            mainEntity: [
              {
                "@type": "Question",
                name: "[FAQ Question 1]",
                acceptedAnswer: { "@type": "Answer", text: "[FAQ Answer 1]" },
              },
              {
                "@type": "Question",
                name: "[FAQ Question 2]",
                acceptedAnswer: { "@type": "Answer", text: "[FAQ Answer 2]" },
              },
            ],
          }),
        }}
      />

    </main>
  );
}
```

### File 2: Update `lib/blog.ts`

Add a new entry to the `allPosts` array (newest first):

```typescript
{
  slug: "[slug]",
  title: "[Full display title]",
  seoTitle: "[SEO title]",
  metaDescription: "[Meta description]",
  excerpt: "[1–2 sentence excerpt for the listing card]",
  tag: "[Tag]",
  publishDate: "[YYYY-MM-DD]",
  readTime: "[X min read]",
  coverImage: "[Unsplash URL — chosen based on post topic, see Grok prompts for the ideal image]",
  keywords: ["[kw1]", "[kw2]", "[kw3]"],
  author: "H. Regan",
},
```

**For `coverImage`:** Use a relevant Unsplash URL as a temporary placeholder. The Grok prompt (Step 6) gives JP the exact image to generate and swap in.

---

## Step 6 — Generate Grok Image Prompts

Output two prompts, clearly labelled.

### Prompt 1 — Blog Cover / OG Image (1200×630, 16:9)
Used on the listing card, social share preview, and OG image.

Format:
```
Cinematic, natural-light photography. [Specific scene directly relevant to the post topic — e.g. "a woman in her 50s doing a Romanian deadlift in a bright home gym, coach visible in background"]. Warm, neutral colour palette — cream, soft blush, natural wood tones. No text. No logos. No stock-photo poses. Shot on 35mm, shallow depth of field. Aspect ratio 16:9.
```

### Prompt 2 — Post Hero Image (1600×900, landscape)
Used as the full-width image at the top of the post page. Can be the same scene as the cover or a companion shot.

Format:
```
Wide cinematic shot. [Specific scene — slightly wider/more environmental than the cover]. Same warm palette. Hero image feel — spacious, aspirational, real. No text. No logos. Aspect ratio 16:9, landscape.
```

---

## Step 7 — Publish Checklist

After files are written, output this checklist for JP:

```
✅ Files written:
   app/blog/[slug]/page.tsx
   lib/blog.ts updated

📋 Before going live:
   [ ] Replace coverImage URL in lib/blog.ts with generated Grok image
   [ ] Replace heroImage URL in page.tsx with generated Grok image
   [ ] Commit and push (Vercel deploys automatically)
   [ ] Submit URL to Google Search Console → Request Indexing
   [ ] Post LinkedIn + Instagram (see SEO Master Workflow)
```

---

## Tone Reference — H. Regan's Voice

When writing the intro hook or FAQ answers, match this style:

- Direct and no-nonsense. Never preachy.
- British English (programme not program, colour not color, etc.)
- Short sentences when making a point. Longer ones for context.
- Self-aware and occasionally wry — not a sales pitch
- Talks to the reader like a friend who happens to be a professional
- Proof over claims: names real situations, real changes, real timelines
- **Never uses:** "amazing journey", "transform your life", "unlock your potential", "game-changer", "holistic"
- **Does use:** "actually works", "proper", "straightforward", "real", "no nonsense"

---

## Prose Tailwind Plugin Dependency

The post template uses Tailwind Typography (`prose` classes). If not yet installed:

```bash
cd empowered-fitness
npm install @tailwindcss/typography
```

Then add to `tailwind.config.ts`:
```typescript
plugins: [require('@tailwindcss/typography')],
```
