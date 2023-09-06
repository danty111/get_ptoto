import multiprocessing
from datetime import time

from ptojectAPI import BoatPhoto


def run_boat_task():
    BoatPhoto().carry_out_boat()

if __name__ == '__main__':
    run_boat_task()