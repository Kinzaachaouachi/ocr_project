from typing import List, Optional

from pydantic import BaseModel


class BenchmarkMetrics(BaseModel):
    precision: float = 0.0
    execution_time: float = 0.0
    init_time: float = 0.0
    robustness: float = 0.0
    global_score: float = 0.0


class ModelBenchmark(BaseModel):
    model_id: str
    model_name: str
    extractions_count: int = 0
    avg_precision: float = 0.0
    avg_execution_time: float = 0.0
    avg_init_time: float = 0.0
    avg_robustness: float = 0.0
    avg_global_score: float = 0.0


class DashboardStats(BaseModel):
    total_extractions: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    success_rate: float = 0.0
    overall_metrics: BenchmarkMetrics
    model_benchmarks: List[ModelBenchmark] = []
    file_type_distribution: dict = {}
    recent_extractions: list = []
