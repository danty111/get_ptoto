import ast
import configparser
import copy
import json
import os

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
        if "You are currently venturing unknown space" not in res:
            _element = etree.HTML(res)
            _element_org = etree.HTML(res_organizations)
            #获取用户信息
            text = _element.xpath('//*[@class="inner clearfix"]/*[@class="info"]//p//text()')
            #获取舰队信息
            tex1 = _element.xpath("//*[@class='left-col']//text()")

            jud_visibility = _element.xpath('//*[@class="member-visibility-restriction member-visibility-r trans-03s"]')

            empty_ass = _element.xpath('//*[@class="empty"]')
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
                    text.append("未加入舰队")
                    text.append("organization_rank")
                    text.append("未加入舰队")
                    image_ass = "need_empty"


            image_medal = _element.xpath('//*[@class="icon"]/img/@src')[0]
            image_medal = "https://robertsspaceindustries.com" + image_medal

            # 获取用户头像
            image_user = _element.xpath("//*[@class='thumb']/img/@src")[0]
            if "cdn" not in image_user:
                image_user = "https://robertsspaceindustries.com/" + image_ass

            # 获取徽章信息
            image_medal = _element.xpath('//*[@class="icon"]/img/@src')[0]
            if "https" not in image_medal:
                image_medal = "https://robertsspaceindustries.com" + image_medal
            image_ass_num = len(_element_org.xpath('//*[@class="profile-content orgs-content clearfix"]/div'))
            list = text + tex1
            text = [x.strip() for x in list if x.strip() != '']
            text.insert(0, "id")
            text.insert(4, "medal")
            # if len(jud_visibility) == 0:
            #     text.insert(6, "organization")
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
            get_dict["image_medal"] = image_medal
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
            return str(new_dict).replace("'", "\"")
        else:

            raise ValueError("Without this user")

    def get_boat(self, ):
        print(1)


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

        # 绘制红色框框和文字
        draw = ImageDraw.Draw(new_img)
        font = ImageFont.truetype(font=font_path, size=int(font_size))
        # 获取参数位置
        get_dict = {}
        adjust_coor = eval(adjust_coor)
        for item in res:
            position = item['position']
            x1, y1 = position[0][0], position[0][1]
            x2, y2 = position[2][0], position[2][1]
            draw.rectangle((x1, y1, x2, y2), outline='red')
            if "：" in item['text'] or ":" in item['text']:
                item['text'] = item['text'].replace("：", "").replace(":", "")
            draw.text((x2 + adjust_coor[0], y2 - adjust_coor[1]), item['text'], font=font, fill=font_color)
            get_dict[item['text']] = (x2 + adjust_coor[0], y2 - adjust_coor[1])
        if save_path != "":
            save_path = save_path + "/Image_coordinate_reference.png"
            new_img.save(save_path)
        return get_dict

    def photo_to_photo(self, photo_add, add_phtoto_size, add_value_coord):
        if "https" in photo_add:
            response = requests.get(photo_add)
            # 将图片内容转换为 Image 对象
            image = Image.open(BytesIO(response.content))
            # Opening the primary image (used in background)
        else:
            image = Image.open(photo_add)
        img1 = self.back_ground_image.convert('RGBA')

        # Opening the secondary image (overlay image)
        imgAdd = image.convert('RGBA')
        base_width = ast.literal_eval(add_phtoto_size)
        # 基本宽度与原图宽度的比例
        w_percent = base_width[0] / float(imgAdd.size[0])
        new_size = img1.size
        new_image = Image.new("RGBA", new_size, (255, 255, 255, 0))
        # 计算比例不变的条件下新图的长度
        h_size = int(float(imgAdd.size[1]) * float(w_percent))
        imgAdd = imgAdd.resize((base_width[0], h_size))
        new_image.paste(imgAdd, ast.literal_eval(add_value_coord), imgAdd)
        new_image.paste(img1, (0, 0), img1)
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
