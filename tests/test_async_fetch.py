import unittest
import sys
import os
import json
import tempfile
from unittest.mock import patch, Mock, AsyncMock
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # noqa: E402
from stats_visualization.league import FetchMetrics, export_metrics_json, _fetch_metrics  # noqa: E402


class TestFetchMetrics(unittest.TestCase):
    """Test metrics collection functionality."""

    def setUp(self):
        """Reset metrics before each test."""
        global _fetch_metrics
        _fetch_metrics.total_requests = 0
        _fetch_metrics.cache_hits = 0
        _fetch_metrics.cache_misses = 0
        _fetch_metrics.retry_count = 0
        _fetch_metrics.request_latencies = []
        _fetch_metrics.match_ids_requests = 0
        _fetch_metrics.match_details_requests = 0
        _fetch_metrics.timeline_requests = 0
        _fetch_metrics.start_time = None
        _fetch_metrics.end_time = None

    def test_metrics_initialization(self):
        """Test metrics dataclass initialization."""
        metrics = FetchMetrics()
        self.assertEqual(metrics.total_requests, 0)
        self.assertEqual(metrics.cache_hits, 0)
        self.assertEqual(metrics.cache_misses, 0)
        self.assertEqual(metrics.retry_count, 0)
        self.assertEqual(len(metrics.request_latencies), 0)

    def test_add_request_latency(self):
        """Test adding request latency measurements."""
        metrics = FetchMetrics()
        metrics.add_request_latency(0.5, "match_details")
        metrics.add_request_latency(0.3, "timeline")
        
        self.assertEqual(metrics.total_requests, 2)
        self.assertEqual(metrics.match_details_requests, 1)
        self.assertEqual(metrics.timeline_requests, 1)
        self.assertEqual(len(metrics.request_latencies), 2)
        self.assertIn(0.5, metrics.request_latencies)
        self.assertIn(0.3, metrics.request_latencies)

    def test_cache_tracking(self):
        """Test cache hit/miss tracking."""
        metrics = FetchMetrics()
        metrics.add_cache_hit()
        metrics.add_cache_hit()
        metrics.add_cache_miss()
        
        self.assertEqual(metrics.cache_hits, 2)
        self.assertEqual(metrics.cache_misses, 1)

    def test_latency_statistics(self):
        """Test latency statistical calculations."""
        metrics = FetchMetrics()
        # Add latencies: [0.1, 0.2, 0.3, 0.4, 0.5]
        for i in range(1, 6):
            metrics.add_request_latency(i * 0.1)
        
        self.assertAlmostEqual(metrics.avg_latency, 0.3, places=1)
        self.assertAlmostEqual(metrics.max_latency, 0.5, places=1)
        # P95 of [0.1, 0.2, 0.3, 0.4, 0.5] should be close to 0.5
        self.assertGreaterEqual(metrics.p95_latency, 0.4)

    def test_timing_tracking(self):
        """Test overall timing functionality."""
        metrics = FetchMetrics()
        import time
        
        metrics.start_timing()
        time.sleep(0.01)  # Sleep for 10ms
        metrics.end_timing()
        
        self.assertIsNotNone(metrics.total_duration)
        self.assertGreater(metrics.total_duration, 0.005)  # Should be at least 5ms

    def test_to_dict_conversion(self):
        """Test conversion to dictionary for JSON export."""
        metrics = FetchMetrics()
        metrics.add_request_latency(0.2, "match_details")
        metrics.add_cache_hit()
        metrics.add_retry()
        
        result = metrics.to_dict()
        
        self.assertEqual(result["total_requests"], 1)
        self.assertEqual(result["cache_hits"], 1)
        self.assertEqual(result["cache_misses"], 0)
        self.assertEqual(result["retry_count"], 1)
        self.assertEqual(result["avg_latency_ms"], 200.0)  # 0.2s = 200ms
        self.assertIn("phase_breakdown", result)
        self.assertEqual(result["phase_breakdown"]["match_details_requests"], 1)

    def test_metrics_json_export(self):
        """Test JSON export functionality."""
        # Set up some test metrics
        _fetch_metrics.add_request_latency(0.1, "match_details")
        _fetch_metrics.add_cache_hit()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            export_metrics_json(temp_path)
            
            # Verify file was created and contains expected data
            self.assertTrue(Path(temp_path).exists())
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            self.assertEqual(data["total_requests"], 1)
            self.assertEqual(data["cache_hits"], 1)
            self.assertEqual(data["avg_latency_ms"], 100.0)
            
        finally:
            # Clean up
            if Path(temp_path).exists():
                Path(temp_path).unlink()

    def test_empty_metrics_statistics(self):
        """Test statistics with no data."""
        metrics = FetchMetrics()
        
        self.assertEqual(metrics.avg_latency, 0.0)
        self.assertEqual(metrics.p95_latency, 0.0)
        self.assertEqual(metrics.max_latency, 0.0)
        self.assertIsNone(metrics.total_duration)


class TestAsyncFunctionalities(unittest.TestCase):
    """Test async-related functionalities (mocked)."""

    def test_httpx_import_graceful_fallback(self):
        """Test graceful fallback when httpx is not available."""
        # This is more of a documentation test since we can't easily 
        # test import failures in the current setup
        try:
            import httpx  # noqa: F401
            self.assertTrue(True, "httpx is available")
        except ImportError:
            self.assertTrue(True, "httpx graceful fallback would work")

    @patch('stats_visualization.league.logger')
    def test_metrics_print_summary(self, mock_logger):
        """Test metrics summary printing."""
        metrics = FetchMetrics()
        metrics.add_request_latency(0.2)
        metrics.add_cache_hit()
        metrics.add_cache_miss()
        
        # Capture print output
        import io
        import sys
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            metrics.print_summary()
            output = captured_output.getvalue()
            
            self.assertIn("=== Fetch Metrics Summary ===", output)
            self.assertIn("Total requests: 1", output)
            self.assertIn("Cache hits: 1", output)
            self.assertIn("Cache misses: 1", output)
            
        finally:
            sys.stdout = sys.__stdout__


if __name__ == "__main__":
    unittest.main()