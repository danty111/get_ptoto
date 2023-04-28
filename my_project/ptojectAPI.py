import json
import re

from PIL import Image
from lxml import etree

from common import IniFileEditor, MakePhotos, Request, common_method


class MakePhoto:
    def __init__(self, interface, name):
        self.config = json.loads(IniFileEditor().read_ini_file())
        self.interface = interface
        self.back_ground_image = Image.open(self.config[interface]["background"])

        self.template_image_name = self.config[interface]["background"].replace(".png", "_template.png")
        self.template_image = Image.open(self.template_image_name)
        self.name = name

        # 获取卡片配置参数
        self.section = self.config[interface]
        # 获取名片位置参数
        self.template = self.config[f"{interface}_template"]
        # 获取名称对应字典
        self.parameter_dic = self.config[f"{interface}_parameter_dictionary"]

    def _replace_dict(self, old_dict, com_table):
        swapped_dict = {value: key for key, value in com_table.items() if key != "template_path"}
        new_dict = {}

        if isinstance(old_dict, dict) or isinstance(old_dict, str):
            if old_dict is str:
                try:
                    old_dict = eval(old_dict)
                except:
                    raise ValueError("格式不符合str转为dict的规范")
            for i in swapped_dict:
                if i in com_table.values():
                    new_dict[swapped_dict[i]] = old_dict[i]
                else:
                    continue
            return new_dict
        else:
            raise ValueError("old_dict参数应为dict或str")

    def make_card(self):
        self.no_fleet = self.config[self.interface]["no_fleet"]
        # 识别模版
        if self.template_image_name != self.parameter_dic["template_path"] or self.section["need_change"] != "false":
            get_value = MakePhotos(self.template_image).recognize_text(self.section["ttf_path"],
                                                                       self.section["font_size"]
                                                                       , self.section["adjust_coor"]
                                                                       , self.section["font_color"],
                                                                       self.section["save_path"])
            get_value = self._replace_dict(get_value, self.parameter_dic)
            IniFileEditor().set_value("card_parameter_dictionary", "template_path", self.template_image_name)
            IniFileEditor().write_value("card_template", get_value)
            IniFileEditor().set_value("card", "need_change", "false")
        # 获取名片信息
        msg = Request.get_json(GetValue(self.name).get_card())
        # 判断舰队图标是否为空
        if msg["ass_image_path"] == "need_empty":
            msg["ass_image_path"] = self.no_fleet
        # 绘制舰队图标
        self.back_ground_image = MakePhotos(self.back_ground_image) \
            .photo_to_photo(msg["ass_image_path"], self.template["ass_image_size"],
                            self.template["ass_image_coordinate"])

        self.back_ground_image = MakePhotos(self.back_ground_image) \
            .photo_to_photo(msg["medal_image_path"], self.template["medal_image_size"],
                            self.template["medal_image_coordinate"], hierarchy="upper")

        self.back_ground_image = MakePhotos(self.back_ground_image) \
            .photo_to_photo(msg["user_image_path"], self.template["user_image_size"],
                            self.template["user_image_coordinate"])

        self.back_ground_image = MakePhotos(self.back_ground_image).text_to_photo(msg, self.section["ttf_path"]
                                                                                  , self.section["font_size"],
                                                                                  self.section["font_color"],
                                                                                  self.template)
        # 将图像保存为 PNG 格式

        return self.back_ground_image

    def make_boat(self):

        if self.template_image_name != self.parameter_dic["template_path"] or self.section["need_change"] != "false":
            get_value = MakePhotos(self.template_image).recognize_text(self.section["ttf_path"],
                                                                       self.section["font_size"]
                                                                       , self.section["adjust_coor"]
                                                                       , self.section["font_color"],
                                                                       self.section["save_path"])
            get_value = self._replace_dict(get_value, self.parameter_dic)
            # 自动回填模版地址
            IniFileEditor().set_value("boat_parameter_dictionary", "template_path", self.template_image_name)
            # 回填模版地址坐标
            IniFileEditor().write_value("boat_template", get_value)
            # 将判断改变字段回填false
            IniFileEditor().set_value("boat", "need_change", "false")
        # 获取名片信息
        msg = Request.get_json(GetValue(self.name).get_boat())
        print(msg)


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
        # 判断是否存在用户
        if "You are currently venturing unknown space" not in 'utf-8':
            _element = etree.HTML(res)
            _element_org = etree.HTML(res_organizations)
            # 获取用户信息
            text = _element.xpath('//*[@class="inner clearfix"]/*[@class="info"]//p//text()')
            # 获取舰队信息
            tex1 = _element.xpath("//*[@class='left-col']//text()")

            jud_visibility = _element.xpath('//*[@class="member-visibility-restriction member-visibility-r trans-03s"]')

            empty_ass = _element.xpath('//*[@class="empty"]')
            empry_ass_num = _element_org.xpath('//*[@class="empty"]')
            # 兼容舰队隐藏的问题
            if len(jud_visibility) == 0 and len(empty_ass) == 0:
                # 获取舰队信息
                image_ass = _element.xpath('//*[@class="thumb"]/a/img/@src')[0]
                if "cdn" not in image_ass:
                    image_ass = "https://robertsspaceindustries.com/" + image_ass
            else:
                if len(empty_ass) == 0:
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
            # 加入舰队数量
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
        res1 = json.loads(Request.get_html_encode("https://www.spviewer.eu/assets/json/ship-list-min.json"))
        res2 = Request.get_html_encode(f"https://starcitizen.tools/Buccaneer")

        for boat_value in res1:
            if re.search(boat_value["ClassName"], self.name, re.IGNORECASE):
                res1 = boat_value
                break
        else:
            raise Exception("没有当前飞船:", self.name)
        _element = etree.HTML(res2)
        boat_value_dict = {}
        # 添加船价
        price = _element.xpath('//*[text() = "Standalone"]/following-sibling::*/text()')[0]
        boat_value_dict["price"] = price
        # 添加游戏价格
        game_price = res1["Buy"]
        first_item = list(game_price.items())[0]
        game_price = '{}: {}'.format(first_item[0], first_item[1])
        game_price = common_method.decimal_de_zeroing(game_price)
        boat_value_dict["game_price"] = common_method.amount_handled(game_price) + " aUEC"
        #  添加船的尺寸
        dimensions = res1["Dimensions"]
        get_size_stage = _element.xpath("//*[@class='data-size infobox-data infobox-col2']/td/text()")[0]
        size = f"{dimensions['Length']}x{dimensions['Width']}x{dimensions['Height']} m{get_size_stage}"
        size = common_method.decimal_de_zeroing(size)
        boat_value_dict["size"] = size
        # 添加船员
        crew_num = _element.xpath('//*[text() = "Crew"]/following-sibling::*/text()')[0]
        boat_value_dict["crew_num"] = crew_num
        # 质量
        quality = common_method.decimal_de_zeroing(res1["Mass"])
        boat_value_dict["quality"] = quality
        # 货物
        goods = common_method.decimal_de_zeroing(res1["Cargo"])
        boat_value_dict["goods"] = goods
        # 储存
        ExternalStorage = common_method.decimal_de_zeroing(res1["ExternalStorage"])
        boat_value_dict["storage_space"] = ExternalStorage
        # 索赔\加急
        Insurance = res1["Insurance"]
        StandardClaimTime = common_method().convert_seconds_to_time_format(Insurance["StandardClaimTime"])
        ExpeditedClaimTime = common_method().convert_seconds_to_time_format(Insurance["ExpeditedClaimTime"])
        boat_value_dict["compensation_and_expedited"] = StandardClaimTime + "\\" + ExpeditedClaimTime
        # 加急费用
        expedited_charge = common_method.decimal_de_zeroing(Insurance["ExpeditedCost"])
        boat_value_dict["expedited_charge"] = expedited_charge + " aUEC"
        # XYZ
        FlightCharacteristics  = res1["FlightCharacteristics"]
        pitch_yaw_roll = common_method.decimal_de_zeroing(FlightCharacteristics["Pitch"])+"、"+\
                         common_method.decimal_de_zeroing(FlightCharacteristics["Yaw"])+ "、"+\
                         common_method.decimal_de_zeroing(FlightCharacteristics["Roll"])
        boat_value_dict["pitch_yaw_roll"] = pitch_yaw_roll
        # 氢油箱
        FuelManagement = res1["FuelManagement"]
        hydrogen_mailbox = common_method.amount_handled(FuelManagement["FuelCapacity"])
        boat_value_dict["hydrogen_mailbox"] = hydrogen_mailbox + " L"
        # 量子油箱
        quantum_mailbox = common_method.amount_handled(FuelManagement["QuantumFuelCapacity"])
        boat_value_dict["quantum_mailbox"] = quantum_mailbox + " L"
        # 主引擎
        AccelerationG = res1["AccelerationG"]
        main_engine = common_method.decimal_de_zeroing(AccelerationG["Main"])
        boat_value_dict["main_engine"] = main_engine
        # 反推引擎
        reverse_thrust_engine = common_method.decimal_de_zeroing(AccelerationG["Retro"])
        boat_value_dict["reverse_thrust_engine"] = reverse_thrust_engine

        print(boat_value_dict)
