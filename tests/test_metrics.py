"""
Unit tests for metrics module.
"""

import pytest
import time

from app.metrics import (
    Counter, Histogram, Gauge, MetricsRegistry,
    get_metrics, track_request
)


class TestCounter:
    """Tests for Counter metric."""
    
    def test_counter_initial_value(self):
        """Test counter starts at zero."""
        counter = Counter("test_counter", "Test description")
        assert counter.get() == 0.0
    
    def test_counter_increment(self):
        """Test counter increment."""
        counter = Counter("test_counter", "Test description")
        counter.inc()
        assert counter.get() == 1.0
        counter.inc()
        assert counter.get() == 2.0
    
    def test_counter_increment_by_value(self):
        """Test counter increment by specific value."""
        counter = Counter("test_counter", "Test description")
        counter.inc(value=5.0)
        assert counter.get() == 5.0
    
    def test_counter_with_labels(self):
        """Test counter with labels."""
        counter = Counter("test_counter", "Test description")
        
        counter.inc(labels={"method": "GET", "path": "/api"})
        counter.inc(labels={"method": "POST", "path": "/api"})
        counter.inc(labels={"method": "GET", "path": "/api"})
        
        assert counter.get(labels={"method": "GET", "path": "/api"}) == 2.0
        assert counter.get(labels={"method": "POST", "path": "/api"}) == 1.0
    
    def test_counter_collect(self):
        """Test counter collection."""
        counter = Counter("test_counter", "Test description")
        counter.inc(labels={"method": "GET"})
        
        collected = counter.collect()
        
        assert collected["name"] == "test_counter"
        assert collected["type"] == "counter"
        assert len(collected["values"]) == 1


class TestHistogram:
    """Tests for Histogram metric."""
    
    def test_histogram_observe(self):
        """Test histogram observation."""
        histogram = Histogram("test_histogram", "Test description")
        histogram.observe(0.5)
        histogram.observe(1.0)
        histogram.observe(0.1)
        
        summary = histogram.get_summary()
        assert summary["count"] == 3
        assert summary["sum"] == 1.6
        assert summary["avg"] == pytest.approx(0.533, rel=0.01)
    
    def test_histogram_with_labels(self):
        """Test histogram with labels."""
        histogram = Histogram("test_histogram", "Test description")
        
        histogram.observe(0.5, labels={"path": "/api"})
        histogram.observe(1.0, labels={"path": "/api"})
        histogram.observe(0.2, labels={"path": "/health"})
        
        api_summary = histogram.get_summary(labels={"path": "/api"})
        health_summary = histogram.get_summary(labels={"path": "/health"})
        
        assert api_summary["count"] == 2
        assert health_summary["count"] == 1
    
    def test_histogram_buckets(self):
        """Test histogram bucket distribution."""
        histogram = Histogram(
            "test_histogram",
            "Test description",
            buckets=(0.1, 0.5, 1.0)
        )
        
        histogram.observe(0.05)  # <= 0.1
        histogram.observe(0.3)   # <= 0.5
        histogram.observe(0.8)   # <= 1.0
        histogram.observe(2.0)   # > all buckets
        
        collected = histogram.collect()
        assert collected["type"] == "histogram"
    
    def test_histogram_collect(self):
        """Test histogram collection."""
        histogram = Histogram("test_histogram", "Test description")
        histogram.observe(0.5)
        
        collected = histogram.collect()
        
        assert collected["name"] == "test_histogram"
        assert collected["type"] == "histogram"


class TestGauge:
    """Tests for Gauge metric."""
    
    def test_gauge_initial_value(self):
        """Test gauge starts at zero."""
        gauge = Gauge("test_gauge", "Test description")
        assert gauge.get() == 0.0
    
    def test_gauge_set(self):
        """Test setting gauge value."""
        gauge = Gauge("test_gauge", "Test description")
        gauge.set(10.0)
        assert gauge.get() == 10.0
        gauge.set(5.0)
        assert gauge.get() == 5.0
    
    def test_gauge_increment(self):
        """Test gauge increment."""
        gauge = Gauge("test_gauge", "Test description")
        gauge.inc()
        assert gauge.get() == 1.0
        gauge.inc(value=4.0)
        assert gauge.get() == 5.0
    
    def test_gauge_decrement(self):
        """Test gauge decrement."""
        gauge = Gauge("test_gauge", "Test description")
        gauge.set(10.0)
        gauge.dec()
        assert gauge.get() == 9.0
        gauge.dec(value=4.0)
        assert gauge.get() == 5.0
    
    def test_gauge_with_labels(self):
        """Test gauge with labels."""
        gauge = Gauge("test_gauge", "Test description")
        
        gauge.set(5.0, labels={"instance": "a"})
        gauge.set(10.0, labels={"instance": "b"})
        
        assert gauge.get(labels={"instance": "a"}) == 5.0
        assert gauge.get(labels={"instance": "b"}) == 10.0
    
    def test_gauge_collect(self):
        """Test gauge collection."""
        gauge = Gauge("test_gauge", "Test description")
        gauge.set(5.0)
        
        collected = gauge.collect()
        
        assert collected["name"] == "test_gauge"
        assert collected["type"] == "gauge"


class TestMetricsRegistry:
    """Tests for MetricsRegistry."""
    
    def test_registry_initialization(self):
        """Test registry initializes with default metrics."""
        registry = MetricsRegistry()
        
        assert registry.request_count is not None
        assert registry.request_latency is not None
        assert registry.error_count is not None
        assert registry.active_requests is not None
    
    def test_registry_uptime(self):
        """Test uptime tracking."""
        registry = MetricsRegistry()
        time.sleep(0.1)
        
        uptime = registry.get_uptime()
        assert uptime >= 0.1
    
    def test_registry_collect_all(self):
        """Test collecting all metrics."""
        registry = MetricsRegistry()
        registry.request_count.inc(labels={"method": "GET", "path": "/", "status": "200"})
        
        collected = registry.collect_all()
        
        assert "uptime_seconds" in collected
        assert "metrics" in collected
        assert "http_requests_total" in collected["metrics"]
    
    def test_registry_prometheus_format(self):
        """Test Prometheus format export."""
        registry = MetricsRegistry()
        registry.request_count.inc(labels={"method": "GET", "path": "/", "status": "200"})
        
        prometheus_output = registry.to_prometheus_format()
        
        assert "# HELP http_requests_total" in prometheus_output
        assert "# TYPE http_requests_total counter" in prometheus_output


class TestTrackRequest:
    """Tests for track_request helper."""
    
    def test_track_request_success(self):
        """Test tracking a successful request."""
        metrics = get_metrics()
        initial_count = metrics.request_count.get(
            labels={"method": "GET", "path": "/test", "status": "200"}
        )
        
        track_request("GET", "/test", 200, 0.5)
        
        new_count = metrics.request_count.get(
            labels={"method": "GET", "path": "/test", "status": "200"}
        )
        assert new_count == initial_count + 1
    
    def test_track_request_error(self):
        """Test tracking an error request."""
        metrics = get_metrics()
        initial_error_count = metrics.error_count.get(
            labels={"method": "GET", "path": "/error", "status": "500"}
        )
        
        track_request("GET", "/error", 500, 0.1)
        
        new_error_count = metrics.error_count.get(
            labels={"method": "GET", "path": "/error", "status": "500"}
        )
        assert new_error_count == initial_error_count + 1
    
    def test_track_request_client_error(self):
        """Test tracking a client error (4xx)."""
        metrics = get_metrics()
        
        track_request("POST", "/notfound", 404, 0.05)
        
        error_count = metrics.error_count.get(
            labels={"method": "POST", "path": "/notfound", "status": "404"}
        )
        assert error_count >= 1
