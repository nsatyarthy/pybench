# pybench
Python benchmark application to compare multiprocessing and threading libraries

$ ./pybench.py --help
usage: pybench.py [-h] (-t | -p) -w WORKERS [-s WORK_SIZE] [-m MAX_TIME]

optional arguments:
  -h, --help            show this help message and exit
  -t, --thread          use 'threading' library
  -p, --process         use 'multiprocessing' library
  -w WORKERS, --workers WORKERS
                        number of worker threads/processes
  -s WORK_SIZE, --work-size WORK_SIZE
                        work size
  -m MAX_TIME, --max-time MAX_TIME
                        exit after MAX_TIME seconds
---

A few examples of how to invoke it:

    ./pybench.py --thread -w4 -s100000000 -m10
    ./pybench.py --process -w4 -s100000000 -m10
    
