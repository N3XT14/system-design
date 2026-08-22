from abc import ABC, abstractmethod
from threading import Thread, Lock, Event
from enum import Enum
from datetime import datetime, timedelta
import time
import uuid


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
    def __init__(
        self,
        job: Job,
        run_at: datetime,
        interval: int = None
    ):
        self.id = str(uuid.uuid4())
        self.job = job
        self.run_at = run_at
        self.interval = interval

        self.status = JobStatus.SCHEDULED

        # Protects this job's mutable state.
        self._lock = Lock()

        # Used as the cancellation signal.
        self.cancel_event = Event()

    def cancel(self):
        with self._lock:
            if self.status in (
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED
            ):
                return False

            self.status = JobStatus.CANCELLED
            self.cancel_event.set()
            return True

    def mark_running(self):
        with self._lock:
            if self.status == JobStatus.CANCELLED:
                return False

            self.status = JobStatus.RUNNING
            return True

    def mark_completed(self):
        with self._lock:
            # Don't overwrite cancellation.
            if self.status != JobStatus.CANCELLED:
                self.status = JobStatus.COMPLETED

    def mark_failed(self):
        with self._lock:
            if self.status != JobStatus.CANCELLED:
                self.status = JobStatus.FAILED

    def reschedule(self):
        with self._lock:
            if self.status == JobStatus.CANCELLED:
                return False

            self.run_at += timedelta(
                seconds=self.interval
            )

            self.status = JobStatus.SCHEDULED
            return True

    def get_status(self):
        with self._lock:
            return self.status


class JobExecutor(Thread):
    def __init__(self, scheduled_job: ScheduledJob):
        super().__init__()
        self.scheduled_job = scheduled_job

    def run(self):
        job = self.scheduled_job

        while not job.cancel_event.is_set():

            now = datetime.now()

            if now < job.run_at:
                time.sleep(1)
                continue

            # Cancellation may have happened between
            # the while-check and this point.
            if job.cancel_event.is_set():
                break

            if not job.mark_running():
                break

            try:
                job.job.run()

            except Exception as e:
                print(
                    f"Job {job.id} failed: {e}"
                )
                job.mark_failed()
                break

            # One-time job
            if job.interval is None:
                job.mark_completed()
                break

            # Recurring job
            if job.cancel_event.is_set():
                break

            job.mark_completed()

            if not job.reschedule():
                break


class JobScheduler:
    def __init__(self):
        self.jobs = {}

        # Protects scheduler-level shared state:
        # the jobs dictionary.
        self._lock = Lock()

    def schedule(
        self,
        job: Job,
        run_at: datetime,
        interval: int = None
    ) -> str:

        scheduled_job = ScheduledJob(
            job=job,
            run_at=run_at,
            interval=interval
        )

        executor = JobExecutor(scheduled_job)

        # Only dictionary mutation needs this lock.
        with self._lock:
            self.jobs[
                scheduled_job.id
            ] = scheduled_job

        # Don't hold scheduler lock while starting thread.
        executor.start()

        return scheduled_job.id

    def cancel(self, job_id: str) -> bool:

        # Scheduler lock only needed for lookup.
        with self._lock:
            job = self.jobs.get(job_id)

        if job is None:
            return False

        # Job handles its own synchronization.
        return job.cancel()

    def list_jobs(self):
        # Make a snapshot first.
        with self._lock:
            jobs = list(self.jobs.items())

        # Don't keep scheduler lock while
        # reading individual job state.
        return [
            (
                job_id,
                job.get_status().value
            )
            for job_id, job in jobs
        ]


class PrintJob(Job):
    def __init__(self, message):
        self.message = message

    def run(self):
        print(
            f"[{datetime.now()}] "
            f"Running job: {self.message}"
        )


if __name__ == "__main__":

    scheduler = JobScheduler()

    # -------------------------
    # One-time job
    # -------------------------
    job1 = PrintJob("Say Hello")

    job1_id = scheduler.schedule(
        job1,
        run_at=datetime.now()
        + timedelta(seconds=3)
    )

    # -------------------------
    # Recurring job
    # -------------------------
    job2 = PrintJob("Recurring Job")

    job2_id = scheduler.schedule(
        job2,
        run_at=datetime.now()
        + timedelta(seconds=2),
        interval=3
    )

    time.sleep(7)

    # Cancel recurring job
    scheduler.cancel(job2_id)

    print("\nJobs:")

    for job_id, status in scheduler.list_jobs():
        print(job_id, status)
