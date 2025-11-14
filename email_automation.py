import os
import re
from dataclasses import dataclass, asdict
from typing import List, Tuple
import csv

# ---------- Simple utilities ----------

# Very small custom stopword list (no external downloads needed)
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "if", "in", "on", "at", "to", "for",
    "from", "of", "is", "are", "was", "were", "be", "been", "am", "it", "that",
    "this", "with", "as", "by", "about", "into", "up", "out", "over", "after",
    "before", "between", "then", "than", "so", "very", "can", "will", "just",
    "do", "does", "did", "have", "has", "had", "you", "i", "we", "they",
    "he", "she", "them", "his", "her", "our", "your", "their"
}


@dataclass
class EmailSummary:
    filename: str
    summary: str
    priority: str
    category: str


def normalize_text(text: str) -> str:
    """Collapse extra whitespace and strip."""
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str):
    """
    Very simple sentence splitter based on punctuation.
    Not perfect, but good enough for emails/text.
    """
    text = text.strip()
    if not text:
        return []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Remove empty sentences
    return [s.strip() for s in sentences if s.strip()]


def tokenize_words(text: str):
    """Extract alphabetic words in lowercase."""
    return re.findall(r"\b[a-zA-Z]+\b", text.lower())


# ---------- Summarization ----------

def summarize_text(text: str, max_sentences: int = 3) -> str:
    """
    Simple extractive summarization:
    - score sentences based on word frequency
    - return the top N sentences, preserving original order
    """
    text = normalize_text(text)
    if not text:
        return ""

    sentences = split_sentences(text)
    if not sentences:
        return ""
    if len(sentences) <= max_sentences:
        return text

    # Build word frequency table
    freq = {}
    for sent in sentences:
        for word in tokenize_words(sent):
            if word not in STOP_WORDS:
                freq[word] = freq.get(word, 0) + 1

    if not freq:
        # fallback: just take first few sentences
        return " ".join(sentences[:max_sentences])

    max_freq = max(freq.values())
    # normalize frequencies
    for w in freq:
        freq[w] /= max_freq

    # Score each sentence
    sent_scores = {}
    for sent in sentences:
        score = 0.0
        for word in tokenize_words(sent):
            score += freq.get(word, 0.0)
        sent_scores[sent] = score

    # Rank sentences by score (high to low)
    ranked = sorted(sent_scores, key=sent_scores.get, reverse=True)
    chosen = set(ranked[:max_sentences])

    # Keep chosen sentences in original order
    summary_sentences = [s for s in sentences if s in chosen]
    return " ".join(summary_sentences)


# ---------- Categorization ----------

def categorize_text(text: str) -> Tuple[str, str]:
    """
    Returns (priority, category)
    priority: HIGH or NORMAL
    category: BUSINESS, PERSONAL, PROMOTION, OTHER
    """
    text_low = text.lower()

    high_keywords = [
        "urgent", "immediately", "asap", "deadline", "failed",
        "error", "issue", "critical", "important", "payment",
        "invoice", "meeting", "schedule", "client", "project"
    ]
    business_keywords = [
        "client", "project", "meeting", "contract",
        "invoice", "payment", "report", "proposal", "deadline"
    ]
    personal_keywords = [
        "friend", "family", "birthday", "party", "hangout",
        "dinner", "call me", "see you", "miss you"
    ]
    promo_keywords = [
        "discount", "offer", "sale", "promotion", "coupon",
        "deal", "subscribe", "newsletter", "limited time"
    ]

    # Priority
    priority = "NORMAL"
    if any(k in text_low for k in high_keywords):
        priority = "HIGH"

    # Category
    category = "OTHER"
    if any(k in text_low for k in business_keywords):
        category = "BUSINESS"
    elif any(k in text_low for k in personal_keywords):
        category = "PERSONAL"
    elif any(k in text_low for k in promo_keywords):
        category = "PROMOTION"

    return priority, category


# ---------- Main processing ----------

def process_folder(input_folder: str, output_csv: str = "email_summaries.csv") -> List[EmailSummary]:
    results: List[EmailSummary] = []

    for fname in os.listdir(input_folder):
        if not fname.lower().endswith(".txt"):
            continue

        path = os.path.join(input_folder, fname)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        summary = summarize_text(text)
        priority, category = categorize_text(text)

        results.append(
            EmailSummary(
                filename=fname,
                summary=summary,
                priority=priority,
                category=category,
            )
        )

    # Save to CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["filename", "summary", "priority", "category"],
        )
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Automation Script: Email/Text Summarization & Categorization"
    )
    parser.add_argument(
        "input_folder",
        help="Folder containing .txt files (each file = one email/text)",
    )
    parser.add_argument(
        "--output",
        default="email_summaries.csv",
        help="Output CSV file name (default: email_summaries.csv)",
    )

    args = parser.parse_args()

    summaries = process_folder(args.input_folder, args.output)
    print(f"Processed {len(summaries)} files. Results saved to {args.output}.")
