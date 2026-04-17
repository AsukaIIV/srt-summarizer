def choose_stream_tag(delta: str) -> str:
    stripped = delta.lstrip()
    if stripped.startswith("## "):
        return "h2"
    if stripped.startswith("# "):
        return "h1"
    if "**" in delta:
        return "bold"
    return "normal"
