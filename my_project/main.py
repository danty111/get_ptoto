#!/usr/bin/python3
# encoding:utf-8
import json
import os
import asyncio
import threading
from datetime import datetime
from io import BytesIO
import logging
from logging.handlers import RotatingFileHandler
import flask
from PIL import Image
from flask import jsonify, abort, request, make_response
from common import IniFileEditor, MakePhotos, GetExcelValue
from ptojectAPI import MakePhoto, GetValue
from retrying import retry
import sys
import urllib.parse
from apscheduler.schedulers.background import BackgroundScheduler

sys.path.append(os.path.dirname(sys.path[0]))
config_file = os.path.abspath(__file__).split("/my_project")[0] + "/config.ini"



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

        image = Image.open(os.path.abspath(__file__).split("/main.py")[0]+"/my_html/templates/storage_boat/"+boat_name+".png")
    except Exception as e:
        return abort(400, description=str(e))
    buffer = BytesIO()
    image.convert('RGBA').save(buffer, format="PNG")
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
        image = MakePhoto("boat",name).make_boat()[0]
    except Exception as e:
        return abort(400, description=str(e))

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

scheduler = BackgroundScheduler()

@retry(stop_max_attempt_number=5, wait_fixed=4000)
async def get_all_boat():
    # 执行获取所有船只信息的函数
    # 如果函数执行失败，retrying 库会自动重试最多 5 次，每次重试之间等待 2 秒
    await asyncio.sleep(1)  # 模拟异步执行
    GetValue.get_all_boat()

def run_async_task():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(get_all_boat())
    loop.close()

def start_async_task():
    thread = threading.Thread(target=run_async_task)
    thread.start()

def schedule_async_task():
    scheduler.add_job(func=start_async_task, trigger='date', run_date=datetime.now())
    scheduler.add_job(func=start_async_task, trigger='interval', seconds=3600 * 12)
    scheduler.start()


if __name__ == '__main__':
    schedule_async_task()
    api.run(port=8888, host='0.0.0.0',debug=True)
    # image = MakePhoto("boat","术士").make_boat()
    # IniFileEditor().read_ini_file()
    # print(IniFileEditor().))

    # # 验证船体模版识别
    # print(IniFileEditor().read_ini_file())
    # section = json.loads(IniFileEditor().read_ini_file())
    # card=section["card"]
    # image = Aimage.open(section["boat_parameter_dictionary"]["template_path"])
    # MakePhotos(image).recognize_text(card["ttf_path"], card["font_size"]
    #                                                                       ,card["adjust_coor"]
    #                                                                       ,card["font_color"],card["save_path"])
    # # MakePhoto("card", 'fkbaicai').make_card()
    # # #识别船坐标
    # GetValue("drak_cutlass_black").get_boat()

    # MakePhoto("boat", 'anvl_carrack').make_boat()
