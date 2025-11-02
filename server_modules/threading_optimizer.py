"""
Multi-threading Optimization Module
Optimizes concurrent operations and thread management
"""
import threading
import queue
import time
import concurrent.futures
from typing import Callable, Any, List, Dict
import logging
from functools import wraps

class ThreadPoolManager:
    """Advanced thread pool management with optimization"""
    
    def __init__(self, max_workers=None, thread_name_prefix="Monitor"):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.thread_name_prefix = thread_name_prefix
        
        # Create thread pools for different types of tasks
        self.io_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max(4, self.max_workers // 2),
            thread_name_prefix=f"{thread_name_prefix}_IO"
        )
        
        self.cpu_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max(2, self.max_workers // 4),
            thread_name_prefix=f"{thread_name_prefix}_CPU"
        )
        
        self.background_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max(2, self.max_workers // 4),
            thread_name_prefix=f"{thread_name_prefix}_BG"
        )
        
        # Task queues for priority handling
        self.high_priority_queue = queue.PriorityQueue()
        self.normal_priority_queue = queue.Queue()
        self.low_priority_queue = queue.Queue()
        
        # Performance tracking
        self.task_stats = {
            'submitted': 0,
            'completed': 0,
            'failed': 0,
            'avg_execution_time': 0
        }
        
        self.logger = logging.getLogger('ThreadPoolManager')
        self._shutdown = False
        
        # Start queue processing threads
        self._start_queue_processors()
    
    def _start_queue_processors(self):
        """Start threads to process priority queues"""
        threading.Thread(
            target=self._process_priority_queue,
            args=(self.high_priority_queue, "high"),
            daemon=True
        ).start()
        
        threading.Thread(
            target=self._process_priority_queue,
            args=(self.normal_priority_queue, "normal"),
            daemon=True
        ).start()
        
        threading.Thread(
            target=self._process_priority_queue,
            args=(self.low_priority_queue, "low"),
            daemon=True
        ).start()
    
    def _process_priority_queue(self, task_queue, priority_name):
        """Process tasks from priority queue"""
        while not self._shutdown:
            try:
                if isinstance(task_queue, queue.PriorityQueue):
                    priority, task_data = task_queue.get(timeout=1)
                else:
                    task_data = task_queue.get(timeout=1)
                
                func, args, kwargs, future = task_data
                
                if not future.cancelled():
                    try:
                        start_time = time.time()
                        result = func(*args, **kwargs)
                        execution_time = time.time() - start_time
                        
                        future.set_result(result)
                        self._update_stats('completed', execution_time)
                        
                    except Exception as e:
                        future.set_exception(e)
                        self._update_stats('failed')
                
                task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing {priority_name} priority queue: {e}")
    
    def _update_stats(self, stat_type, execution_time=None):
        """Update task statistics"""
        self.task_stats[stat_type] += 1
        
        if execution_time is not None:
            current_avg = self.task_stats['avg_execution_time']
            completed = self.task_stats['completed']
            
            # Calculate running average
            self.task_stats['avg_execution_time'] = (
                (current_avg * (completed - 1) + execution_time) / completed
            )
    
    def submit_io_task(self, func: Callable, *args, priority=1, **kwargs):
        """Submit IO-bound task"""
        future = concurrent.futures.Future()
        task_data = (func, args, kwargs, future)
        
        if priority == 0:  # High priority
            self.high_priority_queue.put((priority, task_data))
        elif priority == 1:  # Normal priority
            self.normal_priority_queue.put(task_data)
        else:  # Low priority
            self.low_priority_queue.put(task_data)
        
        self.task_stats['submitted'] += 1
        return future
    
    def submit_cpu_task(self, func: Callable, *args, **kwargs):
        """Submit CPU-bound task"""
        future = self.cpu_pool.submit(func, *args, **kwargs)
        self.task_stats['submitted'] += 1
        return future
    
    def submit_background_task(self, func: Callable, *args, **kwargs):
        """Submit background task"""
        future = self.background_pool.submit(func, *args, **kwargs)
        self.task_stats['submitted'] += 1
        return future
    
    def get_stats(self):
        """Get thread pool statistics"""
        return {
            'max_workers': self.max_workers,
            'active_threads': threading.active_count(),
            'task_stats': self.task_stats.copy(),
            'queue_sizes': {
                'high_priority': self.high_priority_queue.qsize(),
                'normal_priority': self.normal_priority_queue.qsize(),
                'low_priority': self.low_priority_queue.qsize()
            },
            'pool_stats': {
                'io_pool_threads': len(self.io_pool._threads),
                'cpu_pool_threads': len(self.cpu_pool._threads),
                'background_pool_threads': len(self.background_pool._threads)
            }
        }
    
    def shutdown(self, wait=True):
        """Shutdown all thread pools"""
        self._shutdown = True
        
        self.io_pool.shutdown(wait=wait)
        self.cpu_pool.shutdown(wait=wait)
        self.background_pool.shutdown(wait=wait)
        
        self.logger.info("Thread pools shut down")


class SmartQueue:
    """Intelligent queue with adaptive sizing and priority handling"""
    
    def __init__(self, max_size=1000, auto_scale=True):
        self.max_size = max_size
        self.auto_scale = auto_scale
        
        self._queue = queue.PriorityQueue(maxsize=max_size)
        self._item_count = 0
        self._dropped_items = 0
        self._processing_times = []
        
        self.logger = logging.getLogger('SmartQueue')
    
    def put(self, item, priority=1, timeout=None):
        """Put item in queue with priority"""
        try:
            if self._queue.full() and self.auto_scale:
                self._auto_scale_queue()
            
            queue_item = (priority, time.time(), self._item_count, item)
            self._queue.put(queue_item, timeout=timeout)
            self._item_count += 1
            
        except queue.Full:
            self._dropped_items += 1
            self.logger.warning(f"Queue full, dropped item (total dropped: {self._dropped_items})")
    
    def get(self, timeout=None):
        """Get item from queue"""
        try:
            priority, queued_time, item_id, item = self._queue.get(timeout=timeout)
            
            # Track processing time
            processing_time = time.time() - queued_time
            self._processing_times.append(processing_time)
            
            # Keep only recent processing times
            if len(self._processing_times) > 100:
                self._processing_times = self._processing_times[-50:]
            
            return item
            
        except queue.Empty:
            raise
    
    def _auto_scale_queue(self):
        """Automatically scale queue size based on usage"""
        if len(self._processing_times) > 10:
            avg_processing_time = sum(self._processing_times) / len(self._processing_times)
            
            # If processing is slow, increase queue size
            if avg_processing_time > 1.0:  # More than 1 second average
                new_size = min(self.max_size * 2, 5000)
                self.logger.info(f"Auto-scaling queue from {self.max_size} to {new_size}")
                self.max_size = new_size
    
    def qsize(self):
        return self._queue.qsize()
    
    def empty(self):
        return self._queue.empty()
    
    def full(self):
        return self._queue.full()


class TaskScheduler:
    """Advanced task scheduler with thread optimization"""
    
    def __init__(self, thread_manager: ThreadPoolManager):
        self.thread_manager = thread_manager
        self.scheduled_tasks = {}
        self.recurring_tasks = {}
        self._running = True
        
        self.logger = logging.getLogger('TaskScheduler')
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
    
    def schedule_once(self, func: Callable, delay: float, *args, **kwargs):
        """Schedule a function to run once after delay"""
        run_time = time.time() + delay
        task_id = f"once_{run_time}_{id(func)}"
        
        self.scheduled_tasks[task_id] = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'run_time': run_time,
            'recurring': False
        }
        
        return task_id
    
    def schedule_recurring(self, func: Callable, interval: float, *args, **kwargs):
        """Schedule a function to run repeatedly at interval"""
        run_time = time.time() + interval
        task_id = f"recurring_{interval}_{id(func)}"
        
        self.recurring_tasks[task_id] = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'interval': interval,
            'next_run': run_time
        }
        
        return task_id
    
    def cancel_task(self, task_id: str):
        """Cancel a scheduled task"""
        self.scheduled_tasks.pop(task_id, None)
        self.recurring_tasks.pop(task_id, None)
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self._running:
            try:
                current_time = time.time()
                
                # Process one-time tasks
                completed_tasks = []
                for task_id, task in self.scheduled_tasks.items():
                    if current_time >= task['run_time']:
                        self._execute_task(task)
                        completed_tasks.append(task_id)
                
                # Remove completed one-time tasks
                for task_id in completed_tasks:
                    del self.scheduled_tasks[task_id]
                
                # Process recurring tasks
                for task_id, task in self.recurring_tasks.items():
                    if current_time >= task['next_run']:
                        self._execute_task(task)
                        task['next_run'] = current_time + task['interval']
                
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(1)
    
    def _execute_task(self, task):
        """Execute a scheduled task"""
        try:
            # Submit to appropriate thread pool based on task type
            if 'io' in str(task['func']).lower():
                self.thread_manager.submit_io_task(
                    task['func'], *task['args'], **task['kwargs']
                )
            else:
                self.thread_manager.submit_background_task(
                    task['func'], *task['args'], **task['kwargs']
                )
        except Exception as e:
            self.logger.error(f"Error executing scheduled task: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        self._running = False


def threaded_task(pool_type='io', priority=1):
    """Decorator for automatic thread pool submission"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if pool_type == 'io':
                return thread_manager.submit_io_task(func, *args, priority=priority, **kwargs)
            elif pool_type == 'cpu':
                return thread_manager.submit_cpu_task(func, *args, **kwargs)
            else:
                return thread_manager.submit_background_task(func, *args, **kwargs)
        return wrapper
    return decorator


def batch_process(items: List[Any], func: Callable, batch_size=10, pool_type='io'):
    """Process items in batches using thread pool"""
    results = []
    futures = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        if pool_type == 'io':
            future = thread_manager.submit_io_task(lambda b=batch: [func(item) for item in b])
        elif pool_type == 'cpu':
            future = thread_manager.submit_cpu_task(lambda b=batch: [func(item) for item in b])
        else:
            future = thread_manager.submit_background_task(lambda b=batch: [func(item) for item in b])
        
        futures.append(future)
    
    # Collect results
    for future in concurrent.futures.as_completed(futures):
        try:
            batch_results = future.result()
            results.extend(batch_results)
        except Exception as e:
            logging.error(f"Batch processing error: {e}")
    
    return results


# Global thread manager instance
import os
thread_manager = ThreadPoolManager()
task_scheduler = TaskScheduler(thread_manager)