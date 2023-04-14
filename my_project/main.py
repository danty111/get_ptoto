#!/usr/bin/python3
# encoding:utf-8
import json
import os
from io import BytesIO
import logging
from logging.handlers import RotatingFileHandler
import flask
from PIL.Image import Image

from flask import jsonify, abort, request, make_response
from common import IniFileEditor
from ptojectAPI import MakePhoto
from retrying import retry
import sys

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
                    pro_path = "/my_project/my_html/templates/"
                file_path = IniFileEditor().file_path.split("/config.ini")[0]
                value = pro_path + IniFileEditor().get_value(section, option).split("/")[-1]
                config.set(section, option, file_path + value)
    with open(IniFileEditor().file_path, 'w') as configfile:
        config.write(configfile)


init_app()

api = flask.Flask(__name__)

# 配置日志记录器
handler = RotatingFileHandler(f'{os.path.abspath(__file__).split("/my_project")[0]}/my_logs/app.log', maxBytes=1024*1024*10, backupCount=5)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
handler.setFormatter(formatter)
api.logger.addHandler(handler)


@api.route('/card', methods=['GET'])
@retry(stop_max_attempt_number=6, wait_fixed=300)
def card():
    try:
        name = request.args.get('name')
        image = MakePhoto().make_card(name)
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


if __name__ == '__main__':
    api.run(port=8888, host='0.0.0.0',debug=True)
    # print(IniFileEditor().))

