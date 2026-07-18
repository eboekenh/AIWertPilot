from de_ai_kb.domain.similarity import TITLE_SIMILARITY_THRESHOLD, title_similarity


def test_identical_titles_score_one() -> None:
    assert title_similarity("Artificial Intelligence in Germany", "Artificial Intelligence in Germany") == 1.0


def test_case_and_whitespace_insensitive() -> None:
    assert title_similarity("  AI Adoption Study  ", "ai adoption study") == 1.0


def test_similarity_is_deterministic_across_calls() -> None:
    a, b = "Use of artificial intelligence by German companies", "Use of AI by German companies"
    first = title_similarity(a, b)
    second = title_similarity(a, b)
    assert first == second


def test_unrelated_titles_score_below_threshold() -> None:
    score = title_similarity(
        "Barriers to the use of artificial intelligence",
        "Small and medium-sized enterprises in Germany",
    )
    assert score < TITLE_SIMILARITY_THRESHOLD


def test_near_duplicate_titles_score_above_threshold() -> None:
    score = title_similarity(
        "AI adoption statistics 2025 report",
        "AI adoption statistics 2025 report (revised)",
    )
    assert score >= TITLE_SIMILARITY_THRESHOLD
