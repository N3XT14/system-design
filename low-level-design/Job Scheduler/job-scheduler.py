from abc import ABC, abstractmethod
from threading import Thread, Lock, Event
from enum import Enum
import time
import uuid
from datetime import datetime, timedelta

class Job(ABC):
    @abstractmethod
    def run(self):
        pass
    
class JobStatus(Enum):
    SCHEDULED = "Scheduled"
    RUNNING = "Running"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    FAILED = "Failed"

class ScheduledJob:
    def __init__(self, job: Job, run_at: datetime, interval: int = None):
        self.id = str(uuid.uuid4())
        self.job = job
        self.run_at = run_at
        self.interval = interval  # in seconds (if recurring)
        self.status = JobStatus.SCHEDULED
        self.lock = Lock()
        self.cancel_event = Event()

    def cancel(self):
        with self.lock:
            self.status = JobStatus.CANCELLED
            self.cancel_event.set()

class JobExecutor(Thread):
    def __init__(self, scheduled_job: ScheduledJob):
        super().__init__()
        self.scheduled_job = scheduled_job

    def run(self):
        job = self.scheduled_job
        while not job.cancel_event.is_set():
            now = datetime.now()
            if now >= job.run_at:
                job.status = JobStatus.RUNNING
                try:
                    job.job.run()
                    job.status = JobStatus.COMPLETED
                except Exception as e:
                    print(f"Job {job.id} failed: {e}")
                    job.status = JobStatus.FAILED

                if job.interval is None:
                    break  # One-time job
                else:
                    job.run_at += timedelta(seconds=job.interval)
                    job.status = JobStatus.SCHEDULED
            time.sleep(1)

class JobScheduler:
    def __init__(self):
        self.jobs = {}
        self.lock = Lock()

    def schedule(self, job: Job, run_at: datetime, interval: int = None) -> str:
        scheduled_job = ScheduledJob(job, run_at, interval)
        executor = JobExecutor(scheduled_job)

        with self.lock:
            self.jobs[scheduled_job.id] = scheduled_job
            executor.start()

        return scheduled_job.id

    def cancel(self, job_id: str) -> bool:
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job.cancel()
                return True
            return False

    def list_jobs(self):
        with self.lock:
            return [(job_id, job.status.name) for job_id, job in self.jobs.items()]

class PrintJob(Job):
    def __init__(self, message):
        self.message = message

    def run(self):
        print(f"[{datetime.now()}] Running job: {self.message}")

if __name__ == "__main__":
    scheduler = JobScheduler()
    job1 = PrintJob("Say Hello")
    
    # Schedule job after 3 seconds
    job_id = scheduler.schedule(job1, run_at=datetime.now() + timedelta(seconds=3))
    
    time.sleep(6)
    print(scheduler.list_jobs())
