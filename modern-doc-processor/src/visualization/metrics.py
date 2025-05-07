# src/visualization/metrics.py
import logging
import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

class MetricsVisualizer:
    """Generates visualization for document processing metrics"""
    
    def __init__(self, metrics_dir=None):
        self.metrics_dir = Path(metrics_dir or "data/metrics")
        self.metrics_dir.mkdir(exist_ok=True, parents=True)
        
        self.output_dir = Path("data/visualizations")
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
    def load_metrics(self, days=30):
        """Load processing metrics from files"""
        metrics = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for metrics_file in self.metrics_dir.glob("run_*.json"):
            try:
                with open(metrics_file, "r") as f:
                    run_metrics = json.load(f)
                    
                # Check if within time range
                start_time = datetime.fromisoformat(run_metrics["start_time"])
                if start_time >= cutoff_date:
                    metrics.append(run_metrics)
                    
            except Exception as e:
                logger.error(f"Error loading metrics file {metrics_file}: {str(e)}")
                
        return metrics
        
    def generate_visualizations(self, days=30):
        """Generate visualizations for metrics"""
        metrics = self.load_metrics(days=days)
        
        if not metrics:
            logger.warning("No metrics data available")
            return
            
        # Extract document-level data
        doc_results = []
        for run in metrics:
            for result in run["results"]:
                if "class" in result:
                    doc_results.append({
                        "id": result["id"],
                        "class": result["class"],
                        "confidence": result.get("confidence", 0),
                        "processing_time": result.get("processing_time", 0),
                        "status": result["status"],
                        "run_time": run["start_time"]
                    })
                    
        # Convert to DataFrame
        df = pd.DataFrame(doc_results)
        
        # Convert run_time to datetime
        df["run_time"] = pd.to_datetime(df["run_time"])
        
        # Plot document count by class
        self._plot_document_count_by_class(df)
        
        # Plot processing time by class
        self._plot_processing_time_by_class(df)
        
        # Plot confidence by class
        self._plot_confidence_by_class(df)
        
        # Plot success rate over time
        self._plot_success_rate_over_time(df)
        
    def _plot_document_count_by_class(self, df):
        """Plot document count by class"""
        plt.figure(figsize=(10, 6))
        
        doc_counts = df["class"].value_counts()
        doc_counts.plot(kind="bar", color="skyblue")
        
        plt.title("Document Count by Class")
        plt.xlabel("Document Class")
        plt.ylabel("Count")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig(self.output_dir / "document_count_by_class.png")
        plt.close()
        
    def _plot_processing_time_by_class(self, df):
        """Plot processing time by class"""
        plt.figure(figsize=(10, 6))
        
        # Calculate average processing time by class
        proc_time = df.groupby("class")["processing_time"].mean().sort_values(ascending=False)
        proc_time.plot(kind="bar", color="lightgreen")
        
        plt.title("Average Processing Time by Class")
        plt.xlabel("Document Class")
        plt.ylabel("Processing Time (seconds)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig(self.output_dir / "processing_time_by_class.png")
        plt.close()
        
    def _plot_confidence_by_class(self, df):
        """Plot confidence by class"""
        plt.figure(figsize=(10, 6))
        
        # Calculate average confidence by class
        confidence = df.groupby("class")["confidence"].mean().sort_values(ascending=False)
        confidence.plot(kind="bar", color="salmon")
        
        plt.title("Average Classification Confidence by Class")
        plt.xlabel("Document Class")
        plt.ylabel("Confidence")
        plt.xticks(rotation=45)
        plt.ylim(0, 1)
        plt.tight_layout()
        
        plt.savefig(self.output_dir / "confidence_by_class.png")
        plt.close()
        
    def _plot_success_rate_over_time(self, df):
        """Plot success rate over time"""
        plt.figure(figsize=(12, 6))
        
        # Convert run_time to date
        df["date"] = df["run_time"].dt.date
        
        # Calculate success rate by date
        success_rate = df.groupby("date")["status"].apply(
            lambda x: (x == "completed").sum() / len(x)
        )
        
        success_rate.plot(kind="line", marker="o", color="teal")
        
        plt.title("Document Processing Success Rate Over Time")
        plt.xlabel("Date")
        plt.ylabel("Success Rate")
        plt.ylim(0, 1.05)
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        
        plt.savefig(self.output_dir / "success_rate_over_time.png")
        plt.close()