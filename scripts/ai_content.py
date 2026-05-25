"""
SEOplant AI Content Engine — LLM-powered content generation.

Produces SEO-optimized articles, pillar pages, and programmatic
content variants using Claude or OpenAI APIs.

Tier: Starter+ (Pro for scale usage)
Credit cost: 3 per article, 10 per pillar page
"""

import os
import sys
from datetime import datetime
from typing import Optional

# Try importing LLM SDKs
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class AIContentGenerator:
    """Generate SEO-optimized content using Claude or GPT.

    Usage:
        gen = AIContentGenerator(provider="claude")
        article = gen.generate_article(
            keyword="best hiking boots for flat feet",
            content_type="blog_post",
            word_count=1500,
        )
    """

    def __init__(self, provider: str = "claude"):
        self.provider = provider
        self._client = None

        if provider == "claude" and HAS_ANTHROPIC:
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            if api_key:
                self._client = Anthropic(api_key=api_key)
        elif provider == "openai" and HAS_OPENAI:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if api_key:
                self._client = OpenAI(api_key=api_key)

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def generate_article(
        self,
        keyword: str,
        content_type: str = "blog_post",
        word_count: int = 1500,
        context: dict = None,
        tone: str = "expert",
        humanize: bool = True,
    ) -> dict:
        """Generate a complete, publish-ready SEO article.

        Args:
            keyword: Primary target keyword
            content_type: blog_post / pillar_page / comparison / review / faq
            word_count: Target word count
            context: Extra context (competitor titles, SERP features, etc.)
            tone: expert / conversational / technical / beginner

        Returns:
            {title, content_markdown, meta_description, word_count, tokens_used}
        """
        if not self.is_available:
            return self._heuristic_article(keyword, content_type, word_count)

        ctx = context or {}
        competitor_titles = ctx.get("competitor_titles", [])
        serp_features = ctx.get("serp_features", [])

        system_prompt = self._build_system_prompt(tone)
        user_prompt = self._build_article_prompt(
            keyword, content_type, word_count, competitor_titles, serp_features
        )

        try:
            if self.provider == "claude":
                resp = self._client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=min(word_count * 3, 8000),
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                raw = resp.content[0].text
                tokens = resp.usage.input_tokens + resp.usage.output_tokens
            else:
                resp = self._client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=min(word_count * 3, 8000),
                )
                raw = resp.choices[0].message.content
                tokens = resp.usage.total_tokens

            result = self._parse_llm_output(raw, tokens)

            if humanize:
                try:
                    from ai_humanizer import AIHumanizer
                    h = AIHumanizer()
                    result["content_markdown"] = h.humanize(
                        result["content_markdown"],
                        keywords=[keyword.split(" in ")[0], keyword],
                        intensity="medium",
                    )
                    result["humanized"] = True
                except ImportError:
                    result["humanized"] = False

            return result

        except Exception as e:
            print(f"  [WARN] LLM generation failed: {e}. Falling back to heuristic.")
            return self._heuristic_article(keyword, content_type, word_count)

    def generate_bulk(
        self,
        keywords: list[dict],
        content_type: str = "blog_post",
        word_count: int = 800,
        max_articles: int = 50,
    ) -> list[dict]:
        """Generate articles for multiple keywords in batch."""
        results = []
        for i, kw in enumerate(keywords[:max_articles]):
            keyword = kw.get("keyword", "") if isinstance(kw, dict) else kw
            article = self.generate_article(
                keyword=keyword,
                content_type=content_type,
                word_count=word_count,
            )
            article["keyword"] = keyword
            results.append(article)
        return results

    # ── Prompt builders ──

    def _build_system_prompt(self, tone: str) -> str:
        tone_map = {
            "expert": "You are an expert SEO content writer with deep domain knowledge. Write authoritatively with data-backed claims.",
            "conversational": "You are a friendly SEO writer. Write in a warm, conversational tone that engages readers.",
            "technical": "You are a technical SEO writer. Be precise, use industry terminology, and provide specific details.",
            "beginner": "You are an SEO writer for beginners. Explain concepts simply with helpful analogies.",
        }
        base = tone_map.get(tone, tone_map["expert"])

        return f"""{base}

Output format (strict):
---
title: [SEO-optimized title, 50-65 chars]
description: [Meta description, 120-155 chars, include primary keyword]
---

[Full article in Markdown with:
- H1 matching the title
- H2/H3 subheadings with related keywords
- Short paragraphs (2-4 sentences)
- Bullet points for scannability
- One FAQ section at the end
- Natural keyword placement (no stuffing)]
"""

    def _build_article_prompt(
        self, keyword: str, content_type: str, word_count: int,
        competitor_titles: list, serp_features: list,
    ) -> str:
        type_desc = {
            "blog_post": "informational blog post",
            "pillar_page": "comprehensive pillar page guide",
            "comparison": "product comparison article",
            "review": "product review",
            "faq": "FAQ page",
        }
        desc = type_desc.get(content_type, "article")

        prompt = f"""Write a {word_count}-word {desc} about "{keyword}".

Target audience: People searching Google for information about {keyword}.
Search intent: {self._infer_intent(keyword)}

"""
        if competitor_titles:
            prompt += f"Top-ranking competitor titles for reference:\n"
            for t in competitor_titles[:5]:
                prompt += f"  - {t}\n"
            prompt += "\nMake your content MORE comprehensive than these.\n"

        if serp_features:
            prompt += f"\nSERP features present: {', '.join(serp_features)}. "
            prompt += "Structure your content to capture these features.\n"

        prompt += "\nInclude 2-3 internal linking suggestions at the end (format: [Link text] -> /suggested-slug/)."
        return prompt

    def _parse_llm_output(self, raw: str, tokens: int) -> dict:
        """Parse LLM output into structured dict."""
        import re

        title = re.search(r'^title:\s*(.+)$', raw, re.M | re.I)
        desc = re.search(r'^description:\s*(.+)$', raw, re.M | re.I)

        # Extract markdown body (after --- separator)
        parts = re.split(r'^---\s*$', raw, maxsplit=2, flags=re.M)
        body = parts[-1].strip() if len(parts) >= 2 else raw

        return {
            "title": title.group(1).strip() if title else f"Complete Guide to {keyword if 'keyword' in dir() else ''}",
            "meta_description": desc.group(1).strip() if desc else "",
            "content_markdown": body,
            "word_count": len(body.split()),
            "tokens_used": tokens,
        }

    def _heuristic_article(self, keyword: str, content_type: str, word_count: int) -> dict:
        """Fallback: template-based article generation (no LLM)."""
        kw_title = keyword.title()

        templates = {
            "blog_post": {
                "title": f"{kw_title}: The Complete Guide for {datetime.now().year}",
                "description": f"Everything you need to know about {keyword}. Expert tips, comparisons, and recommendations for {datetime.now().year}.",
                "sections": [
                    f"## What Is {kw_title}?\n\nUnderstanding {keyword} is essential for making informed decisions...",
                    f"## Why {kw_title} Matters\n\n{kw_title} can make a significant difference in your results...",
                    f"## How to Choose the Right {kw_title}\n\nWhen evaluating {keyword}, consider these key factors...",
                    f"## Common Mistakes to Avoid\n\nMany people overlook important aspects of {keyword}...",
                    f"## FAQ\n\n**Q: What is the best {keyword} for beginners?**\n\nA: The best choice depends on your specific needs...",
                ],
            },
            "comparison": {
                "title": f"{kw_title}: In-Depth Comparison and Review",
                "description": f"Compare the best {keyword} options. Side-by-side features, pricing, and honest reviews for {datetime.now().year}.",
                "sections": [
                    f"## Top {kw_title} Options Compared\n\nWe've evaluated the leading {keyword} solutions...",
                    f"## Feature Comparison Table\n\n| Feature | Option A | Option B | Option C |\n|---------|----------|----------|----------|\n| Price | - | - | - |\n| Rating | - | - | - |",
                    f"## Which {kw_title} Is Right for You?\n\nYour choice depends on budget, experience level, and specific requirements...",
                    f"## FAQ\n\n**Q: Is {keyword} worth the investment?**\n\nA: For most users, yes...",
                ],
            },
        }

        tmpl = templates.get(content_type, templates["blog_post"])
        sections = "\n\n".join(tmpl["sections"])
        body = f"# {tmpl['title']}\n\n{sections}\n\n---\n\n*Generated: {datetime.now().strftime('%Y-%m-%d')} | Heuristic mode — upgrade to Pro for AI-powered content*"

        return {
            "title": tmpl["title"],
            "meta_description": tmpl["description"],
            "content_markdown": body,
            "word_count": len(body.split()),
            "tokens_used": 0,
        }

    def _infer_intent(self, keyword: str) -> str:
        k = keyword.lower()
        if any(w in k for w in ["buy", "price", "cheap", "best", "review", "vs", "compare"]):
            return "Commercial — user is comparing options before purchasing"
        if any(w in k for w in ["how", "what", "why", "when", "guide", "tutorial", "learn"]):
            return "Informational — user wants to learn about this topic"
        if any(w in k for w in ["near me", "in", "london", "nyc", "shop", "store"]):
            return "Local/Transactional — user wants to find or buy locally"
        return "Mixed intent — user may be researching or ready to act"


# ── CLI ──

def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    if len(sys.argv) < 2:
        print("""
SEOplant AI Content Engine

Commands:
  article <keyword>              Generate a blog post
  pillar <keyword>               Generate a pillar page
  bulk <keyword1,keyword2,...>   Generate multiple articles
  compare <product_a> <product_b> Generate a comparison page

Options:
  --type blog_post|pillar|comparison|review
  --words 1500
  --tone expert|conversational|technical|beginner
  --provider claude|openai
        """)
        return

    command = sys.argv[1]
    gen = AIContentGenerator(provider="claude")

    if not gen.is_available:
        print("[WARN] No LLM API key configured. Using heuristic mode.")
        print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY for AI-powered content.\n")

    words = 1500
    tone = "expert"
    ctype = "blog_post"
    for i, arg in enumerate(sys.argv):
        if arg == "--words" and i + 1 < len(sys.argv): words = int(sys.argv[i + 1])
        if arg == "--tone" and i + 1 < len(sys.argv): tone = sys.argv[i + 1]
        if arg == "--type" and i + 1 < len(sys.argv): ctype = sys.argv[i + 1]

    if command == "article":
        kw = sys.argv[2] if len(sys.argv) > 2 else "best hiking boots"
        print(f"Generating {words}-word {ctype} about '{kw}'...")
        result = gen.generate_article(kw, ctype, words, tone=tone)
        print(f"\nTitle: {result['title']}")
        print(f"Words: {result['word_count']}")
        print(f"Tokens: {result.get('tokens_used', 'N/A')}")
        print(f"\n{result['content_markdown'][:500]}...")

    elif command == "bulk":
        kws = sys.argv[2].split(",") if len(sys.argv) > 2 else ["seo tools", "keyword research"]
        kws = [k.strip() for k in kws]
        print(f"Generating {len(kws)} articles...")
        for i, article in enumerate(gen.generate_bulk(
            [{"keyword": k} for k in kws], ctype, words, max_articles=10
        )):
            print(f"  {i+1}. {article['title'][:60]} ({article['word_count']} words)")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
