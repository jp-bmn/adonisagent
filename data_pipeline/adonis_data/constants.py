"""Static constants for Michael's Week 1 Day 1 ingestion scope."""

HOSPITAL_QUERIES = {
    "NewYork-Presbyterian": (
        "NewYork-Presbyterian revenue cycle OR leadership OR Epic OR acquisition OR vendor dispute OR AI adoption"
    ),
    "UMass Memorial": (
        "UMass Memorial revenue cycle OR leadership OR Epic OR acquisition OR vendor dispute OR AI adoption"
    ),
    "Ascension": (
        "Ascension revenue cycle OR leadership OR Epic OR acquisition OR vendor dispute OR AI adoption"
    ),
    "University of Arkansas": (
        "University of Arkansas medical center revenue cycle OR leadership OR Epic OR acquisition OR vendor dispute OR AI adoption"
    ),
    "CommonSpirit": (
        "CommonSpirit revenue cycle OR leadership OR Epic OR acquisition OR restructuring OR vendor dispute OR AI adoption"
    ),
}

RSS_FEEDS = {
    "Becker's Hospital Review": "https://www.beckershospitalreview.com/rss/",
    "Modern Healthcare": "https://www.modernhealthcare.com/section/rss",
    "Fierce Healthcare": "https://www.fiercehealthcare.com/rss/xml",
    "RevCycleIntelligence": "https://revcycleintelligence.com/rss",
    "Healthcare IT News": "https://www.healthcareitnews.com/home/feed",
    "Healthcare Dive": "https://www.healthcaredive.com/feeds/news/",
    "HealthLeaders Media": "https://www.healthleadersmedia.com/rss",
}

TOPIC_KEYWORDS = {
    "leadership": [
        "ceo",
        "cfo",
        "cro",
        "revenue cycle",
        "leadership",
        "appointed",
        "named",
        "joined",
        "departure",
    ],
    "epic": ["epic", "ehr", "go-live", "go live", "implementation"],
    "acquisition": ["acquisition", "acquire", "merger", "merging", "divestiture"],
    "revenue_cycle": ["denials", "billing", "claims", "ar", "prior authorization"],
    "vendor_dispute": ["dispute", "dropped", "contract termination", "out of network", "payer dispute"],
    "ai_adoption": ["artificial intelligence", "ai", "machine learning", "automation", "partnership"],
}
