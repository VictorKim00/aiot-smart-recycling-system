from __future__ import annotations

CATEGORY_ALIASES = {
    "plastic": {
        "bottle",
        "plastic bottle",
        "plastic_bottle",
        "pet bottle",
        "pet_bottle",
        "water bottle",
        "plastic",
    },
    "can": {
        "can",
        "tin can",
        "tin_can",
        "aluminum can",
        "aluminium can",
        "aluminum_can",
        "metal can",
        "metal_can",
        "can_metal",
    },
    "paper": {
        "paper",
        "paper cup",
        "paper_cup",
        "cardboard",
        "newspaper",
        "book",
        "document",
        "carton",
        "box",
    },
}

DISPLAY_NAMES = {
    "plastic": "Plastic",
    "can": "Can/Metal",
    "paper": "Paper",
    "unknown": "Unknown",
}

BIN_GUIDE = {
    "plastic": "Put in Plastic Bin",
    "can": "Put in Can Bin",
    "paper": "Put in Paper Bin",
    "unknown": "Ask staff / retry",
}


def normalize_label(label: str | None) -> str:
    if label is None:
        return ""
    return str(label).strip().lower().replace("-", "_").replace("/", " ").replace("_", " ")


def label_to_category(label: str | None) -> str:
    normalized = normalize_label(label)
    if not normalized:
        return "unknown"

    if normalized in {"plastic", "can", "paper"}:
        return normalized

    for category, aliases in CATEGORY_ALIASES.items():
        normalized_aliases = {normalize_label(x) for x in aliases}
        if normalized in normalized_aliases:
            return category

    # Soft keyword matching for slightly different class names.
    if "bottle" in normalized or "pet" in normalized or "plastic" in normalized:
        return "plastic"
    if "can" in normalized or "metal" in normalized or "aluminum" in normalized or "aluminium" in normalized:
        return "can"
    if "paper" in normalized or "cardboard" in normalized or "carton" in normalized or "newspaper" in normalized:
        return "paper"

    return "unknown"


def lcd_lines_for_detection(label: str, category: str, confidence: float, fullness_percent: float | None = None) -> list[str]:
    label_text = (label or "unknown")[:16]
    category_text = DISPLAY_NAMES.get(category, category.title())
    lines = [
        f"Detected: {label_text}",
        f"Type: {category_text}",
        f"Conf:{confidence:.2f}",
        BIN_GUIDE.get(category, "Retry"),
    ]
    if fullness_percent is not None:
        lines[2] = f"Conf:{confidence:.2f} Full:{fullness_percent:.0f}%"
    return lines


def lcd_lines_for_uncertain(label: str, confidence: float) -> list[str]:
    label_text = (label or "unknown")[:16]
    return [
        "Low confidence",
        f"Guess: {label_text}",
        f"Conf:{confidence:.2f}",
        "Show item again",
    ]
