import unittest
import io
import sys
from contextlib import redirect_stdout

# Ensure project root and visualization package on path (if not already)
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestGenerateAllVisuals(unittest.TestCase):
    def test_generate_all_visuals_invokes_all_steps(self):
        """Smoke test for analyze.generate_all_visuals orchestration.

        Patches all underlying extract/plot functions to lightweight stubs and
        asserts that the final summary reports all steps succeeded.
        """
        from stats_visualization import analyze  # noqa: WPS433

        # Pre-import visualization modules so our monkeypatches persist when
        # generate_all_visuals re-imports them locally.
        from stats_visualization.visualizations import (
            personal_performance as _pp,
        )  # noqa: WPS433
        from stats_visualization.visualizations import (
            graph_kills as _gk,
        )  # noqa: WPS433
        from stats_visualization.visualizations import (
            graph_drakes as _gd,
        )  # noqa: WPS433
        from stats_visualization.visualizations import (
            graph_barons_heralds as _bh,
        )  # noqa: WPS433
        from stats_visualization.visualizations import (
            objective_analysis as _oa,
        )  # noqa: WPS433
        from stats_visualization.visualizations import (
            farming_analysis as _fa,
        )  # noqa: WPS433
        from stats_visualization.visualizations import (
            graph_first_bloods as _fb,
        )  # noqa: WPS433
        from stats_visualization.visualizations import (
            jungle_clear_analysis as _jc,
        )  # noqa: WPS433
        from stats_visualization import utils as _utils  # noqa: WPS433

        calls: list[str] = []

        # Patch clean_output to avoid deleting any real files during test
        clean_calls: list[int] = []

        def _clean_output_stub(*_a, **_k):  # noqa: WPS430
            clean_calls.append(1)
            return 0

        _utils.clean_output = _clean_output_stub  # type: ignore

        # Generic plot stub
        def _plot(name):  # noqa: WPS430
            def _inner(*_a, **_k):  # noqa: WPS430
                calls.append(name)

            return _inner

        # Personal performance
        _pp.plot_performance_trends = _plot("personal_trends")  # type: ignore
        _pp.plot_champion_performance = _plot("personal_champions")  # type: ignore
        _pp.plot_role_performance = _plot("personal_roles")  # type: ignore

        # Kills
        _gk.extract_kills_data = lambda *a, **k: {}  # type: ignore  # noqa: E731
        _gk.plot_kills_analysis = _plot("kills")  # type: ignore

        # Drakes
        _gd.extract_drake_data = lambda *a, **k: {}  # type: ignore  # noqa: E731
        _gd.plot_drake_analysis = _plot("drakes")  # type: ignore

        # Barons / Heralds
        _bh.extract_baron_herald_data = lambda *a, **k: {}  # type: ignore  # noqa: E731
        _bh.plot_baron_herald_analysis = _plot("barons_heralds")  # type: ignore

        # Objectives (return truthy cache)
        _oa.extract_objective_data = lambda *a, **k: {"ok": True}  # type: ignore  # noqa: E731
        _oa.plot_objective_control = _plot("objectives_control")  # type: ignore
        _oa.plot_first_objectives = _plot("objectives_first")  # type: ignore
        _oa.plot_objective_win_correlation = _plot("objectives_correlation")  # type: ignore

        # Farming / economy (truthy data)
        _fa.extract_economy_data = lambda *a, **k: {"ok": True}  # type: ignore  # noqa: E731
        _fa.plot_farming_performance = _plot("farming")  # type: ignore
        _fa.plot_gold_efficiency = _plot("gold_efficiency")  # type: ignore
        _fa.plot_role_economy_comparison = _plot("role_economy")  # type: ignore

        # First blood
        _fb.extract_early_game_data = lambda *a, **k: {}  # type: ignore  # noqa: E731
        _fb.plot_first_blood_analysis = _plot("first_bloods")  # type: ignore

        # Jungle clear
        _jc.extract_jungle_clear_data = lambda *a, **k: {}  # type: ignore  # noqa: E731
        _jc.plot_jungle_clear_analysis = _plot("jungle_clear")  # type: ignore

        buf = io.StringIO()
        with redirect_stdout(buf):
            analyze.generate_all_visuals(
                "TestPlayer#TAG",
                "puuid-123",
                clean=True,
                include_aram=False,
            )
        output = buf.getvalue()

        # Expect clean called exactly once
        self.assertEqual(len(clean_calls), 1, "clean_output should run once")

        # We expect 14 plot calls corresponding to the labels used internally
        expected_labels = {
            "personal_trends",
            "personal_champions",
            "personal_roles",
            "kills",
            "drakes",
            "barons_heralds",
            "objectives_control",
            "objectives_first",
            "objectives_correlation",
            "farming",
            "gold_efficiency",
            "role_economy",
            "first_bloods",
            "jungle_clear",
        }
        self.assertEqual(set(calls), expected_labels)
        self.assertEqual(len(calls), len(expected_labels))

        # Summary line should indicate all succeeded
        self.assertIn("14/14 succeeded", output)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
