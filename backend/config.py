"""
SEOplant Backend — FastAPI application configuration.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

# Server
HOST = os.getenv("SEOPLANT_HOST", "0.0.0.0")
PORT = int(os.getenv("SEOPLANT_PORT", "8800"))
DEBUG = os.getenv("SEOPLANT_DEBUG", "true").lower() == "true"
SECRET_KEY = os.getenv("SEOPLANT_SECRET", "change-me-in-production-use-a-random-64-char-string")

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BACKEND_DIR / 'seoplant.db'}"
)

# JWT
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_STARTER = os.getenv("STRIPE_PRICE_STARTER", "price_starter_monthly")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "price_pro_monthly")
STRIPE_PRICE_AGENCY = os.getenv("STRIPE_PRICE_AGENCY", "price_agency_monthly")

# DataForSEO
DATAFORSEO_EMAIL = os.getenv("DATAFORSEO_EMAIL", "")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD", "")

# Claude / LLM API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude")  # claude / openai

# Credit costs
CREDIT_COSTS = {
    "competitor_analysis": 5,
    "seo_plan": 10,
    "site_generation": 20,
    "programmatic_page": 1,
    "deploy": 5,
    "keyword_research": 2,
    "ai_content_article": 3,     # per 500-word article
    "ai_content_pillar": 10,      # per 2000-word pillar page
    "rank_check": 1,              # per keyword check
}

# ── Tier Configuration ──

TIERS = {
    "free": {
        "name": "Free",
        "price": 0,
        "credits_monthly": 100,
        "max_projects": 1,
        "max_pseo_pages": 0,           # no pSEO
        "ai_content": False,            # no AI content generation
        "rank_monitoring": False,       # no rank tracking
        "real_data": False,             # heuristic only
        "support": "Community",
        "features": [
            "5 pipeline modules (CLI)",
            "Heuristic keyword analysis",
            "Competitor crawling + SEO audit",
            "Astro static site generation",
            "VPS / Vercel / Cloudflare deploy",
            "Self-hosted dashboard",
        ],
    },
    "starter": {
        "name": "Starter",
        "price": 29,
        "credits_monthly": 500,
        "max_projects": 3,
        "max_pseo_pages": 50,
        "ai_content": True,
        "ai_articles_per_month": 10,
        "rank_monitoring": False,
        "real_data": True,
        "support": "Email (48h)",
        "features": [
            "Everything in Free",
            "Real-time SEO data (search volume, KD, CPC)",
            "SERP analysis with competitor data",
            "AI content generation (10 articles/mo)",
            "Programmatic SEO (50 pages/mo)",
            "One-click deploy from dashboard",
            "Hosted dashboard",
        ],
    },
    "pro": {
        "name": "Pro",
        "price": 79,
        "credits_monthly": 2000,
        "max_projects": 10,
        "max_pseo_pages": 5000,
        "ai_content": True,
        "ai_articles_per_month": 100,
        "rank_monitoring": True,
        "real_data": True,
        "support": "Email (24h)",
        "features": [
            "Everything in Starter",
            "Unlimited programmatic SEO pages",
            "AI content at scale (100 articles/mo)",
            "Autonomous rank monitoring",
            "Content decay detection + auto-refresh",
            "AI agent orchestration",
            "GEO optimization (llms.txt + AI citations)",
            "Priority email support",
        ],
    },
    "agency": {
        "name": "Agency",
        "price": 199,
        "credits_monthly": 5000,
        "max_projects": 50,
        "max_pseo_pages": 50000,
        "ai_content": True,
        "ai_articles_per_month": 500,
        "rank_monitoring": True,
        "real_data": True,
        "support": "Slack (priority)",
        "features": [
            "Everything in Pro",
            "50 projects",
            "White-label reports",
            "Multi-client dashboard",
            "REST API access",
            "Team accounts",
            "Priority Slack support",
            "Custom integrations",
        ],
    },
}


def get_tier(plan: str) -> dict:
    """Get tier config for a plan name."""
    return TIERS.get(plan, TIERS["free"])


def can_create_project(user) -> bool:
    """Check if user can create more projects based on their tier."""
    tier = get_tier(user.plan)
    current_count = len(user.projects) if hasattr(user, 'projects') else 0
    return current_count < tier["max_projects"]


def can_use_feature(user, feature: str) -> bool:
    """Check if user's tier allows a specific feature."""
    tier = get_tier(user.plan)
    return tier.get(feature, False)
