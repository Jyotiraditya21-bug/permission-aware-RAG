import unittest

from pydantic import ValidationError

from src.settings import Settings


# Test values only; production tuning is intentionally not defaulted.
VALUES = {
    "lexical_candidates": 20, "dense_candidates": 20, "fusion_rank_constant": 60,
    "rerank_candidates": 10, "max_subqueries": 3, "evidence_token_budget": 2000,
    "cache_similarity_threshold": 0.95, "cache_ttl_seconds": 60,
    "embedding_model": "mock-embedding", "generator_model": "mock-generator",
    "retrieval_config_version": "retrieval-1", "reranker_config_version": "reranker-1",
    "prompt_version": "prompt-1",
}


class SettingsTests(unittest.TestCase):
    def test_valid_settings_round_trip(self) -> None:
        settings = Settings.model_validate(VALUES)
        self.assertEqual(settings.model_dump(), VALUES)
        self.assertEqual(Settings.model_validate_json(settings.model_dump_json()), settings)

    def test_all_settings_require_explicit_values(self) -> None:
        for field in VALUES:
            data = dict(VALUES)
            data.pop(field)
            with self.subTest(field=field), self.assertRaises(ValidationError):
                Settings.model_validate(data)

    def test_positive_integer_limits(self) -> None:
        for field, value in VALUES.items():
            if isinstance(value, int):
                for invalid in (0, -1, True, 1.5, "10"):
                    with self.subTest(field=field, invalid=invalid), self.assertRaises(ValidationError):
                        Settings.model_validate({**VALUES, field: invalid})

    def test_similarity_threshold_range(self) -> None:
        for value in (-1, 0, 1):
            self.assertEqual(Settings.model_validate({**VALUES, "cache_similarity_threshold": value}).cache_similarity_threshold, value)
        for value in (-1.01, 1.01, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                Settings.model_validate({**VALUES, "cache_similarity_threshold": value})

    def test_model_and_version_names_are_nonblank(self) -> None:
        for field, value in VALUES.items():
            if isinstance(value, str):
                with self.subTest(field=field), self.assertRaises(ValidationError):
                    Settings.model_validate({**VALUES, field: "  "})

    def test_unknown_settings_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            Settings.model_validate({**VALUES, "typo": 1})
