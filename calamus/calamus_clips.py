import os
from datetime import datetime
from calamus_config import load_json_file, save_json_file


def clips_path(config_dir):
    return os.path.join(config_dir, "clips.json")


def load_clips(config_dir, limit=200):
    data = load_json_file(clips_path(config_dir), [])
    clips = []
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            title = item.get("title") if isinstance(item.get("title"), str) else clip_title_from_text(item["text"])
            clips.append({"title": title, "text": item["text"], "created": item.get("created", "")})
    return clips[:limit]


def save_clips(config_dir, clips, limit=200):
    return save_json_file(clips_path(config_dir), clips[:limit])


def clip_title_from_text(text, max_len=40):
    first = " ".join(text.strip().split())
    if not first:
        return "Empty clip"
    return first[:max_len] + ("…" if len(first) > max_len else "")


def new_clip(title, text):
    return {"title": title or clip_title_from_text(text), "text": text, "created": datetime.now().isoformat(timespec="seconds")}
