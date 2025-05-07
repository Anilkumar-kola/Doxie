import os

structure = {
    "modern-doc-processor": [
        "src/collection/collector.py",
        "src/collection/connectors/",
        "src/preprocessing/processor.py",
        "src/preprocessing/image_enhancer.py",
        "src/preprocessing/ocr_engine.py",
        "src/classification/classifier.py",
        "src/classification/zero_shot.py",
        "src/classification/models/",
        "src/extraction/extractor.py",
        "src/extraction/rag_engine.py",
        "src/extraction/schemas/",
        "src/integration/integrator.py",
        "src/integration/vector_store.py",
        "src/integration/relation_store.py",
        "src/visualization/api.py",
        "src/visualization/metrics.py",
        "src/core/config.py",
        "src/core/models.py",
        "src/core/pipeline.py",
        "ui/src/components/",
        "ui/src/pages/",
        "ui/src/api/",
        "ui/src/hooks/",
        "api/routes/",
        "api/controllers/",
        "api/middleware/",
        "workers/collector_worker.py",
        "workers/processor_worker.py",
        "workers/integration_worker.py",
        "deployment/docker/",
        "deployment/kubernetes/",
        "deployment/terraform/",
        "tools/model_trainer/",
        "tools/data_generators/",
        "notebooks/"
    ]
}

def create_structure(base_path, items):
    for item in items:
        full_path = os.path.join(base_path, item)
        if full_path.endswith("/"):
            os.makedirs(full_path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write("")  # create empty file

if __name__ == "__main__":
    for root, paths in structure.items():
        create_structure(root, paths)
    print("✅ Project structure created successfully!")
