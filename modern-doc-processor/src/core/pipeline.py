# core/pipeline.py
import logging
from typing import List, Tuple, Callable, Dict, Any

logger = logging.getLogger("pipeline")

class Pipeline:
    """
    A flexible pipeline for document processing that chains multiple processing steps
    """
    
    def __init__(self, steps: List[Tuple[str, Callable]]):
        """
        Initialize the pipeline with a list of named processing steps
        
        Args:
            steps: List of tuples (step_name, step_function)
                  Each step_function should accept a document dict and return a modified document dict
        """
        self.steps = steps
        self.metrics = {step_name: {"success": 0, "error": 0, "time": 0} for step_name, _ in steps}
    
    def run(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the document through all processing steps in sequence
        
        Args:
            document: The document to process
            
        Returns:
            The processed document
        """
        current_doc = document.copy()
        current_doc["pipeline_steps"] = []
        
        for step_name, step_function in self.steps:
            logger.debug(f"Running pipeline step: {step_name}")
            
            try:
                import time
                start_time = time.time()
                
                # Run the step
                current_doc = step_function(current_doc)
                
                # Record metrics
                duration = time.time() - start_time
                self.metrics[step_name]["success"] += 1
                self.metrics[step_name]["time"] += duration
                
                # Record in document
                current_doc["pipeline_steps"].append({
                    "step": step_name,
                    "status": "success",
                    "duration": duration
                })
                
                logger.debug(f"Step {step_name} completed in {duration:.2f}s")
                
            except Exception as e:
                logger.error(f"Error in pipeline step {step_name}: {str(e)}")
                self.metrics[step_name]["error"] += 1
                
                # Record in document
                current_doc["pipeline_steps"].append({
                    "step": step_name,
                    "status": "error",
                    "error": str(e)
                })
                
                # Re-raise if this is a critical step
                if getattr(step_function, "critical", False):
                    raise
        
        return current_doc
    
    def get_metrics(self) -> Dict[str, Dict]:
        """
        Get metrics for pipeline steps
        
        Returns:
            A dictionary of metrics for each step
        """
        result = {}
        
        for step_name, metrics in self.metrics.items():
            total = metrics["success"] + metrics["error"]
            avg_time = metrics["time"] / metrics["success"] if metrics["success"] > 0 else 0
            
            result[step_name] = {
                "total": total,
                "success": metrics["success"],
                "error": metrics["error"],
                "success_rate": metrics["success"] / total if total > 0 else 0,
                "avg_time": avg_time
            }
            
        return result

def critical(func):
    """
    Decorator to mark a pipeline step as critical
    Critical steps will cause the pipeline to stop if they fail
    """
    func.critical = True
    return func