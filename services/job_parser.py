import re

from config.settings import COUNTRIES_KEYWORDS
from utils.validators import extract_urls, clean_text


class JobParser:
    @staticmethod
    def parse_job(subject: str, body: str):
        return {
            "title": subject[:255] if subject else "Untitled job",
            "country": JobParser.detect_country(subject, body),
            "details": JobParser.extract_details(body),
            "contact_link": JobParser.extract_link(body),
        }

    @staticmethod
    def detect_country(subject: str, body: str) -> str:
        combined = (subject + " " + body).lower()
        for country, keywords in COUNTRIES_KEYWORDS.items():
            if country == "International":
                continue
            for keyword in keywords:
                if keyword.lower() in combined:
                    return country
        return "International"

    @staticmethod
    def extract_details(body: str) -> str:
        text = clean_text(body[:500])
        return text if text else "تفاصيل الوظيفة متاحة في رابط التقديم"

    @staticmethod
    def extract_link(body: str):
        urls = extract_urls(body)
        return urls[0] if urls else None
