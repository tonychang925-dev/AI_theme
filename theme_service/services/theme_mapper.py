import logging
from typing import List, Dict

from theme_service.models.theme import fetch_all_themes
from theme_service.confidence.confidence_level import (
    confidence_to_level,
    ConfidenceLevel
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

async def map_event_to_themes(event: Dict) -> List[Dict]:
    """
    规则映射：根据 event 的文本字段匹配主题关键词，并进行置信度分层

    event 示例：
    {
        "event_type": "政策",
        "impact_industries": ["半导体", "算力"],
        "summary": "国家出台新政策支持算力基础设施建设"
    }

    返回：
    [
        {
            "theme_id": 1,
            "theme_name": "算力",
            "confidence": 1.0,
            "confidence_level": "strong",
            "confidence_weight": 100,
            "evidence": {...}
        }
    ]
    """

    themes = await fetch_all_themes()
    matched_themes: List[Dict] = []

    logger.debug(f"Start mapping event to themes: {event}")

    # 统一拼接事件文本（用于关键词匹配）
    event_text = (
        event.get("event_type", "") + " " +
        " ".join(event.get("impact_industries", [])) + " " +
        event.get("summary", "")
    ).lower()

    event_type = event.get("event_type", "").strip()
    industries = event.get("impact_industries", [])

    if not event_type or not industries:
        logger.warning(
            "Event missing event_type or impact_industries, skip mapping."
        )
        return matched_themes

    for theme in themes:
        theme_name = theme.get("name", "")
        keywords = [kw.lower() for kw in (theme.get("keywords") or [])]

        if not keywords:
            continue

        # ===== 规则 1：direct_match（行业 or 题材名直接命中）=====
        direct_match = (
            theme_name in industries or
            theme_name.lower() in event_text
        )

        # ===== 规则 2：关键词命中 =====
        hits = [kw for kw in keywords if kw in event_text]

        if not direct_match and not hits:
            continue

        # ===== 置信度计算 =====
        if direct_match:
            raw_confidence = 1.0
        else:
            raw_confidence = len(hits) / len(keywords)

        level, weight = confidence_to_level(raw_confidence)

        if level == ConfidenceLevel.IGNORE:
            logger.debug(
                f"Theme '{theme_name}' ignored due to low confidence "
                f"({raw_confidence:.2f})"
            )
            continue

        logger.debug(
            f"Event matched theme '{theme_name}' "
            f"(direct_match={direct_match}, "
            f"keywords_matched={hits}, "
            f"confidence={raw_confidence:.2f}, "
            f"level={level.value})"
        )

        matched_themes.append({
            "theme_id": theme["id"],
            "theme_name": theme_name,
            "confidence": round(raw_confidence, 2),

            # ===== 置信度分层（第一步核心成果）=====
            "confidence_level": level.value,
            "confidence_weight": weight,

            # ===== 为后续题材聚合 / 龙头引擎预留 =====
            "evidence": {
                "direct_match": direct_match,
                "matched_keywords": hits,
                "event_type": event_type,
            }
        })

    logger.debug(
        f"Finished mapping event, matched {len(matched_themes)} themes."
    )
    return matched_themes


