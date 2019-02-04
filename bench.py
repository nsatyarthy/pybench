#!/usr/bin/python2
import sys
import time
import signal
import argparse
import threading
import multiprocessing

class Worker:
    """A worker could be either thread-based or process-based"""
    
    start_time = time.time()
    
    def __init__(self, wid, job, job_size, timeout):
        self._wid = wid
        self._job = job
        self._job_size = job_size
        self._timeout = timeout
        self._work = []
        self._begin = self._wid * self._job_size
        self._end = self._begin + self._job_size

    @classmethod
    def task(cls, n, end, ret, timeout, stop_cond):
        end_time = Worker.start_time + timeout
        while not stop_cond() and n != end:
            if n % 2 == 0:
                ret.append(n)
            n += 1
            if timeout > 0:
                curr_time = time.time()
                if curr_time > end_time:
                    return
            
class ThreadWorker(Worker):
    """A thread-based worker"""
    
    stopper = threading.Event()
    threads = []

    @classmethod
    def task(cls, wid, n, end, ret, timeout, cond):
        Worker.task(n, end, ret, timeout, cond)

    @classmethod
    def stop(cls):
        cls.stopper.set()

    @classmethod
    def is_stopped(cls):
        return cls.stopper.is_set()

    @classmethod
    def wait_till_active(cls):
        is_any_worker_alive = any([x.is_alive() for x in ThreadWorker.threads])
        while is_any_worker_alive:
            time.sleep(0)
            is_any_worker_alive = any([x.is_alive() for x in ThreadWorker.threads])

    def __init__(self, wid, job, job_size, timeout):
        Worker.__init__(self, wid, job, job_size, timeout)
        ThreadWorker.threads.append(self)
        self._thread = None

    def print_result(self):
        return len(self._work)
            
    def start(self):
        self._thread = threading.Thread(target=self._job,
            args=(self._wid, self._begin, self._end, self._work, self._timeout, ThreadWorker.is_stopped))
        self._thread.start()

    def is_alive(self):
        if self._thread is not None and self._thread.is_alive():
            return True
        else:
            return False

class ProcessWorker(Worker):
    """A process-based worker"""
    
    stopper = False
    processes = []

    @classmethod
    def task(cls, wid, n, end, ret, timeout, cond):
        r = []
        Worker.task(n, end, r, timeout, cond)
        ret.put(r)

    @classmethod
    def stop(cls):
        cls.stopper = True
    
    @classmethod
    def is_stopped(cls):
        return cls.stopper

    @classmethod
    def wait_till_active(cls):
        while any([x.is_alive() for x in ProcessWorker.processes]):
            time.sleep(0)

    def __init__(self, wid, job, job_size, timeout):
        Worker.__init__(self, wid, job, job_size, timeout)
        self._process = None
        self._work = multiprocessing.Queue()

    def print_result(self):
        val = self._work.get()
        return len(val)
            
    def start(self):
        self._process = multiprocessing.Process(target=self._job,
            args=(self._wid, self._begin, self._end, self._work, self._timeout, ProcessWorker.is_stopped))
        self._process.start()

    def is_alive(self):
        if self._process is not None and self._process.is_alive():
            return True
        else:
            return False

def parse_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-t', '--thread', action='store_true', help='use \'threading\' library')
    group.add_argument('-p', '--process', action='store_true', help='use \'multiprocessing\' library')

    parser.add_argument('-w', '--workers', action='store', type=int, required=True, help='number of worker threads/processes')
    parser.add_argument('-s', '--work-size', action='store', type=int, default=10000000000, help='work size')
    parser.add_argument('-m', '--max-time', action='store', type=int, default=0, help='exit after MAX_TIME seconds')
    args = parser.parse_args()
    return args

def allocate_work(cmd_args):
    use_threads = cmd_args.thread
    work_size = cmd_args.work_size
    n_workers = cmd_args.workers
    work_unit = work_size / n_workers
    timeout = cmd_args.max_time
    ws = None
    print 'Test parameters:\n\n', \
     ('     threads  : ' if use_threads else '    processes : ') + str(n_workers) + '\n', \
      '     job size : ' + str(work_size) + '\n', \
     ('     timeout  : ' + str(timeout) + '\n') if timeout > 0 else '\n'
    
    Worker.start_time = time.time()
    if use_threads:
        ws = [ThreadWorker(i, ThreadWorker.task, work_unit, timeout) for i in range(0, n_workers)]
    else:
        ws = [ProcessWorker(i, ProcessWorker.task, work_unit, timeout) for i in range(0, n_workers)]

    print 'Running...'
    return ws

def main():
    args = parse_args()
    workers = allocate_work(args)
    executor = ThreadWorker if args.thread else ProcessWorker

    def signal_handler(sig, frame):
        """KeyboardInterrupt handler
        
        Regardless of the kind of workers (thread or process), the 
        keyboard interrupt is captured and all workers are then
        cautioned to exit gracefully. 

        """
        executor.stop()
    signal.signal(signal.SIGINT, signal_handler)

    for w in workers:
        w.start()

    executor.wait_till_active()

    result = [w.print_result() for w in workers]
    total_time = time.time() - executor.start_time

    print 'Done\n\nWork done by each worker: \n'
    for idx, val in enumerate(result):
        print '     worker ' + str(idx) + ' : ' + str(val) + '  [' + str(round((val*200.0 / args.work_size), 2)) + ' %]'
    print '\nTotal work done      : ', str(2 * sum(result)), '  [' + str(round(2.0 * sum(result) * 100.0 / args.work_size, 2)) + ' %]' 
    print 'Total execution time : ', str(round(total_time, 2)), 'seconds'
    
if __name__ == "__main__":
    main()
