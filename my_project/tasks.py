import multiprocessing
from datetime import time

from ptojectAPI import BoatPhoto


def cronJob():
    BoatPhoto().carry_out_boat()
cronJob()