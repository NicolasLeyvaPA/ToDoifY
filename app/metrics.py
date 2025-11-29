"""
Metrics module for application monitoring.
Exposes Prometheus-compatible metrics for request count, latency, and errors.
"""

import time
from functools import wraps
from typing import Callable, Dict, Any
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class MetricValue:
    """Represents a single metric value with labels."""
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)


class Counter:
    """A counter metric that only increases."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._values: Dict[tuple, float] = defaultdict(float)
        self._lock = Lock()
    
    def inc(self, labels: Dict[str, str] = None, value: float = 1.0) -> None:
        """Increment the counter."""
        label_key = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._values[label_key] += value
    
    def get(self, labels: Dict[str, str] = None) -> float:
        """Get current counter value."""
        label_key = tuple(sorted((labels or {}).items()))
        return self._values.get(label_key, 0.0)
    
    def collect(self) -> Dict[str, Any]:
        """Collect all metric values."""
        with self._lock:
            return {
                "name": self.name,
                "description": self.description,
                "type": "counter",
                "values": [
                    {"labels": dict(k), "value": v}
                    for k, v in self._values.items()
                ]
            }


class Histogram:
    """A histogram metric for measuring distributions (e.g., latency)."""
    
    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    
    def __init__(self, name: str, description: str, buckets: tuple = None):
        self.name = name
        self.description = description
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._counts: Dict[tuple, Dict[float, int]] = defaultdict(lambda: defaultdict(int))
        self._sums: Dict[tuple, float] = defaultdict(float)
        self._totals: Dict[tuple, int] = defaultdict(int)
        self._lock = Lock()
    
    def observe(self, value: float, labels: Dict[str, str] = None) -> None:
        """Record an observation."""
        label_key = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._sums[label_key] += value
            self._totals[label_key] += 1
            for bucket in self.buckets:
                if value <= bucket:
                    self._counts[label_key][bucket] += 1
    
    def get_summary(self, labels: Dict[str, str] = None) -> Dict[str, float]:
        """Get summary statistics."""
        label_key = tuple(sorted((labels or {}).items()))
        total = self._totals.get(label_key, 0)
        sum_val = self._sums.get(label_key, 0.0)
        return {
            "count": total,
            "sum": sum_val,
            "avg": sum_val / total if total > 0 else 0.0
        }
    
    def collect(self) -> Dict[str, Any]:
        """Collect all metric values."""
        with self._lock:
            values = []
            for label_key in set(self._totals.keys()):
                values.append({
                    "labels": dict(label_key),
                    "count": self._totals[label_key],
                    "sum": self._sums[label_key],
                    "buckets": {
                        str(b): self._counts[label_key].get(b, 0)
                        for b in self.buckets
                    }
                })
            return {
                "name": self.name,
                "description": self.description,
                "type": "histogram",
                "values": values
            }


class Gauge:
    """A gauge metric that can go up and down."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._values: Dict[tuple, float] = defaultdict(float)
        self._lock = Lock()
    
    def set(self, value: float, labels: Dict[str, str] = None) -> None:
        """Set the gauge value."""
        label_key = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._values[label_key] = value
    
    def inc(self, labels: Dict[str, str] = None, value: float = 1.0) -> None:
        """Increment the gauge."""
        label_key = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._values[label_key] += value
    
    def dec(self, labels: Dict[str, str] = None, value: float = 1.0) -> None:
        """Decrement the gauge."""
        label_key = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._values[label_key] -= value
    
    def get(self, labels: Dict[str, str] = None) -> float:
        """Get current gauge value."""
        label_key = tuple(sorted((labels or {}).items()))
        return self._values.get(label_key, 0.0)
    
    def collect(self) -> Dict[str, Any]:
        """Collect all metric values."""
        with self._lock:
            return {
                "name": self.name,
                "description": self.description,
                "type": "gauge",
                "values": [
                    {"labels": dict(k), "value": v}
                    for k, v in self._values.items()
                ]
            }


class MetricsRegistry:
    """Registry for all application metrics."""
    
    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self._lock = Lock()
        self._start_time = time.time()
        
        # Initialize default metrics
        self.request_count = Counter(
            "http_requests_total",
            "Total number of HTTP requests"
        )
        self.request_latency = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency in seconds"
        )
        self.error_count = Counter(
            "http_errors_total",
            "Total number of HTTP errors"
        )
        self.active_requests = Gauge(
            "http_active_requests",
            "Number of active HTTP requests"
        )
        
        self._metrics = {
            "http_requests_total": self.request_count,
            "http_request_duration_seconds": self.request_latency,
            "http_errors_total": self.error_count,
            "http_active_requests": self.active_requests
        }
    
    def get_uptime(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self._start_time
    
    def collect_all(self) -> Dict[str, Any]:
        """Collect all metrics."""
        return {
            "uptime_seconds": self.get_uptime(),
            "metrics": {
                name: metric.collect()
                for name, metric in self._metrics.items()
            }
        }
    
    def to_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        
        for name, metric in self._metrics.items():
            data = metric.collect()
            lines.append(f"# HELP {name} {data['description']}")
            lines.append(f"# TYPE {name} {data['type']}")
            
            for value_data in data['values']:
                labels = value_data.get('labels', {})
                label_str = ','.join(f'{k}="{v}"' for k, v in labels.items())
                label_part = f"{{{label_str}}}" if label_str else ""
                
                if data['type'] == 'histogram':
                    # Output histogram buckets
                    for bucket, count in value_data.get('buckets', {}).items():
                        lines.append(f'{name}_bucket{{le="{bucket}"{("," + label_str) if label_str else ""}}} {count}')
                    lines.append(f'{name}_sum{label_part} {value_data.get("sum", 0)}')
                    lines.append(f'{name}_count{label_part} {value_data.get("count", 0)}')
                else:
                    lines.append(f'{name}{label_part} {value_data.get("value", 0)}')
        
        return '\n'.join(lines)


# Global metrics registry
metrics = MetricsRegistry()


def get_metrics() -> MetricsRegistry:
    """Get the global metrics registry."""
    return metrics


def track_request(method: str, path: str, status_code: int, duration: float) -> None:
    """Track a request in metrics."""
    labels = {"method": method, "path": path, "status": str(status_code)}
    metrics.request_count.inc(labels)
    metrics.request_latency.observe(duration, labels)
    
    if status_code >= 400:
        error_labels = {"method": method, "path": path, "status": str(status_code)}
        metrics.error_count.inc(error_labels)
