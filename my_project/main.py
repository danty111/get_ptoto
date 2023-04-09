#!/usr/bin/python3
# encoding:utf-8
import json
import os
from io import BytesIO

import flask

from flask import jsonify, abort, request, make_response
from my_project.common import IniFileEditor
from my_project.ptojectAPI import MakePhoto
from retrying import retry
import sys

sys.path.append(os.path.dirname(sys.path[0]))
config_file = os.getcwd().split("/my_project")[0] + "/config.ini"


def init_app():
    config = IniFileEditor().config
    for section in config.sections():
        for option in config.options(section):
            value = config.get(section, option)
            if '/' in value:
                file_path = IniFileEditor().file_path.split("/config.ini")[0]
                value = IniFileEditor().get_value(section, option).split("/")[-1]
                print(file_path + value)
                config.set(section, option, file_path + value)
    with open(IniFileEditor().file_path, 'w') as configfile:
        config.write(configfile)

        
init_app()

api = flask.Flask(__name__)




@api.route('/card', methods=['GET'])
@retry(stop_max_attempt_number=3, wait_fixed=1000)
def card():
    try:
        name = request.args.get('name')
        image = MakePhoto().make_card(name)
    except Exception as e:
        raise e

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
    api.run(port=8888, host='0.0.0.0')
    # print(IniFileEditor().))
