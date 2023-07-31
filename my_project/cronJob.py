import signal
import threading

from apscheduler.schedulers.background import BackgroundScheduler

from ptojectAPI import BoatPhoto


def signal_handler(signum, frame):
    print(f"Received signal {signum}, stopping server gracefully")

def main():
    # 创建一个 BoatPhoto 对象
    boat_photo = BoatPhoto()

    # 创建一个线程，异步执行方法
    get_all_boat_thread = threading.Thread(target=boat_photo.get_all_boat)
    get_all_boat_thread.start()

    # 在主线程中注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)
    scheduler = BackgroundScheduler()
    # 定义一个任务，每个小时执行一次
    scheduler.add_job(BoatPhoto.get_all_boat, 'interval', minutes=5, replace_existing=True, id='get_photo')
    print("启动定时任务")
    # 启动定时任务调度器
    scheduler.start()

main()