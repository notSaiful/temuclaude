#!/usr/bin/env python3
"""
Halal Compliance Checker — ensures Sharia compliance for all outputs and decisions.
"""

HARAM_KEYWORDS = [
    "alcohol", "wine", "beer", "liquor", "pork", "gambling", "casino",
    "interest rate", "riba", "usury", "adult", "pornographic",
    "escort", "dating app",
]

HARAM_INDUSTRIES = [
    "alcohol", "gambling", "pork", "adult entertainment",
    "conventional banking (interest-based)", "tobacco", "weapons manufacturing",
]

def check_output_halal(content):
    content_lower = content.lower()
    violations = [kw for kw in HARAM_KEYWORDS if kw in content_lower]
    return {"is_halal": len(violations) == 0, "violations": violations,
            "action": "block" if violations else "allow"}

def check_business_halal(partner_industry):
    industry_lower = partner_industry.lower()
    violations = [ind for ind in HARAM_INDUSTRIES if ind in industry_lower]
    return {"is_halal": len(violations) == 0, "violations": violations,
            "action": "reject" if violations else "accept"}

def purify_revenue(revenue_sources):
    halal = {}
    non_halal = {}
    for source, amount in revenue_sources.items():
        if check_business_halal(source)["is_halal"]:
            halal[source] = amount
        else:
            non_halal[source] = amount
    return {"halal_revenue": halal, "non_halal_revenue": non_halal,
            "total_halal": sum(halal.values()), "total_non_halal": sum(non_halal.values())}
