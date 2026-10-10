from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
from datetime import datetime

scheduler = BackgroundScheduler()

def start_scheduler(check_emails_func, no_interview_check_func):
    # Check for new emails every 5 minutes
    scheduler.add_job(
        func=check_emails_func,
        trigger=IntervalTrigger(minutes=5),
        id='check_emails_job',
        name='Check for new interview emails',
        replace_existing=True,
        next_run_time=datetime.now()
    )
    
    # Check for no interviews every 30 minutes
    scheduler.add_job(
        func=no_interview_check_func,
        trigger=IntervalTrigger(minutes=30),
        id='no_interview_check_job',
        name='Check if no interviews found',
        replace_existing=True
    )
    
    scheduler.start()
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
