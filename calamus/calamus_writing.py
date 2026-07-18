import re
import textwrap
from datetime import datetime

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9']+")
SENTENCE_END_RE = re.compile(r"[.!?…][\"'”’)]*$")


def current_date_string(fmt="%Y-%m-%d %H:%M", now=None):
    """Format an explicit datetime, or the current local time when omitted.

    CommandLayer callers pass ``now`` explicitly so formatting stays
    deterministic and GTK-free.  The default preserves the legacy helper API.
    """
    moment = datetime.now() if now is None else now
    if not isinstance(moment, datetime):
        raise TypeError("now must be a datetime")
    if not isinstance(fmt, str):
        raise TypeError("fmt must be a string")
    return moment.strftime(fmt)


def preserve_final_newline(original, result):
    return result + "\n" if original.endswith("\n") and not result.endswith("\n") else result


def sort_lines(text, reverse=False, casefold=True):
    lines = text.splitlines()
    key = (lambda s: s.casefold()) if casefold else None
    out = "\n".join(sorted(lines, key=key, reverse=reverse))
    return preserve_final_newline(text, out)


def clean_pdf_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"([A-Za-zÀ-ÖØ-öø-ÿ])-\n([A-Za-zÀ-ÖØ-öø-ÿ])", r"\1\2", text)
    paragraphs = re.split(r"\n\s*\n+", text.strip())
    cleaned = []
    for para in paragraphs:
        raw_lines = [re.sub(r"[ \t]+", " ", l).strip() for l in para.split("\n")]
        raw_lines = [l for l in raw_lines if l]
        if not raw_lines:
            continue
        merged = []
        current = ""
        for line in raw_lines:
            if not current:
                current = line
            elif SENTENCE_END_RE.search(current):
                current += " " + line
            else:
                current += " " + line
        current = re.sub(r"[ \t]+", " ", current).strip()
        if current:
            cleaned.append(current)
    result = "\n\n".join(cleaned)
    return preserve_final_newline(text, result)


def remove_extra_spaces(text):
    out = "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines())
    return preserve_final_newline(text, out)


def remove_trailing_spaces(text):
    out = "\n".join(line.rstrip() for line in text.splitlines())
    return preserve_final_newline(text, out)


def join_lines(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"([A-Za-zÀ-ÖØ-öø-ÿ])-\n([A-Za-zÀ-ÖØ-öø-ÿ])", r"\1\2", text)
    paragraphs = re.split(r"\n\s*\n+", text.strip())
    out = []
    for p in paragraphs:
        line = " ".join(x.strip() for x in p.splitlines() if x.strip())
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            out.append(line)
    return preserve_final_newline(text, "\n\n".join(out))


def reflow_paragraph(text, width=80):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = re.split(r"(\n\s*\n+)", text)
    out = []
    for part in paragraphs:
        if re.match(r"\n\s*\n+", part):
            out.append("\n\n")
        else:
            joined = " ".join(x.strip() for x in part.splitlines() if x.strip())
            if joined:
                out.append(textwrap.fill(joined, width=width, break_long_words=False, replace_whitespace=True))
    result = "".join(out).strip("\n")
    return preserve_final_newline(text, result)


def smart_typography(text):
    text = text.replace("...", "…")
    text = text.replace("---", "—").replace("--", "—")
    # conservative curly quote conversion
    chars = []
    open_double = True
    open_single = True
    for ch in text:
        if ch == '"':
            chars.append("“" if open_double else "”")
            open_double = not open_double
        elif ch == "'":
            chars.append("‘" if open_single else "’")
            open_single = not open_single
        else:
            chars.append(ch)
    return "".join(chars)


def title_case(text):
    return re.sub(r"\b([A-Za-zÀ-ÖØ-öø-ÿ])([A-Za-zÀ-ÖØ-öø-ÿ']*)", lambda m: m.group(1).upper() + m.group(2).lower(), text)


def sentence_case(text):
    lower = text.lower()
    def repl(m):
        return m.group(1) + m.group(2).upper()
    lower = re.sub(r"(^|[.!?…]\s+)([a-zà-öø-ÿ])", repl, lower, flags=re.MULTILINE)
    return lower


def document_statistics(text, words_per_minute=200):
    words = WORD_RE.findall(text)
    chars = len(text)
    chars_no_spaces = len(re.sub(r"\s+", "", text))
    paragraphs = len([p for p in re.split(r"\n\s*\n+", text.strip()) if p.strip()]) if text.strip() else 0
    lines = len(text.splitlines()) if text else 0
    reading_minutes = max(1, round(len(words) / float(words_per_minute))) if words else 0
    return {
        "words": len(words),
        "characters": chars,
        "characters_no_spaces": chars_no_spaces,
        "paragraphs": paragraphs,
        "lines": lines,
        "reading_minutes": reading_minutes,
    }
