"""
SEOplant Programmatic SEO Engine — Phase 3.

Template + Dataset → Bulk SEO Pages at Scale.

One keyword becomes 5000 pages. City pages, product variants,
comparison pages, FAQ sections — all generated from templates
with AI-powered content variation and automatic internal linking.

Usage:
    from pseo_engine import PSEOEngine

    engine = PSEOEngine()
    engine.load_dataset("cities.csv")       # or JSON, or AI-generated
    engine.set_templates(["city_guide.md", "hotel_listing.md"])
    result = engine.generate(output_dir="./pages")

    # 500 cities × 2 templates = 1000 pages

Dependencies: none (standard library + optional DataForSEO/LLM)
"""

import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# ===================================================================
# 1. Dataset Loaders
# ===================================================================

def load_dataset_csv(path: str) -> list[dict]:
    """Load a CSV file as a list of row dicts."""
    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k.strip(): v.strip() for k, v in row.items()})
    return rows


def load_dataset_json(path: str) -> list[dict]:
    """Load a JSON array or {data: [...]} file."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                return v
    return []


def load_dataset_ai(keyword: str, template_type: str, count: int = 100) -> list[dict]:
    """Generate a dataset using AI (requires LLM or DataForSEO).

    For example, "best hotels" + "cities" → 100 city records with
    country, population, tourism_data, etc.

    Falls back to a heuristic stub if no AI is available.
    """
    # Try DataForSEO first (keyword suggestions)
    try:
        from dataforseo_client import DataForSEOClient
        client = DataForSEOClient()
        if client.is_configured:
            suggestions = client.keyword_suggestions(
                f"{keyword} {template_type}", limit=count
            )
            return [
                {
                    "keyword": s["keyword"],
                    "search_volume": s.get("search_volume", 0),
                    "cpc": s.get("cpc", 0),
                    "source": "dataforseo",
                }
                for s in suggestions[:count]
            ]
    except Exception:
        pass

    # Heuristic stub
    return [
        {
            "keyword": f"{keyword} {template_type} example {i}",
            "search_volume": 0,
            "source": "heuristic",
        }
        for i in range(1, min(count, 20) + 1)
    ]


# ===================================================================
# 2. Template Engine
# ===================================================================

class PSEOTemplate:
    """A programmatic SEO page template with variable interpolation.

    Variables: {keyword}, {city}, {country}, {search_volume}, etc.
    Also supports: {title_case:keyword}, {upper:city}, {slug:keyword}
    """

    def __init__(self, name: str, template_str: str):
        self.name = name
        self.raw = template_str

    def render(self, variables: dict) -> str:
        """Render the template with variable substitution."""
        result = self.raw
        # Handle {transform:variable} patterns
        for match in re.finditer(r'\{(\w+):(\w+)\}', result):
            transform, var = match.group(1), match.group(2)
            value = str(variables.get(var, ""))
            if transform == "title_case":
                value = value.title()
            elif transform == "upper":
                value = value.upper()
            elif transform == "lower":
                value = value.lower()
            elif transform == "slug":
                value = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip("-")
            result = result.replace(match.group(0), value)

        # Handle {variable} patterns
        for var in set(re.findall(r'\{(\w+)\}', result)):
            value = str(variables.get(var, ""))
            result = result.replace(f"{{{var}}}", value)

        return result


# Pre-built templates for common pSEO use cases
DEFAULT_TEMPLATES = {
    "city_landing": PSEOTemplate("city_landing", """---
title: "{keyword} in {city}, {country} — The Complete Guide"
description: "Discover the best {keyword} in {city}. Expert reviews, pricing, and local tips for {year}."
schema: LocalBusiness
---

# {title_case:keyword} in {city}, {country}

{city} is one of the most popular destinations for {keyword} in {country}.
Whether you're a local or a visitor, finding the right {keyword} can make
all the difference.

## Top {title_case:keyword} in {city}

Our team has researched and tested the best options available.

## Why Choose {city} for {title_case:keyword}?

{city} offers unique advantages for {keyword} enthusiasts.

## Frequently Asked Questions

### What is the best time for {keyword} in {city}?

### How much does {keyword} cost in {city}?

The average price ranges depending on the season and location.

---

*Last updated: {date} | Data sourced from our research team*
"""),

    "product_comparison": PSEOTemplate("product_comparison", """---
title: "{product_a} vs {product_b} — Which {keyword} Is Right for You?"
description: "Compare {product_a} vs {product_b} for {keyword}. Side-by-side features, pricing, and honest review."
schema: Product
---

# {product_a} vs {product_b}: The Ultimate {title_case:keyword} Comparison

Choosing between {product_a} and {product_b} for your {keyword} needs?
We've tested both extensively to help you decide.

## Quick Comparison Table

| Feature | {product_a} | {product_b} |
|---------|-------------|-------------|
| Price | Check Latest | Check Latest |
| Rating | ★★★★★ | ★★★★★ |

## {product_a} — Detailed Review

## {product_b} — Detailed Review

## The Verdict

For most people needing {keyword}, we recommend...

---

*Last updated: {date}*
"""),

    "faq_page": PSEOTemplate("faq_page", """---
title: "{keyword} FAQ — Your Questions Answered ({year})"
description: "Everything you need to know about {keyword}. Expert answers to the most common questions."
schema: FAQPage
---

# {title_case:keyword} — Frequently Asked Questions

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {{
      "@type": "Question",
      "name": "What is {keyword}?",
      "acceptedAnswer": {{
        "@type": "Answer",
        "text": "{keyword} refers to..."
      }}
    }},
    {{
      "@type": "Question",
      "name": "How much does {keyword} cost?",
      "acceptedAnswer": {{
        "@type": "Answer",
        "text": "The cost of {keyword} varies depending on several factors..."
      }}
    }},
    {{
      "@type": "Question",
      "name": "Is {keyword} worth it?",
      "acceptedAnswer": {{
        "@type": "Answer",
        "text": "For the right person, {keyword} is absolutely worth the investment..."
      }}
    }}
  ]
}}
</script>

## What is {keyword}?

## How Much Does {keyword} Cost?

## Is {keyword} Worth It?

## Common {title_case:keyword} Mistakes to Avoid

---

*Last updated: {date}*
"""),

    "review_roundup": PSEOTemplate("review_roundup", """---
title: "Best {keyword} in {year} — Top Picks & Expert Reviews"
description: "We tested the top {keyword} products. See our rankings, pros and cons, and buying guide."
schema: Article
---

# Best {title_case:keyword} of {year}

After {hours} hours of research and testing, here are our top picks for {keyword}.

## Our Top Pick: {top_pick}

## Best Budget Option: {budget_pick}

## Best Premium Option: {premium_pick}

## How We Tested

## Buying Guide: What to Look for in {title_case:keyword}

---

*Last updated: {date} | Affiliate disclosure: We may earn a commission*
"""),
}


# ===================================================================
# 3. Content Variation Engine
# ===================================================================

_CONTENT_VARIANTS = {
    "intro": [
        "Looking for {keyword} in {city}? You've come to the right place.",
        "If you're searching for the best {keyword} in {city}, we've got you covered.",
        "{city} is home to some of the finest {keyword} options available.",
        "Discover why {city} is a top destination for {keyword} enthusiasts.",
    ],
    "conclusion": [
        "Whether you choose {city} or another location, {keyword} is an experience worth having.",
        "Ready to explore {keyword} in {city}? Start planning your journey today.",
        "{city} offers something special for every {keyword} seeker.",
    ],
}


class ContentVariator:
    """Adds variation to pSEO pages to avoid duplicate content penalties.

    Rotates through intro/conclusion variants and can optionally
    use LLM to generate unique paragraph-level variations.
    """

    def __init__(self, seed: int = None):
        import random
        self.rng = random.Random(seed or hash(datetime.now().timestamp()))

    def vary(self, template_type: str, section: str, variables: dict) -> str:
        """Return a varied version of the given section."""
        variants = _CONTENT_VARIANTS.get(section, [])
        if not variants:
            return ""
        chosen = self.rng.choice(variants)
        for var, val in variables.items():
            chosen = chosen.replace(f"{{{var}}}", str(val))
        return chosen

    def generate_paragraph(self, keyword: str, context: str, dfseo_client=None) -> str:
        """Generate a unique paragraph using DataForSEO or heuristic data.

        In production, this would call an LLM (Claude/GPT) for truly unique content.
        For the open-source version, it uses heuristic variation.
        """
        # Heuristic variation: rotate through sentence structures
        structures = [
            f"When it comes to {keyword}, {context} matters more than most people realize.",
            f"Experts agree that {keyword} in the context of {context} requires careful consideration.",
            f"One thing that sets great {keyword} apart is how they handle {context}.",
            f"Don't underestimate the importance of {context} when choosing {keyword}.",
        ]
        idx = hash(f"{keyword}:{context}") % len(structures)
        return structures[idx]


# ===================================================================
# 4. Internal Linking Engine
# ===================================================================

class InternalLinker:
    """Builds internal link graphs between programmatic pages.

    Links related pages (e.g., city pages within same country,
    product comparisons within same category).
    """

    def __init__(self):
        self.pages = []

    def add_page(self, slug: str, title: str, group: str = ""):
        self.pages.append({"slug": slug, "title": title, "group": group})

    def get_links_for(self, current_slug: str, group: str = "", max_links: int = 5) -> list[dict]:
        """Get related pages to link to from a given page."""
        candidates = [
            p for p in self.pages
            if p["slug"] != current_slug
        ]
        # Prioritize same-group pages
        same_group = [p for p in candidates if p["group"] == group]
        other = [p for p in candidates if p["group"] != group]

        selected = (same_group + other)[:max_links]
        return selected

    def generate_links_html(self, current_slug: str, group: str = "", max_links: int = 5) -> str:
        """Generate HTML for internal links section."""
        links = self.get_links_for(current_slug, group, max_links)
        if not links:
            return ""
        items = "\n".join(
            f'- [{p["title"]}](/{p["slug"]}/)'
            for p in links
        )
        return f"""## Related Pages

{items}
"""


# ===================================================================
# 5. Main PSEO Engine
# ===================================================================

class PSEOEngine:
    """Programmatic SEO Engine — the core of SEOplant Phase 3.

    Takes a keyword + dataset + templates → generates hundreds/thousands
    of SEO-optimized pages with content variation and internal linking.
    """

    def __init__(self, output_dir: str = "./pseo_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.templates: dict[str, PSEOTemplate] = {}
        self.dataset: list[dict] = []
        self.variator = ContentVariator()
        self.linker = InternalLinker()
        self.stats = {"total": 0, "generated": 0, "errors": 0, "skipped": 0}

    def load_dataset(self, source: str, dataset_type: str = "csv", keyword: str = "", count: int = 100):
        """Load data from CSV, JSON, or AI generation."""
        if dataset_type == "csv":
            self.dataset = load_dataset_csv(source)
        elif dataset_type == "json":
            self.dataset = load_dataset_json(source)
        elif dataset_type == "ai":
            self.dataset = load_dataset_ai(keyword, source, count)
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")
        self.stats["total"] = len(self.dataset)
        return self

    def add_template(self, name: str, template: PSEOTemplate):
        self.templates[name] = template

    def use_default_templates(self, *names: str):
        """Load pre-built templates by name."""
        for name in names:
            if name in DEFAULT_TEMPLATES:
                self.templates[name] = DEFAULT_TEMPLATES[name]

    def generate(
        self,
        primary_template: str,
        url_pattern: str,
        group_field: str = None,
        extra_vars: dict = None,
        max_pages: int = None,
    ) -> dict:
        """Generate all pages from dataset using the primary template.

        Args:
            primary_template: Name of the template to use
            url_pattern: URL pattern with {vars}, e.g. "hotels/{slug:city}"
            group_field: Dataset field for internal linking groups
            extra_vars: Extra template variables (date, year, brand_name, etc.)
            max_pages: Limit output (for testing)

        Returns:
            Dict with stats and list of generated files
        """
        template = self.templates.get(primary_template)
        if not template:
            return {"error": f"Template '{primary_template}' not found. Add it first."}

        base_vars = extra_vars or {}
        base_vars.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
        base_vars.setdefault("year", str(datetime.now().year))
        base_vars.setdefault("hours", "40")

        generated = []
        pages_dir = self.output_dir / "pages"
        pages_dir.mkdir(exist_ok=True)

        rows = self.dataset[:max_pages] if max_pages else self.dataset

        for i, row in enumerate(rows):
            try:
                # Merge variables
                vars_ = {**base_vars, **row}

                # Generate slug
                slug = url_pattern
                for var, val in vars_.items():
                    slug_val = re.sub(r'[^a-z0-9]+', '-', str(val).lower()).strip("-")
                    slug = slug.replace(f"{{slug:{var}}}", slug_val)
                    slug = slug.replace(f"{{{var}}}", str(val))

                # Render page
                content = template.render(vars_)

                # Add internal links
                group = vars_.get(group_field, "") if group_field else ""
                links = self.linker.generate_links_html(slug, group)
                if links:
                    content += "\n\n" + links

                # Write file
                page_dir = pages_dir / slug
                page_dir.mkdir(parents=True, exist_ok=True)
                (page_dir / "index.md").write_text(content, encoding="utf-8")

                # Register for linking
                title = re.search(r'^# (.+)$', content, re.MULTILINE)
                page_title = title.group(1) if title else slug
                self.linker.add_page(slug, page_title, group)

                generated.append({"slug": slug, "title": page_title, "group": group})
                self.stats["generated"] += 1

            except Exception as e:
                self.stats["errors"] += 1
                print(f"  [ERROR] Row {i}: {e}")

        # Generate index page
        self._generate_index(generated, primary_template)

        self.stats["total"] = len(rows)
        return {
            "stats": self.stats,
            "pages_dir": str(pages_dir),
            "generated": generated,
        }

    def _generate_index(self, pages: list[dict], template_name: str):
        """Generate an index/sitemap page linking to all generated pages."""
        lines = [
            f"# Generated Pages — {template_name}",
            f"*{len(pages)} pages generated on {datetime.now().strftime('%Y-%m-%d')}*",
            "",
        ]
        current_group = ""
        for p in sorted(pages, key=lambda x: (x.get("group", ""), x["slug"])):
            if p.get("group") and p["group"] != current_group:
                current_group = p["group"]
                lines.append(f"\n## {current_group}\n")
            lines.append(f'- [{p["title"]}](/pages/{p["slug"]}/)')

        (self.output_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")

    def generate_sitemap(self, domain: str = "https://example.com") -> str:
        """Generate an XML sitemap for all generated pages."""
        urls = []
        for page_dir in (self.output_dir / "pages").iterdir():
            if page_dir.is_dir():
                slug = page_dir.name
                urls.append(
                    f"  <url>\n"
                    f"    <loc>{domain}/{slug}/</loc>\n"
                    f"    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>\n"
                    f"    <changefreq>monthly</changefreq>\n"
                    f"    <priority>0.7</priority>\n"
                    f"  </url>"
                )

        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls)
            + "\n</urlset>\n"
        )


# ===================================================================
# 6. Bulk Generator (full site integration)
# ===================================================================

def generate_bulk_site(
    keyword: str,
    dataset_path: str,
    dataset_type: str = "csv",
    templates: list[str] = None,
    output_dir: str = "./pseo_site",
    domain: str = "https://example.com",
    extra_vars: dict = None,
) -> dict:
    """One-shot: dataset + keyword → complete programmatic SEO site.

    Args:
        keyword: Primary keyword/niche
        dataset_path: Path to CSV/JSON dataset or AI dataset type
        dataset_type: 'csv', 'json', or 'ai'
        templates: Template names from DEFAULT_TEMPLATES
        output_dir: Output directory
        domain: Site domain for sitemap
        extra_vars: Extra template variables

    Returns:
        Dict with summary of generated pages and sitemap path
    """
    templates = templates or ["city_landing"]
    engine = PSEOEngine(output_dir)

    # Load data
    if dataset_type == "ai":
        engine.load_dataset(dataset_path, "ai", keyword=keyword, count=500)
    else:
        engine.load_dataset(dataset_path, dataset_type)

    # Add templates
    engine.use_default_templates(*templates)

    # Add extras
    base = extra_vars or {}
    base.setdefault("keyword", keyword)
    base.setdefault("top_pick", f"Top Pick for {keyword}")
    base.setdefault("budget_pick", f"Budget {keyword} Choice")
    base.setdefault("premium_pick", f"Premium {keyword} Experience")

    all_generated = []
    for tmpl_name in templates:
        # Derive URL pattern from template name
        url_map = {
            "city_landing": f"{keyword}/{{slug:city}}",
            "product_comparison": f"compare/{{slug:product_a}}-vs-{{slug:product_b}}",
            "faq_page": f"faq/{{slug:keyword}}",
            "review_roundup": f"best/{{slug:keyword}}",
        }
        url = url_map.get(tmpl_name, f"page/{{slug:keyword}}")
        group = "city" if "city" in tmpl_name else "product" if "product" in tmpl_name else ""

        result = engine.generate(
            primary_template=tmpl_name,
            url_pattern=url,
            group_field=group,
            extra_vars=base,
        )
        if "generated" in result:
            all_generated.extend(result["generated"])

    # Sitemap
    sitemap = engine.generate_sitemap(domain)
    (engine.output_dir / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    return {
        "total_pages": engine.stats["generated"],
        "errors": engine.stats["errors"],
        "templates_used": templates,
        "output_dir": str(engine.output_dir),
        "sitemap": str(engine.output_dir / "sitemap.xml"),
    }


# ===================================================================
# CLI Interface
# ===================================================================

def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    if len(sys.argv) < 2:
        print("""
SEOplant Programmatic SEO Engine

Commands:
  generate <keyword> <dataset.csv>     Generate pages from CSV dataset
  ai-generate <keyword> <type>         AI-generate dataset + pages
  templates                            List available templates
  preview <keyword> <template>         Preview template with sample data

Usage:
  python pseo_engine.py generate "best hotels" cities.csv --templates city_landing
  python pseo_engine.py ai-generate "best hiking boots" cities --count 500
  python pseo_engine.py templates
  python pseo_engine.py preview "best hotels" city_landing
        """)
        return

    command = sys.argv[1]

    if command == "templates":
        print("Available templates:\n")
        for name, tmpl in DEFAULT_TEMPLATES.items():
            print(f"  {name}")
            print(f"    Variables: {', '.join(list(set(re.findall(r'\{(\w+)', tmpl.raw)))[:10])}")
            print()

    elif command == "preview":
        keyword = sys.argv[2] if len(sys.argv) > 2 else "best hotels"
        tmpl_name = sys.argv[3] if len(sys.argv) > 3 else "city_landing"
        tmpl = DEFAULT_TEMPLATES.get(tmpl_name)
        if not tmpl:
            print(f"Template not found: {tmpl_name}")
            return
        sample = {"keyword": keyword, "city": "London", "country": "UK",
                  "year": str(datetime.now().year), "date": datetime.now().strftime("%Y-%m-%d"),
                  "top_pick": "Top Pick", "budget_pick": "Budget Pick",
                  "premium_pick": "Premium Pick", "hours": "40",
                  "product_a": "Product A", "product_b": "Product B"}
        print(tmpl.render(sample))

    elif command == "generate":
        keyword = sys.argv[2] if len(sys.argv) > 2 else "best hotels"
        dataset = sys.argv[3] if len(sys.argv) > 3 else ""

        templates = ["city_landing"]
        output = "./pseo_output"
        for i, arg in enumerate(sys.argv):
            if arg == "--templates" and i + 1 < len(sys.argv):
                templates = sys.argv[i + 1].split(",")
            if arg == "--output" and i + 1 < len(sys.argv):
                output = sys.argv[i + 1]

        if not dataset:
            print("ERROR: Dataset CSV/JSON path required")
            return

        result = generate_bulk_site(
            keyword=keyword,
            dataset_path=dataset,
            dataset_type="csv" if dataset.endswith(".csv") else "json",
            templates=templates,
            output_dir=output,
        )
        print(f"Generated {result['total_pages']} pages ({result['errors']} errors)")
        print(f"Output: {result['output_dir']}")
        print(f"Sitemap: {result['sitemap']}")

    elif command == "ai-generate":
        keyword = sys.argv[2] if len(sys.argv) > 2 else "best hotels"
        dataset_type = sys.argv[3] if len(sys.argv) > 3 else "cities"
        count = 100
        for i, arg in enumerate(sys.argv):
            if arg == "--count" and i + 1 < len(sys.argv):
                count = int(sys.argv[i + 1])

        print(f"Generating {count} {dataset_type} pages for '{keyword}'...")
        engine = PSEOEngine(f"./pseo_{keyword.replace(' ', '-')}")
        engine.load_dataset(dataset_type, "ai", keyword=keyword, count=count)

        # Determine best template based on dataset type
        template_map = {
            "cities": "city_landing",
            "products": "product_comparison",
            "faq": "faq_page",
            "reviews": "review_roundup",
        }
        tmpl = template_map.get(dataset_type, "city_landing")
        engine.use_default_templates(tmpl)

        result = engine.generate(
            primary_template=tmpl,
            url_pattern=f"{keyword}/{{slug:keyword}}",
        )
        print(f"Generated {engine.stats['generated']} pages")
        print(f"Output: {engine.output_dir}")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
