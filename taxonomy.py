"""
Shared vocabulary for courses, users, and the recommendation engine.

Both data/generate_data.py and everything under engine/ import from here.
This exists specifically so topic/level/skill names can't drift between the
generator and the engine the way NGO Decision Support's FEATURE_COLUMNS
drifted across three separate files (see that project's architecture.md) --
one wrong string here would silently break matching, with no error raised.
If you add a topic, add it here once.
"""

TOPICS = [
    "financial_planning",
    "bookkeeping",
    "marketing",
    "sales",
    "leadership",
    "hr_management",
    "digital_skills",
    "operations",
    "strategy",
    "customer_service",
    "entrepreneurship",
    "negotiation",
]

TOPIC_DISPLAY = {
    "financial_planning": "Financial Planning",
    "bookkeeping": "Bookkeeping",
    "marketing": "Marketing",
    "sales": "Sales",
    "leadership": "Leadership",
    "hr_management": "HR Management",
    "digital_skills": "Digital Skills",
    "operations": "Operations",
    "strategy": "Strategy",
    "customer_service": "Customer Service",
    "entrepreneurship": "Entrepreneurship",
    "negotiation": "Negotiation",
}

TOPIC_SKILLS = {
    "financial_planning": ["budgeting", "cash_flow", "forecasting", "financial_planning"],
    "bookkeeping": ["bookkeeping", "ledgers", "reconciliation", "financial_records"],
    "marketing": ["branding", "digital_marketing", "social_media", "market_research"],
    "sales": ["sales_pitch", "customer_acquisition", "closing", "pipeline_management"],
    "leadership": ["team_management", "delegation", "coaching", "decision_making"],
    "hr_management": ["recruitment", "performance_management", "employee_relations", "payroll"],
    "digital_skills": ["excel", "data_analysis", "digital_tools", "online_presence"],
    "operations": ["process_improvement", "supply_chain", "inventory", "quality_control"],
    "strategy": ["business_planning", "competitive_analysis", "goal_setting", "growth_strategy"],
    "customer_service": ["customer_support", "communication", "conflict_resolution", "retention"],
    "entrepreneurship": ["business_model", "fundraising", "pitching", "startup_basics"],
    "negotiation": ["negotiation", "persuasion", "conflict_resolution", "deal_making"],
}

# Order matters here -- it's the progression assumed by prerequisite chains
# and by any level-appropriateness logic you write in engine/filters.py.
LEVELS = ["beginner", "intermediate", "advanced"]

SENIORITY = ["entry", "mid", "senior", "executive"]

ROLES = [
    "Business Owner",
    "Manager",
    "Team Lead",
    "Analyst",
    "Founder",
    "Operations Staff",
    "Sales Associate",
]

INDUSTRIES = [
    "Retail",
    "Agriculture",
    "Manufacturing",
    "Financial Services",
    "Hospitality",
    "Technology",
    "Healthcare",
    "Education",
]

COMPANY_SIZES = ["1-10", "11-50", "51-200", "201-500", "500+"]
