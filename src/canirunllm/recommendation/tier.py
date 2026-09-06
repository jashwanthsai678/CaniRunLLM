from enum import Enum


class RecommendationTier(str, Enum):
    BEST_MATCH = "BEST_MATCH"
    GOOD = "GOOD"
    POSSIBLE = "POSSIBLE"
    NOT_RECOMMENDED = "NOT_RECOMMENDED"
    CANNOT_RUN = "CANNOT_RUN"


TIER_STARS = {
    RecommendationTier.BEST_MATCH: 5,
    RecommendationTier.GOOD: 4,
    RecommendationTier.POSSIBLE: 3,
    RecommendationTier.NOT_RECOMMENDED: 2,
    RecommendationTier.CANNOT_RUN: 1,
}

TIER_ORDER = {
    RecommendationTier.BEST_MATCH: 0,
    RecommendationTier.GOOD: 1,
    RecommendationTier.POSSIBLE: 2,
    RecommendationTier.NOT_RECOMMENDED: 3,
    RecommendationTier.CANNOT_RUN: 4,
}
