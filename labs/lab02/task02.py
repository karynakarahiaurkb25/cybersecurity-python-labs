import argparse
import csv
import logging
import os
import re
import sys
from typing import Any

DOMAIN_REGEX: re.Pattern = re.compile(
    r"@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", re.IGNORECASE
)


def setup_logger(debug: bool = False) -> logging.Logger:
    level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger("EmailAuditor")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def extract_domain(email_raw: str | None) -> str | None:
    if not email_raw:
        return None
    match = DOMAIN_REGEX.search(email_raw)
    return match.group(1).lower() if match else None


def load_keywords(filepath: str) -> list[str]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, mode="r", encoding="utf-8") as f:
        return [
            line.strip().lower()
            for line in f
            if line.strip() and not line.startswith("#")
        ]


def parse_mail_log(filepath: str) -> list[dict[str, Any]]:
    if not os.path.exists(filepath):
        return []

    with open(filepath, mode="r", encoding="utf-8") as f:
        content = f.read()

    raw_messages = content.split("--- MESSAGE ---")
    emails = []

    for idx, raw_msg in enumerate(raw_messages, start=1):
        lines = [line.strip() for line in raw_msg.strip().splitlines() if line.strip()]
        if not lines:
            continue

        email_data: dict[str, Any] = {
            "id": idx,
            "message_id": "",
            "from": "",
            "return_path": "",
            "reply_to": "",
            "subject": "",
            "received": [],
        }

        for line in lines:
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip().lower()
            val = val.strip()

            if key == "message-id":
                email_data["message_id"] = val
                id_match = re.search(r"<([^@>]+)", val)
                if id_match:
                    email_data["id"] = id_match.group(1)
            elif key == "from":
                email_data["from"] = val
            elif key == "return-path":
                email_data["return_path"] = val
            elif key == "reply-to":
                email_data["reply_to"] = val
            elif key == "subject":
                email_data["subject"] = val
            elif key == "received":
                email_data["received"].append(val)

        emails.append(email_data)

    return emails


def analyze_email(email_data: dict[str, Any], keywords: list[str]) -> dict[str, Any]:
    email_id = email_data.get("id", "Unknown")
    from_header = email_data.get("from", "")
    return_path = email_data.get("return_path", "")
    reply_to = email_data.get("reply_to", "")
    subject = email_data.get("subject", "")
    received_hops = email_data.get("received", [])

    from_domain = extract_domain(from_header)
    return_path_domain = extract_domain(return_path)
    reply_to_domain = extract_domain(reply_to)

    risk_score = 0
    sender_mismatch = False
    reply_to_mismatch = False

    if return_path_domain and from_domain != return_path_domain:
        sender_mismatch = True
        risk_score += 35

    if reply_to_domain and from_domain != reply_to_domain:
        reply_to_mismatch = True
        risk_score += 25

    found_keywords = []
    subject_lower = subject.lower()
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}\b", subject_lower, re.IGNORECASE):
            found_keywords.append(kw)

    if found_keywords:
        risk_score += min(len(found_keywords) * 15, 30)

    hop_count = len(received_hops)
    if hop_count >= 4:
        risk_score += 15

    risk_score = min(risk_score, 100)

    if risk_score >= 60:
        risk_level = "HIGH RISK"
        verdict = "CRITICAL PHISHING SUSPECT"
    elif risk_score >= 30:
        risk_level = "MEDIUM RISK"
        verdict = "SUSPICIOUS EMAIL"
    else:
        risk_level = "LOW RISK"
        verdict = "LEGITIMATE / CLEAN"

    return {
        "id": email_id,
        "subject": subject,
        "from": from_header,
        "return_path": return_path,
        "reply_to": reply_to,
        "sender_mismatch": sender_mismatch,
        "reply_to_mismatch": reply_to_mismatch,
        "stopwords_found": found_keywords,
        "hop_count": hop_count,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "verdict": verdict,
    }


def export_to_csv(results: list[dict[str, Any]], filepath: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    fieldnames = [
        "id",
        "risk_level",
        "risk_score",
        "verdict",
        "subject",
        "from",
        "return_path",
        "reply_to",
        "sender_mismatch",
        "reply_to_mismatch",
        "stopwords_found",
        "hop_count",
    ]

    with open(filepath, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            row = res.copy()
            row["stopwords_found"] = ", ".join(row["stopwords_found"])
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Аналізатор заголовків електронної пошти та фішингових індикаторів"
    )
    parser.add_argument(
        "--mail-log",
        required=True,
        help="Шлях до файлу із дампами заголовків (mail_headers.log)",
    )
    parser.add_argument(
        "--suspicious-keywords",
        required=True,
        help="Шлях до файлу стоп-слів (suspicious_keywords.txt)",
    )
    parser.add_argument(
        "--out-csv",
        required=False,
        default="data/phishing_report.csv",
        help="Шлях для вивантаження звіту CSV",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Режим налагодження DEBUG",
    )

    args = parser.parse_args()
    logger = setup_logger(args.debug)

    logger.debug(f"Зчитування логів із {args.mail_log}")
    emails = parse_mail_log(args.mail_log)
    if not emails:
        logger.error(f"Не вдалося зчитати листи або файл порожній: {args.mail_log}")
        sys.exit(1)

    keywords = load_keywords(args.suspicious_keywords)
    logger.debug(f"Завантажено ключових слів: {len(keywords)}")

    logger.info(f"Analyzing email headers dump from {args.mail_log}...")
    logger.info(f"Total emails inspected: {len(emails)}.")

    print("\n=== Phishing & Spoofing Audit Results ===")
    audit_results = []

    for email_data in emails:
        result = analyze_email(email_data, keywords)
        audit_results.append(result)

        if result["risk_score"] >= 30:
            print(
                f"\n[{result['risk_level']}] Email ID #{result['id']} | Subject: \"{result['subject']}\""
            )
            if result["sender_mismatch"]:
                print(
                    f"- Sender Mismatch : From: \"{result['from']}\" vs Return-Path: \"{result['return_path']}\""
                )
            if result["reply_to_mismatch"]:
                print(f"- Reply-To Mismatch: \"{result['reply_to']}\"")
            if result["stopwords_found"]:
                print(f"- Stopwords Found : {result['stopwords_found']}")
            abnormal_str = " (Abnormal)" if result["hop_count"] >= 4 else ""
            print(
                f"- Hop Count : {result['hop_count']} intermediate relays{abnormal_str}"
            )
            print(
                f"- Risk Score : {result['risk_score']}/100 ({result['verdict']})"
            )

    export_to_csv(audit_results, args.out_csv)
    logger.info(f"Phishing audit summary exported to {args.out_csv}")


if __name__ == "__main__":
    main()