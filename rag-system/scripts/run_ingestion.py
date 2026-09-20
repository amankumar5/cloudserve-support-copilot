import sys
import os
import asyncio

# Ensure parent path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ingestion.pipeline import ingestion_pipeline
from app.storage.metadata_db import metadata_db
from app.core.logging import logger


def main():
    logger.info("Starting manual ingestion sync script...")
    folder_id = sys.argv[1] if len(sys.argv) > 1 else None
    job_id = ingestion_pipeline.start_ingestion_job(folder_id=folder_id, force_resync=True)

    print(f"Ingestion job started with ID: {job_id}")
    print("Polling job status...")

    while True:
        job = metadata_db.get_job(job_id)
        if not job:
            print("Job not found.")
            break

        status = job["status"]
        progress = job["progress_percentage"]
        print(f"Status: {status} | Progress: {progress:.1f}% ({job['files_processed']}/{job['files_total']})")

        if status in ["completed", "completed_with_errors", "failed"]:
            print(f"Ingestion job finished with status: {status}")
            if job["errors"]:
                print(f"Errors encountered ({len(job['errors'])}):")
                for err in job["errors"]:
                    print(f" - {err}")
            break

        import time
        time.sleep(2)


if __name__ == "__main__":
    main()
