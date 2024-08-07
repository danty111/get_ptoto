#!/usr/bin/python3
# encoding:utf-8
import asyncio
import concurrent.futures
import multiprocessing
import os
import profile
import signal
import subprocess
import threading
import time
from io import BytesIO
import logging
from logging.handlers import RotatingFileHandler
import flask
from PIL import Image
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from flask import jsonify, abort, request, make_response
from common import IniFileEditor, GetExcelValue, common_method
from ptojectAPI import MakePhoto, GetValue,BoatPhoto
from retrying import retry
import sys
import urllib.parse

sys.path.append(os.path.dirname(sys.path[0]))
config_file = os.path.abspath(__file__).split("/my_project")[0] + "/config.ini"

import socket

def check_port(port):
    """
    检查端口是否被占用
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # 设置超时时间为1秒
        s.settimeout(1)
        try:
            s.bind(("localhost", port))
            return True
        except socket.error as e:
            print(f"端口{port}已被占用")
            return False

def close_port(port):
    """
    关闭指定端口上的进程
    """
    try:
        output = subprocess.check_output(['sudo', 'lsof', '-ti', f'tcp:{port}'])
        pids = output.strip().decode('utf-8').split('\n')
        for pid in pids:
            subprocess.run(['sudo', 'kill', pid])
        print(f"端口{port}上的进程已被关闭")
    except subprocess.CalledProcessError:
        print(f"端口{port}未被占用")


def init_app():
    """
    预处理：将ini文件的地址根据当前项目地址更换，
    用相对地址总是有莫名其妙的问题，懒得查了
    :return:
    """
    config = IniFileEditor().config
    for section in config.sections():
        for option in config.options(section):
            value = config.get(section, option)
            if '/' in value:
                if "save" in value:
                    pro_path = "/my_project/my_html/"
                else:
                    if "card" in section:
                        model = "/card/"
                    elif "boat" in section:
                        model = "/boat/"
                    else:
                        raise Exception("配置文件错误")
                    pro_path = "/my_project/my_html/templates" + model
                file_path = IniFileEditor().file_path.split("/config.ini")[0]
                value = pro_path + IniFileEditor().get_value(section, option).split("/")[-1]
                config.set(section, option, file_path + value)
    with open(IniFileEditor().file_path, 'w') as configfile:
        config.write(configfile)






init_app()
api = flask.Flask(__name__)
api.debug = True


# 配置日志记录器
handler = RotatingFileHandler(f'{os.path.abspath(__file__).split("/my_project")[0]}/my_logs/app.log', maxBytes=1024*1024*10, backupCount=5)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
handler.setFormatter(formatter)
api.logger.addHandler(handler)


@api.route('/card', methods=['GET'])
@retry(stop_max_attempt_number=3, wait_fixed=300)
def card():
    try:
        name = request.args.get('name')
        image = MakePhoto("card",name).make_card()
    except Exception as e:
        return abort(400, description=str(e))

    buffer = BytesIO()
    image.convert('RGBA').save(buffer, format="PNG")
    buffer.seek(0)

    # 将图像作为响应内容返回
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "image/png"
    return response

@api.route('/boat', methods=['GET'])
@retry(stop_max_attempt_number=3, wait_fixed=300)
def boat():
    try:
        name = request.args.get('name')
        name = urllib.parse.unquote(name)
        config = IniFileEditor().get_value("boat","boat_name_excel")
        boat_name = GetExcelValue(name).get_boat_name(config)[0]
        image = Image.open(os.path.abspath(__file__).split("/main.py")[0]+"/my_html/templates/storage_boat/"+boat_name+".jpeg")
    except Exception as e:
        return abort(400, description=str(e))
    buffer = BytesIO()
    image.convert('RGB').save(buffer, format="jpeg")
    buffer.seek(0)

    # 将图像作为响应内容返回
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "image/png"
    return response




@api.route('/boa_real_time', methods=['GET'])
@retry(stop_max_attempt_number=3, wait_fixed=300)
def boat_real_time():
    try:
        name = request.args.get('name')
        name = urllib.parse.unquote(name)
        image = Image.open(os.path.abspath(__file__).split("/main.py")[0]+"/my_html/templates/renewal_pic/img.png")
    except Exception as e:
        return abort(400, description=str(e))
    buffer = BytesIO()
    image.convert('RGB').save(buffer, format="jpeg")
    buffer.seek(0)
    # 将图像作为响应内容返回
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "image/png"
    if name == "更新数据":
        get_all_boat_thread = threading.Thread(target=BoatPhoto().get_all_boat)
        get_all_boat_thread.start()
        logging.info("启动船只更新")
    # try:
    #     name = request.args.get('name')
    #     name = urllib.parse.unquote(name)
    #     image = MakePhoto("boat",name).make_boat()[0]
    # except Exception as e:
    #     return abort(400, description=str(e))

    buffer = BytesIO()
    image.convert('RGBA').save(buffer, format="PNG")
    buffer.seek(0)

    # 将图像作为响应内容返回
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "image/png"

    return response


@api.route('/set_card_temple', methods=['POST'])
def set_card_template():
    req_data = request.get_json()
    if not req_data:
        abort(400, description='Missing request data')

    for key, value in req_data.items():
        if not isinstance(value, tuple):
            abort(400, description='Invalid value type for key: {}'.format(key))

    message = IniFileEditor().write_value("card_template", req_data)
    if "成功" in message:
        return jsonify({'message': message})
    else:
        return abort(400, description='以下字段与接口参数不同:{}'.format(message))



if __name__ == '__main__':

    # 启动 API 服务

    api.run(port=8888, host='0.0.0.0',debug=False)
