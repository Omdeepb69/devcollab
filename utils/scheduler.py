import logging
from typing import Dict, Any, Callable, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        """Initialize the task scheduler with default configuration."""
        # Configure job stores and executors
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(20)
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        # Create and configure the scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        # Start the scheduler
        self.scheduler.start()
        logger.info("Task scheduler initialized and started")
    
    def schedule_task(self, 
                     func: Callable, 
                     args: Optional[tuple] = None, 
                     kwargs: Optional[Dict] = None, 
                     run_date: Optional[datetime] = None,
                     minutes_from_now: Optional[int] = None,
                     job_id: Optional[str] = None) -> Dict:
        """
        Schedule a task to run at a specific time or after a delay.
        
        Args:
            func (callable): Function to execute
            args (tuple, optional): Positional arguments for the function
            kwargs (dict, optional): Keyword arguments for the function
            run_date (datetime, optional): Specific datetime to run the task
            minutes_from_now (int, optional): Minutes from now to run the task
            job_id (str, optional): Unique identifier for the job
            
        Returns:
            dict: Information about the scheduled job
        """
        try:
            # Set default values
            args = args or ()
            kwargs = kwargs or {}
            
            # Calculate run_date if minutes_from_now is provided
            if minutes_from_now is not None and run_date is None:
                run_date = datetime.now() + timedelta(minutes=minutes_from_now)
            
            # Schedule the job
            job = self.scheduler.add_job(
                func=func,
                args=args,
                kwargs=kwargs,
                trigger='date',
                run_date=run_date,
                id=job_id,
                replace_existing=True
            )
            
            logger.info(f"Task scheduled with ID {job.id} to run at {run_date}")
            
            return {
                "status": "success",
                "job_id": job.id,
                "scheduled_time": run_date.isoformat() if run_date else None
            }
        
        except Exception as e:
            logger.error(f"Error scheduling task: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to schedule task: {str(e)}"
            }
    
    def cancel_task(self, job_id: str) -> Dict:
        """
        Cancel a scheduled task.
        
        Args:
            job_id (str): ID of the job to cancel
            
        Returns:
            dict: Status of the operation
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Task with ID {job_id} cancelled")
            
            return {
                "status": "success",
                "message": f"Task with ID {job_id} cancelled successfully"
            }
        
        except Exception as e:
            logger.error(f"Error cancelling task: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to cancel task: {str(e)}"
            }
    
    def get_pending_tasks(self) -> Dict:
        """
        Get all pending scheduled tasks.
        
        Returns:
            dict: List of pending tasks with their details
        """
        try:
            jobs = self.scheduler.get_jobs()
            pending_tasks = []
            
            for job in jobs:
                pending_tasks.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "func": str(job.func),
                    "args": job.args,
                    "kwargs": job.kwargs
                })
            
            return {
                "status": "success",
                "tasks": pending_tasks
            }
        
        except Exception as e:
            logger.error(f"Error retrieving pending tasks: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to retrieve pending tasks: {str(e)}"
            }
    
    def shutdown(self):
        """Shut down the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Task scheduler shut down")