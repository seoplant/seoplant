---
name: seoplant
description: |
  End-to-end SEO website generation methodology. 5 phases: Competitor Intelligence →
  SEO/GEO Strategy → Design Intelligence → Site Generation → Deployment.
version: "4.0"
author: seoplant
tags: [seo, website, programmatic-seo, geo, design, deployment]
---

# SEOplant — AI SEO Website Factory

## Overview

This document describes a complete pipeline for generating SEO-optimized websites programmatically. It takes a keyword or niche as input and produces a deployed, ranking-optimized website as output.

The methodology is platform-agnostic. You can implement it with any tech stack, any AI agent, and any deployment target.

## Core Principles

1. **File-based state** — every phase produces artifacts (`.md`, `.yaml`, `.json`) that feed the next phase. Any agent can resume from any checkpoint.
2. **Fallback chains** — every tool has alternatives. If one data source fails, the next takes over automatically.
3. **SEO-first architecture** — design and content decisions flow from the SEO strategy, not the other way around.

---

## Phase 0: Requirement Clarification

**Goal**: Define exactly what to build before building anything.

**Steps**:
1. Parse the user's keyword and intent
2. Clarify: site type, target languages, markets, optional modules
3. Set defaults for anything unspecified

**Output**: Project brief document

---

## Phase 1: Competitor Intelligence

**Goal**: Understand the competitive landscape.

**Process**:
1. **Discover competitors** — search for top-ranking sites in the target niche using multiple search APIs with automatic fallback
2. **Crawl competitors** — fetch and extract content from each competitor's website
3. **Analyze SEO signals**:
   - Title tag length and keyword placement
   - Meta description quality
   - Heading hierarchy (H1/H2/H3)
   - Content depth (word count, media density)
   - Schema.org structured data types
   - Internal linking structure
   - Image alt text coverage
   - Technical signals (sitemap, robots.txt)
4. **Generate SWOT report** — strengths, weaknesses, opportunities, threats for each competitor

**Output**: Competitor intelligence report with gap analysis

**Fallback strategy**: If primary search API is rate-limited, automatically fail over to backup engines.

---

## Phase 2: SEO/GEO Strategy

**Goal**: Turn research into an actionable content plan.

**Process**:
1. **Expand keywords** — generate long-tail variations using modifier templates (informational, commercial, transactional, temporal, geo-targeted)
2. **Enrich with data** — when available, overlay real search volume, keyword difficulty, CPC, and search intent
3. **Cluster by topic** — group keywords by search intent into topic clusters, each with a pillar page and supporting content
4. **Assess difficulty** — score each keyword on competition level, prioritizing quick wins
5. **Build content calendar** — 6-month phased publishing plan:
   - Months 1-2: Foundation (pillar pages + low-difficulty targets)
   - Months 3-4: Growth (supporting content + medium difficulty)
   - Months 5-6: Authority (harder targets + link building)
6. **Generate GEO config** — AI search engine optimization:
   - Crawler hints for LLM discovery
   - Schema.org templates (WebSite, Organization, Article, FAQ, Breadcrumb)
   - Structured data for AI citation optimization

**Output**: Complete SEO/GEO plan with keyword clusters, content calendar, and structured data templates

---

## Phase 3: Design Intelligence

**Goal**: Extract design patterns from winning sites and create an original system.

**Process**:
1. **Search for inspiration** — scan design galleries and live websites in the target niche
2. **Extract design tokens**:
   - Color palette (primary, secondary, accent, backgrounds)
   - Typography (heading font, body font, type scale)
   - Spacing and layout patterns
   - Component patterns (navigation, hero, cards, footer)
   - CSS custom properties and gradients
3. **Build design library** — store and index extracted tokens for reuse
4. **Fuse designs** — combine selected design systems into a unified, original system
5. **Generate design document** — standardized format with YAML frontmatter and visual reference

**Output**: Design system document with color palette, typography scale, spacing, and component library

---

## Phase 4: Site Generation

**Goal**: Generate an SEO-optimized static website from the strategy and design system.

**Process**:
1. **Initialize project** — scaffold a static site project with the chosen framework
2. **Apply design tokens** — generate global CSS from the design document
3. **Build layout system**:
   - Base layout with SEO metadata injection
   - Responsive navigation component
   - Footer with sitemap links
4. **Create SEO components**:
   - Dynamic SEO head (title, meta, Open Graph, Twitter cards)
   - Schema.org markup (JSON-LD, auto-generated per page type)
5. **Generate page structure**:
   - Homepage (pillar)
   - Category/topic pages
   - Blog/article pages
   - About, contact, and EEAT authority pages
6. **Configure i18n** — multi-language routing with independent keyword systems per language
7. **Wire optional modules** — CMS backend, analytics, maps, e-commerce

**Output**: Complete, buildable static site project

**Key principle**: Every generated page is standard, exportable code. No proprietary format. No lock-in.

---

## Phase 5: Deployment

**Goal**: One-command deployment to production.

**Process**:
1. **Build** — compile the static site to optimized output
2. **Configure web server** — generate server config with compression, caching, security headers
3. **Provision SSL** — automatic certificate issuance and renewal
4. **Deploy** — push to target (user's own server, or cloud platform)
5. **Verify** — check that the site is live and responding
6. **Optional services** — deploy CMS, analytics, or e-commerce containers

**Deployment targets**:
- **BYOV (Bring Your Own VPS)** — SSH push to customer's server. No platform dependency.
- **Cloud platforms** — one-click deploy to static hosting services
- **Manual** — generate all config files for self-service deployment

**Output**: Live, HTTPS-enabled website

---

## Post-Launch: Monitoring & Optimization

Beyond the 5 phases, a complete system should include:

1. **Rank monitoring** — track keyword positions over time
2. **Content decay detection** — identify pages losing rankings
3. **Automatic refresh** — regenerate underperforming content
4. **Keyword expansion** — discover new opportunities as the site matures
5. **Cannibalization detection** — identify and fix competing pages

---

## Implementation Notes

### Data Sources

The pipeline works with multiple tiers of data quality:

| Tier | Description | When to Use |
|------|------------|-------------|
| **Heuristic** | Pattern-based estimates, no API needed | Prototyping, offline use |
| **Real-time** | Live search volume, difficulty, CPC | Production SEO |
| **AI-augmented** | LLM-powered strategy and content | Premium/enterprise |

### Error Handling

Every phase should handle failures gracefully:
- API rate limits → automatic fallback to next engine
- Network errors → retry with exponential backoff
- Missing data → degrade to heuristic estimates
- Partial failures → save progress and allow resume

### Security

- Deployment agent code should be auditable (open source preferred)
- API keys stored as environment variables, never in code
- Generated sites run on user's own infrastructure

---

## Related Resources

- [seoplant.io](https://seoplant.io) — Production platform with real-time data, AI content, and managed dashboard
- [github.com/seoplant](https://github.com/seoplant) — Organization
