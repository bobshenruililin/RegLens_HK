from lawtrace_worker.stage_d import score_candidate


def test_score_candidate_not_version_count_alone() -> None:
    high_churn_weak = {
        "stable_id_successor_coverage": 0.5,
        "reconstruction_success_rate": 0.5,
        "renderability": {"complete": 1, "unsupported": 9},
        "unsupported_structures": {"img": 5},
        "changed_section_pairs": 200,
        "ambiguous_events": 3,
        "versions_evaluated": 40,
        "elapsed_seconds": 10,
    }
    solid = {
        "stable_id_successor_coverage": 1.0,
        "reconstruction_success_rate": 1.0,
        "renderability": {"complete": 100},
        "unsupported_structures": {},
        "changed_section_pairs": 40,
        "ambiguous_events": 0,
        "versions_evaluated": 20,
        "elapsed_seconds": 10,
    }
    assert score_candidate(solid)["total"] > score_candidate(high_churn_weak)["total"]
