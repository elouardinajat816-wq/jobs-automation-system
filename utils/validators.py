import re


def is_valid_email(email: str) -> bool:
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def extract_urls(text: str):
    return re.findall(r"https?://[^\s)]+", text or "")


def clean_text(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"\s+", " ", text)
    cleaned = re.sub(r"[^\w\s\-().,؟!:/@\u0600-\u06FF]", "", cleaned, flags=re.UNICODE)
    return cleaned.strip()
