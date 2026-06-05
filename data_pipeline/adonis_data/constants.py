"""Static constants for Michael's Week 1 Day 1 ingestion scope."""

HOSPITAL_QUERIES = {
    "NewYork-Presbyterian": (
        "NewYork-Presbyterian revenue cycle OR leadership OR Epic OR acquisition"
    ),
    "UMass Memorial": (
        "UMass Memorial revenue cycle OR leadership OR Epic OR acquisition"
    ),
    "Ascension": (
        "Ascension revenue cycle OR leadership OR Epic OR acquisition OR vendor dispute"
    ),
    "University of Arkansas": (
        "University of Arkansas medical center revenue cycle OR leadership OR Epic OR acquisition"
    ),
    "CommonSpirit": (
        "CommonSpirit revenue cycle OR leadership OR Epic OR acquisition OR restructuring"
    ),
}

RSS_FEEDS = {
    "Becker's Hospital Review": "https://www.beckershospitalreview.com/rss/",
    "Modern Healthcare": "https://www.modernhealthcare.com/section/rss",
    "Fierce Healthcare": "https://www.fiercehealthcare.com/rss/xml",
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
}
