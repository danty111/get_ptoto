import ast
import configparser
import copy
import json
import os
from typing import List, Dict, Any

import numpy as np
import requests
from lxml import html

from io import BytesIO
from pprint import pprint
import requests
from cnocr import CnOcr
from lxml import etree
from PIL import Image, ImageDraw, ImageFont

config_file = os.getcwd().split("/my_project")[0]+"/config.ini"




class HttpStatus:
    def __init__(self, response):
        self.response = response
        self.status_code = response.status_code
        self.reason = response.reason

    def is_success(self):
        return self.status_code >= 200 and self.status_code < 300

    def is_redirect(self):
        return self.status_code >= 300 and self.status_code < 400

    def is_client_error(self):
        return self.status_code >= 400 and self.status_code < 500

    def is_server_error(self):
        return self.status_code >= 500 and self.status_code < 600

    def is_error(self):
        return self.status_code >= 400

    def __str__(self):
        return f'{self.status_code} {self.reason}'


class Request:
    def __init__(self, headers=None, cookies=None):
        self.session = requests.Session()
        self.headers = headers
        self.cookies = cookies

    @staticmethod
    def get_html(path):
        """
        直接获取页面的html使用
        :param path:
        :param vale_dict:
        :return:
        """
        return requests.get(path).text

    def get(self, url, params=None):
        return self._send_request('GET', url, params=params)

    def post(self, url, data=None, json=None):
        return self._send_request('POST', url, data=data, json=json)

    @staticmethod
    def get_json(my_str):
        try:
            my_dict = json.loads(my_str)
            return my_dict
        except Exception as e:
            print("发生异常：", e)

    def _send_request(self, method, url, params=None, data=None, json=None):
        response = self.session.request(
            method,
            url,
            headers=self.headers,
            cookies=self.cookies,
            params=params,
            data=data,
            json=json
        )
        response.raise_for_status()
        return response


class GetValue():
    def __init__(self, name):
        self.name = name

    def get_card(self):
        """
        获取名片的内容
        :param name:查询者的名字
        :return:
        """
        res = Request.get_html(f"https://robertsspaceindustries.com/citizens/{self.name}")
        res_organizations = Request.get_html(f"https://robertsspaceindustries.com/citizens/{self.name}/organizations")
        #判断是否存在用户
        if "You are currently venturing unknown space" not in res:
            _element = etree.HTML(res)
            _element_org = etree.HTML(res_organizations)
            #获取用户信息
            text = _element.xpath('//*[@class="inner clearfix"]/*[@class="info"]//p//text()')
            #获取舰队信息
            tex1 = _element.xpath("//*[@class='left-col']//text()")

            jud_visibility = _element.xpath('//*[@class="member-visibility-restriction member-visibility-r trans-03s"]')

            empty_ass = _element.xpath('//*[@class="empty"]')
            empry_ass_num = _element_org.xpath('//*[@class="empty"]')
            # 兼容舰队隐藏的问题
            if len(jud_visibility) == 0 and len(empty_ass)==0:
                #获取舰队信息
                image_ass = _element.xpath('//*[@class="thumb"]/a/img/@src')[0]
                if "cdn" not in image_ass:
                    image_ass = "https://robertsspaceindustries.com/" + image_ass
            else:
                if len(empty_ass)==0:
                    image_ass = _element.xpath("//*[@class='thumb']/img/@src")[1]
                    text.append("organization")
                    text.append("无权限查看")
                    text.append("organization_rank")
                    text.append("无权限查看")
                else:
                    text.append("organization")
                    text.append("无")
                    text.append("organization_rank")
                    text.append("-")
                    image_ass = "need_empty"


            # 获取用户头像
            image_user = _element.xpath("//*[@class='thumb']/img/@src")[0]
            # 获取徽章信息
            image_medal = _element.xpath('//*[@class="icon"]/img/@src')[0]
            if "https" not in image_medal:
                image_medal = "https://robertsspaceindustries.com" + image_medal
            if "https" not in image_user:
                image_user = "https://robertsspaceindustries.com" + image_user
            if len(empry_ass_num) == 0:
                image_ass_num = len(_element_org.xpath('//*[@class="profile-content orgs-content clearfix"]/div'))
            else:
                image_ass_num = 0
            list = text + tex1
            text = [x.strip() for x in list if x.strip() != '']
            text.insert(0, "id")
            text.insert(4, "medal")
            if len(jud_visibility) == 0 and len(empty_ass) == 0:
                text.insert(6, "organization")
            key, value = [], []
            for i in range(len(text)):
                if "\n" in text[i] or "\r" in text[i]:
                    text[i] = text[i].replace('\n', '').replace('\r', '')
                if i % 2 == 0:
                    key.append(text[i])
                else:
                    if " " in text[i]:
                        text[i] = ''.join(text[i].split())
                    value.append(text[i])
            #加入舰队数量
            get_dict = dict(zip(key, value))
            get_dict["fleet_quantity"] = str(image_ass_num)
            get_dict["ass_image_path"] = image_ass
            get_dict["medal_image_path"] = image_medal
            get_dict["user_image_path"] = image_user
            if "Location" in get_dict:
                get_dict["Location"] = get_dict["Location"].replace(" ", "")
            else:
                get_dict["Location"] = "-"
            new_dict = {}
            for i in get_dict:
                new_key = i.lower().replace(" ", "_")
                if "(sid)" in new_key:
                    new_key = new_key.replace("(sid)", "sid")
                new_dict[new_key] = get_dict[i]
            new_dict_str = str(json.dumps(new_dict))
            return new_dict_str
        else:
            raise ValueError("Without this user")

    def get_boat(self):

        res = Request.get_html("https://www.spviewer.eu/pages/ship-performances.html?ship=drak_buccaneer")
        res2 = Request.get_html("https://starcitizen.tools/Buccaneer#Pledge-0")
        print(res2)
        _element = etree.HTML(res)
        # 游戏价格
        game_price = _element.xpath('//*[@id="SBuy"]/span[2]')
        # 尺寸
        size = _element.xpath('//*[@id="SBuy"]/span[2]')


        # return res
class MakePhotos():
    def __init__(self, bGImgPath):
        """
        默认获取背景图片和
        :param bGImgPath:
        :param addValueCoord:
        """
        self.back_ground_image = bGImgPath


    def _judgment_Coord(self, addValueCoord):
        if type(addValueCoord) == tuple and len(addValueCoord) == 2:
            return addValueCoord
        else:
            pprint(f"位置填写错误{addValueCoord}")

    def recognize_text(self, font_path, font_size, adjust_coor, font_color, save_path):
        """
        识别图片文字模型
        :param font_path: 文字文件地址
        :param font_size: 文字大小
        :param adjust_coor: 参数调整位置，根据x1,y1调整
        :param font_color: 文字颜色
        :param save_path: 储存地址，如果为""则不保存
        :return: 返回{参数：参数坐标}
        """
        # 调用 OCR 模型识别文本
        ocr = CnOcr()
        new_img = copy.copy(self.back_ground_image)
        res = ocr.ocr(new_img)

        from typing import List, Dict, Any
        import numpy as np

        def merge_elements(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

            """
            合并OCR元素，将相邻的元素合并成一个元素，若相邻元素的X轴距离小于200且Y轴距离小于50。
            合并后的元素的左边界取最后一个元素的左边界，右边界通过左边界加上字符的长度计算获得。

            参数：
                elements（List[Dict[str，Any]]）：OCR元素的列表，其中每个元素都是包含'text'，'score'和'position'键的字典。
                'position'键是一个numpy数组，其形状为（4，2），表示元素的左上角，右上角，右下角和左下角的坐标。

            返回：
                List[Dict[str，Any]]：合并后的元素列表，其中每个元素都是包含'text'，'score'和'position'键的字典。
                'position'键是一个numpy数组，其形状为（4，2），表示元素的左上角，右上角，右下角和左下角的坐标。
            """

            merged_elements = []  # 用于存储合并的元素
            merge_buffer = []  # 用于存储待合并的元素
            merge_flag = False  # 用于记录是否需要合并元素


            for i, elem in enumerate(elements):
                if merge_flag:  # 如果需要合并元素，则将当前元素与之前的元素合并
                    merged_elem = merge_buffer.pop()
                    merged_text = merged_elem['text'] + elem['text']
                    merged_score = max(merged_elem['score'], elem['score'])
                    # 计算合并后元素的左上角和右下角坐标
                    merged_left = min(merged_elem['position'][0][0], elem['position'][0][0])
                    merged_top = min(merged_elem['position'][0][1], elem['position'][0][1])
                    merged_right = max(merged_elem['position'][2][0], elem['position'][2][0])
                    merged_bottom = max(merged_elem['position'][2][1], elem['position'][2][1])
                    # 构造新的位置数组，只保留左上角、左下角、右下角、右上角坐标
                    merged_position = np.array([[merged_left, merged_top], [merged_left, merged_bottom],
                                                [merged_right, merged_bottom], [merged_right, merged_top]],
                                               dtype=np.float32)
                    merged_elem = {'text': merged_text, 'score': merged_score, 'position': merged_position}
                    merged_elem['merged_position'] = merged_position[-1]
                    merge_buffer.append(merged_elem)
                    merge_flag = False
                else:  # 如果不需要合并元素，则直接将当前元素添加到merge_buffer中
                    merge_buffer.append(elem)
                if i < len(elements) - 1:  # 如果不是最后一个元素
                    curr_right = elem['position'][1, 0]  # 当前元素的右边界
                    next_left = elements[i + 1]['position'][0, 0]  # 下一个元素的左边界
                    curr_bottom = elem['position'][0, 1]  # 当前元素的下边界
                    next_top = elements[i + 1]['position'][0, 1]  # 下一个元素的上边界
                    if next_left - curr_right < 200 and abs(curr_bottom - next_top) < 15:  # 如果相邻元素距离小于阈值，则需要合并元素
                        merge_flag = True

                if not merge_flag:  # 如果不需要合并元素，则将merge_buffer中的元素添加到merged_elements中，并清空merge_buffer
                    merged_elem = merge_buffer[-1]
                    merged_elem['position'][0, 0] = merge_buffer[0]['position'][0, 0]  # 左边界取第一个元素的左边界
                    merged_elem['position'][1, 0] = merged_elem['position'][0, 0] + len(
                        merged_elem['text']) * 20  # 右边界通过左边界加上字符的长度计算获得
                    merged_elements.append(merged_elem)
                    merge_buffer = []

            if merge_buffer:  # 处理最后一组待合并的元素
                merged_elem = merge_buffer[-1]
                merged_elem['position'][0, 0] = merge_buffer[0]['position'][0, 0]  # 左边界取第一个元素的左边界
                merged_elem['position'][1, 0] = merged_elem['position'][0, 0] + len(
                    merged_elem['text']) * 20  # 右边界通过左边界加上字符的长度计算获得

            return merged_elements
        merged_res = merge_elements(res)

        # 绘制红色框框和文字
        draw = ImageDraw.Draw(new_img)
        font = ImageFont.truetype(font=font_path, size=int(font_size))
        # 获取参数位置
        get_dict = {}
        adjust_coor = eval(adjust_coor)
        for item in merged_res:
            position = item['position']
            x1, y1 = position[0][0], position[0][1]
            x2, y2 = position[2][0], position[2][1]
            draw.rectangle((x1, y1, x2, y2), outline='red')
            if "：" in item['text'] or ":" in item['text']:
                item['text'] = item['text'].replace("：", "").replace(":", "")
            if "(" in font_color:
                font_color = eval(font_color)
            draw.text((x2 + adjust_coor[0], y2 - adjust_coor[1]), item['text'], font=font, fill=font_color)
            get_dict[item['text']] = (x2 + adjust_coor[0], y2 - adjust_coor[1])
        if save_path != "":
            save_path = save_path + "/Image_coordinate_reference.png"
            new_img.save(save_path)
        return get_dict

    def photo_to_photo(self, photo_add, add_phtoto_size, add_value_coord,hierarchy="lower"):
        if "https" in photo_add:
            response = requests.get(photo_add)
            # 将图片内容转换为 Image 对象
            image = Image.open(BytesIO(response.content))
            # Opening the primary image (used in background)
        else:
            image = Image.open(photo_add)

        try:
            img1 = self.back_ground_image.convert('RGBA')

            # Opening the secondary image (overlay image)
            imgAdd = image.convert('RGBA')
            base_width = ast.literal_eval(add_phtoto_size)
        except:
            raise Exception("获取图片失败")
        # 基本宽度与原图宽度的比例
        w_percent = base_width[0] / float(imgAdd.size[0])
        new_size = img1.size
        new_image = Image.new("RGBA", new_size, (255, 255, 255, 0))
        # 计算比例不变的条件下新图的长度
        h_size = int(float(imgAdd.size[1]) * float(w_percent))
        imgAdd = imgAdd.resize((base_width[0], h_size))
        if hierarchy == "lower":
            new_image.paste(imgAdd, ast.literal_eval(add_value_coord), imgAdd)
            new_image.paste(img1, (0, 0), img1)
        elif hierarchy == "upper":
            new_image.paste(img1, (0, 0), img1)
            new_image.paste(imgAdd, ast.literal_eval(add_value_coord), imgAdd)
        else:
            raise Exception("hierarchy 参数仅支持'lower'或'upper'")
        result_image = new_image.resize(new_size)

        return result_image
        # Displaying the image

    def text_to_photo(self, chars, ttf_path,ttf_size, font_color,addValueCoord):
        # ttfont = ImageFont.truetype("/Library/Fonts/华文细黑.ttf", 20)  # 这里我之前使用Arial.ttf时不能打出中文，用华文细黑就可以

        # 2. 加载字体并指定字体大小
        # ttf = ImageFont.load_default()  # 默认字体
        ttf = ImageFont.truetype(ttf_path, int(ttf_size))
        # 3. 创建绘图对象
        img_draw = ImageDraw.Draw(self.back_ground_image)
        # 4. 在图片上写字
        # 第一个参数：指定文字区域的左上角在图片上的位置(x,y)
        # 第二个参数：文字内容
        # 第三个参数：字体
        # 第四个参数：颜色RGB值
        list = dict(addValueCoord).keys()
        for i in chars:
            if not (i in list) or addValueCoord[i] == '(0,0)':
                continue
            if i == "medal":
                tup = tuple(map(float, addValueCoord[i].strip("()").split(",")))

                # 对元组中的第一个值加50
                new_tup = (tup[0] + 50,) + tup[1:]

                # 将元组转换为字符串
                addValueCoord[i] = str(new_tup)

            if "(" in font_color:
                font_color = eval(font_color)
            img_draw.text(ast.literal_eval(addValueCoord[i]), chars[i], font=ttf, fill=font_color)
        return self.back_ground_image
        # image.save("1.jpg")


class IniFileEditor:
    def __init__(self):
        """
        config_file：ini文件路径，在
        """
        self.file_path = config_file
        self.config = configparser.ConfigParser()
        self.config.read(self.file_path)


    def get_value(self, section, key):
        return self.config.get(section, key)

    def read_ini_file(self):
        config = configparser.ConfigParser()
        config.read(self.file_path)
        data = {}
        for section in config.sections():
            data[section] = {}
            for option in config.options(section):
                data[section][option] = config.get(section, option)
        data = str(data).replace("'", "\"")
        return data

    def set_value(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, f'{value}')
        self.save()

    def write_value(self, section, keyList):
        iniKeys = dict(self.config.items(section))
        if iniKeys.keys() == keyList.keys():
            iniKeys.update(keyList)
        else:
            for i in keyList:
                self.set_value(section, i, keyList[i])
            diff = set(iniKeys.keys()) - set(keyList.keys())
            return diff
        for option in self.config.options(section):
            self.config.set(section, option, keyList[option])
        self.save()
        return "配置文件坐标更新成功，{}".format(keyList)

    def save(self):
        with open(self.file_path, 'w') as config_file:
            self.config.write(config_file)
