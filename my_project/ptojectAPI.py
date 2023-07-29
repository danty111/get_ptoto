import _thread
import random
import json
import re
import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


import requests
from PIL import Image
from PIL.Image import Quantize
from lxml import etree

from common import IniFileEditor, MakePhotos, Request, common_method, GetExcelValue


class MakePhoto:
    def __init__(self, interface, name):
        self.config = json.loads(IniFileEditor().read_ini_file())
        self.interface = interface
        self.template_image_name = self.config[interface]["background"].replace(".png", "_template.png")
        if self.interface == "boat":
            random_number = random.randint(1, 10)
            if random_number < 10:
                random_number = "0" + str(random_number)
            else:
                random_number = str(random_number)
            self.back_ground_image = Image.open(
                self.config[interface]["background"].replace(".png", f"_{random_number}.png"))

        else:
            random_number = random.randint(1, 5)
            if random_number < 10:
                random_number = "0" + str(random_number)
            else:
                random_number = str(random_number)

            self.back_ground_image = Image.open(self.config[interface]["background"].replace(".png", f"_{random_number}.png"))

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
        # self.back_ground_image = common_method.compress_image(self.back_ground_image, 10)
        return self.back_ground_image

    def make_boat(self, boat_value=None):


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
        # 获取舰船名称
        msg = GetValue(self.name).get_boat(self.config[self.interface]["boat_name_excel"],boat_value=boat_value)
        self.back_ground_image = MakePhotos(self.back_ground_image) \
            .photo_to_photo(msg["boat_image"], self.template["boat_image_size"],
                            self.template["boat_image_coordinate"], hierarchy="upper")
        boatyard_name = GetExcelValue(self.name).get_boat_name(self.config[self.interface]["boat_name_excel"])
        self.back_ground_image = MakePhotos(self.back_ground_image) \
            .photo_to_photo(self.section["shipyard_file"] + f"/{boatyard_name[1]}.png", self.template['shipyard_size'],
                            self.template["shipyard_coordinate"], hierarchy="upper")
        self.back_ground_image = MakePhotos(self.back_ground_image).text_to_photo(msg, self.section["ttf_path"]
                                                                                  , self.section["font_size"],
                                                                                  self.section["font_color"],
                                                                                  self.template)
        self.back_ground_image = MakePhotos(self.back_ground_image).text_to_photo(
            {"boat_name_coordinate": msg["boat_name"]}, self.section["ttf_path"]
            , self.section["boat_name_size"],
            self.section["font_color"],
            {"boat_name_coordinate": self.section["boat_name_coordinate"]})
        self.back_ground_image = MakePhotos(self.back_ground_image).text_to_photo(
            {"boat_name_coordinate": msg["boat_en_name"]}, self.section["ttf_path"]
            , self.section["boat_name_en_size"],
            self.section["font_color"],
            {"boat_name_coordinate": self.section["boat_name_en_coordinate"]})

        # 将图像保存为 PNG 格式
        return self.back_ground_image, boatyard_name[0]


class GetValue():
    def __init__(self, name):
        self.name = name

    def get_card(self):
        """
        获取名片的内容
        :param name:查询者的名字
        :return:
        """

        res = Request().get_html(f"https://robertsspaceindustries.com/citizens/{self.name}")
        res_organizations = Request().get_html(f"https://robertsspaceindustries.com/citizens/{self.name}/organizations")
        # 判断是否存在用户
        _element = etree.HTML(res)
        _element_org = etree.HTML(res_organizations)
        if "You are currently venturing unknown space" not in res:

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

    def get_boat(self, filename, boat_value=None):
        if boat_value is None:
            boat_value = {}
        name_list = GetExcelValue(self.name).get_boat_name(filename)
        if name_list == None:
            raise Exception("船表格里没有当前飞船", self.name)
        self.name = name_list[0]
        self.add_name = name_list[2]

        if boat_value["boat_json"] == "":
            res1 = json.loads(Request.get_html_encode("https://www.spviewer.eu/assets/json/ship-list-min.json"))
        else:
            res1 = boat_value["boat_json"]
        res2 = Request.get_html_encode(f"https://starcitizen.tools/{self.name}")

        if boat_value["ship_hardpoints"] == "":
            ship_hardpoints = "https://www.spviewer.eu/assets/json/ship-hardpoints-min.json"
            boat_response = requests.get(ship_hardpoints)
            json_data = boat_response.content.decode('utf-8-sig')
            boat_weapon_list = json.loads(json_data)
        else:
            boat_weapon_list = boat_value["ship_hardpoints"]

        if boat_value["data_version"] == "":
            data_version = Request.get_html_encode("https://www.spviewer.eu/assets/js/data-version.js").decode('utf-8')
        else:
            data_version = boat_value["data_version"]



        for boat_data in res1:
            if self.add_name.lower() == boat_data["ClassName"].lower():
                res1 = boat_data
                break
        else:
            raise Exception("没有当前飞船:", name_list[1], self.name, self.add_name)

        for boat_weapon in boat_weapon_list:
            if self.add_name.lower() == boat_weapon["ClassName"].lower():
                boat_weapon = boat_weapon
                break
        else:
            raise Exception("没有当前飞船:", name_list[1], self.name, self.add_name)

        _element = etree.HTML(res2)
        none_value = _element.xpath('//*[@id="This_page_is_avaliable_on_sale_on_the_Privateer_legally."]')
        if len(none_value) != 0:
            raise Exception("当前非常查找错误" + self.name)

        boat_value_dict = {}
        if "_" in self.name:
            boat_name = self.name.replace("_", " ")
        else:
            boat_name = self.name
        # 船名
        boat_value_dict["boat_name"] = name_list[3]
        boat_value_dict["boat_en_name"] = boat_name.upper()
        # 添加船价
        try:
            price = _element.xpath('//*[text() = "Standalone"]/following-sibling::*//*[@class="smwtext"]/text()')
            if len(price) == 2:
                price = "$ " + str(float(price[0].replace('$', '').replace(' ', ''))) + "($ " + str(
                    float(price[1].replace('$', '').replace(' ', ''))) + ")"
            else:
                price = "$ " + str(float(price[0].replace('$', '').replace(' ', '')))
            if ".0" in price:
                price = price.replace(".0", "")
            boat_value_dict["price"] = price
        except:
            boat_value_dict["price"] = "无法购买"
        # 添加游戏价格
        if "Buy" in res1:
            game_price = res1["Buy"]
            first_item = list(game_price.items())[0]
            selling_address = {"Astro Armada": '奥里森', 'Area 18': '18区', 'Lorville': "罗威尔"}
            address = ''
            if "," in first_item[0]:
                address_list = first_item[0].split(",")
                for i in address_list:
                    i = i.strip()
                    if i in selling_address:
                        address += selling_address[i] + ","
                address = address[: -1]
            else:
                address = first_item[0]
            price = common_method.amount_handled(first_item[1])
            game_price = '{} aUEC ({}) '.format(price, address)

            boat_value_dict["game_price"] = game_price
        else:
            boat_value_dict["game_price"] = "无法aUEC购买"
        #  添加船的尺寸

        dimensions = res1["Dimensions"]
        # get_size_stage = _element.xpath("//*[@class='data-size infobox-data infobox-col2']/td/text()")
        # if get_size_stage != []:
        # get_size_stage = get_size_stage[0]
        try:
            size = f"{dimensions['Length']} m x{dimensions['Width']} m x{dimensions['Height']} m "
            size = common_method.decimal_de_zeroing(size)
            boat_value_dict["size"] = size
        except:
            boat_value_dict["size"] = "-"
        # 添加船员
        try:
            crew_num = _element.xpath('//*[text() = "Crew"]/following-sibling::*/text()')
            crew_num = crew_num[0]
            # if "–" in crew_num:
            #     s = crew_num.replace(' ', '')  # 移除空格
            #     crew_num_list = s.split('–')  # 将字符串按照'-'分割成两个部分
            #     crew_num = sum([int(x) for x in crew_num_list])
            # boat_value_dict["crew_num"] = str(crew_num) + " 人"
            boat_value_dict["crew_num"] = crew_num
        except:
            boat_value_dict["crew_num"] = "-"
        # 质量
        quality = common_method.decimal_de_zeroing(res1["Mass"])
        boat_value_dict["quality"] = quality + " KG"
        # 货物
        goods = common_method.decimal_de_zeroing(res1["Cargo"])
        boat_value_dict["goods"] = goods + " SCU"
        # 储存
        ExternalStorage = common_method.decimal_de_zeroing(res1["PersonalInventory"])
        boat_value_dict["storage_space"] = ExternalStorage + ",000 K uSCU"
        # 索赔\加急
        Insurance = res1["Insurance"]
        StandardClaimTime = common_method().convert_seconds_to_time_format(Insurance["StandardClaimTime"])
        ExpeditedClaimTime = common_method().convert_seconds_to_time_format(Insurance["ExpeditedClaimTime"])
        if ExpeditedClaimTime == "00s":
            ExpeditedClaimTime = "0s"
        boat_value_dict["compensation_and_expedited"] = StandardClaimTime + "\\" + ExpeditedClaimTime
        # 加急费用
        expedited_charge = common_method.decimal_de_zeroing(Insurance["ExpeditedCost"])
        boat_value_dict["expedited_charge"] = expedited_charge + " aUEC"
        # XYZ
        if "FlightCharacteristics" in res1:
            FlightCharacteristics = res1["FlightCharacteristics"]
            pitch_yaw_roll = common_method.decimal_de_zeroing(FlightCharacteristics["Pitch"]) + "/S、" + \
                             common_method.decimal_de_zeroing(FlightCharacteristics["Yaw"]) + "/S、" + \
                             common_method.decimal_de_zeroing(FlightCharacteristics["Roll"]) + "/S"
            boat_value_dict["pitch_yaw_roll"] = pitch_yaw_roll
        else:
            boat_value_dict["pitch_yaw_roll"] = "-"
        # 氢油箱
        if 'FuelManagement' in res1:
            FuelManagement = res1["FuelManagement"]
            hydrogen_mailbox = FuelManagement["FuelCapacity"]
            boat_value_dict["hydrogen_mailbox"] = common_method.decimal_de_zeroing(hydrogen_mailbox) + " L"
            # 量子油箱
            quantum_mailbox = FuelManagement["QuantumFuelCapacity"]
            boat_value_dict["quantum_mailbox"] = common_method.decimal_de_zeroing(quantum_mailbox) + " L"
        else:
            boat_value_dict["hydrogen_mailbox"] = "-"
            boat_value_dict["quantum_mailbox"] = "-"

        # 标准速度
        try:
            standard_speed = _element.xpath('//*[text() = "Scm speed"]/following-sibling::*//*[@class="smwtext"]/text()')[0]
            s_speed = boat_value_dict["standard_speed"] = standard_speed.encode('utf-8').decode('utf-8')
            match = re.search(r'(\d+(\.\d+)?)\s*(\w+/\w+)', s_speed)

            if match:
                value = match.group(1)  # 提取数字部分
                unit = match.group(3)  # 提取单位部分

                boat_value_dict["standard_speed"] = f'{value} {unit}'
            else:
                print('No match found.')
        except:
            boat_value_dict["standard_speed"] = "-"

        # 最高速度
        try:
            maximum_speed = _element.xpath('//*[text() = "Max speed"]/following-sibling::*//*[@class="smwtext"]/text()')
            if maximum_speed != []:
                maximum_speed = maximum_speed[0]
            else:
                maximum_speed = res1['FlightCharacteristics']['MaxSpeed']
            max_speed = maximum_speed.encode('utf-8').decode('utf-8')
            match = re.search(r'([\d,]+(\.\d+)?)(\s*)([a-zA-Z]+/[a-zA-Z]+)', max_speed)

            if match:
                value = match.group(1)  # 提取数字部分
                unit = match.group(4)  # 提取单位部分
                boat_value_dict["maximum_speed"] = f'{value} {unit}'
            else:
                print('No match found.')

        except:
            boat_value_dict["maximum_speed"] = "-"
        # 主引擎
        try:
            AccelerationG = res1["FlightCharacteristics"]["AccelerationG"]
            Y_AccelMultiplicator = res1["FlightCharacteristics"]["Capacitors"]["Y_AccelMultiplicator"]
            main_engine = common_method.decimal_de_zeroing(AccelerationG["Main"])
            boat_value_dict[
                "main_engine"] = main_engine + f' G（加力{common_method.decimal_de_zeroing(float(AccelerationG["Main"]) * float(Y_AccelMultiplicator))} G）'
            # 反推引擎
            reverse_thrust_engine = common_method.decimal_de_zeroing(AccelerationG["Retro"])

            boat_value_dict[
                "reverse_thrust_engine"] = reverse_thrust_engine + f' G（加力{common_method.decimal_de_zeroing(float(reverse_thrust_engine) * float(Y_AccelMultiplicator))} G）'

        except:
            boat_value_dict["main_engine"] = "-"
            boat_value_dict["reverse_thrust_engine"] = "-"
        # DPS武器
        try:
            boat_DPS = 0
            weapon_list = boat_weapon['Hardpoints']['Weapons']['PilotWeapons']['InstalledItems']
            for weapon in weapon_list:
                if "SubWeapons" in weapon:
                    DPS = weapon["SubWeapons"][0]["BurstDPS"].values()
                    DPS = next(iter(DPS))
                    boat_DPS += DPS
                elif "BurstDPS" in weapon:
                    DPS = weapon["BurstDPS"].values()
                    DPS = next(iter(DPS))
                    boat_DPS += DPS
            boat_value_dict["dps_weapon"] = common_method.decimal_de_zeroing(boat_DPS) + " DPS"
        except:
            boat_value_dict["dps_weapon"] = "-"
        # DPS导弹
        try:
            dps_missile = 0
            MissileRacks = boat_weapon['Hardpoints']['Weapons']['MissileRacks']["InstalledItems"]
            for i in MissileRacks:
                test = i['Missiles']
                for missile in test:
                    DPS = missile["Damage"].values()
                    DPS = next(iter(DPS))
                    dps_missile += DPS
            boat_value_dict["dps_missile"] = common_method.decimal_de_zeroing(int(dps_missile)) + " DPS"
        except:
            boat_value_dict["dps_missile"] = "-"
        # 护盾值
        shield_value = res1['Weapons']['TotalShieldHP']
        boat_value_dict["shield_value"] = common_method.decimal_de_zeroing(shield_value) + " HP"
        # 机体血量
        body_blood_volume = 0
        for i in res1["Hull"]["DamageBeforeDestruction"].values():
            body_blood_volume += i
        for i in res1["Hull"]["DamageBeforeDetach"].values():
            body_blood_volume += i
        boat_value_dict["body_blood_volume"] = common_method.decimal_de_zeroing(body_blood_volume) + " HP"
        # 机头\机身
        Canopy = res1["Hull"]["DamageBeforeDestruction"]
        if "Nose" in Canopy:
            Canopy = Canopy["Nose"]
        elif "nose" in Canopy:
            Canopy = Canopy["nose"]
        else:
            Canopy = "-"
        Canopy = common_method.decimal_de_zeroing(Canopy)

        Body = res1["Hull"]["DamageBeforeDestruction"]
        if "Body" in Body:
            Body = Body['Body']
        elif "body" in Body:
            Body = Body['body']
        else:
            Body = '-'
        Body = common_method.decimal_de_zeroing(Body)

        boat_value_dict["nose_and_fuselage"] = Canopy + " HP" + "\\" + Body + " HP"
        # 雷达电磁
        electromagnetic_radar = common_method.decimal_de_zeroing(res1['Emissions']['Electromagnetic']['IdleEMEmission'])
        ActiveEMEmission = common_method.decimal_de_zeroing(res1['Emissions']['Electromagnetic']["ActiveEMEmission"])
        boat_value_dict[
            "electromagnetic_radar"] = electromagnetic_radar + " EM(空闲)" + "\\" + ActiveEMEmission + " EM(活动)"
        # 雷达红外
        infrared_radar = common_method.decimal_de_zeroing(res1['Emissions']['Infrared']['StartIREmission'])
        boat_value_dict["infrared_radar"] = infrared_radar + " IR"
        # 量子引擎
        try:
            quantum_engine = _element.xpath(
                '//*[text() = " Quantum drive"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__size"]/text()')[
                                 0] + \
                             _element.xpath(
                                 '//*[text() = " Quantum drive"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__count"]/text()')[
                                 0][::-1]
            boat_value_dict["quantum_engine"] = quantum_engine
            boat_value_dict["transition_engine"] = quantum_engine
        except:
            boat_value_dict["quantum_engine"] = "-"
            boat_value_dict["transition_engine"] = "-"
        # # 越迁引擎
        # try:
        #     transition_engine = _element.xpath('//*[text() = " Jump drive"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__size"]/text()')[0]+\
        #                         _element.xpath(
        #                             '//*[text() = " Jump drive"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__count"]/text()')[0][::-1]
        #     boat_value_dict["transition_engine"] = transition_engine
        # except:
        #     boat_value_dict["transition_engine"] = "-"

        # 发电:
        try:
            generator = _element.xpath(
                '//*[text() = " Power plant"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__size"]/text()')[
                            0] + \
                        _element.xpath(
                            '//*[text() = " Power plant"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__count"]/text()')[
                            0][::-1]
            boat_value_dict["generator"] = generator
        except:
            boat_value_dict["generator"] = "-"
        try:
            # 冷却器
            cooler = _element.xpath(
                '//*[text() = " Cooler"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__size"]/text()')[
                         0] + \
                     _element.xpath(
                         '//*[text() = " Cooler"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__count"]/text()')[
                         0][::-1]
            boat_value_dict["cooler"] = cooler
        except:
            boat_value_dict["cooler"] = "-"
        try:
            # 护盾
            shield = _element.xpath(
                '//*[text() = " Shield generator"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__size"]/text()')[
                         0] + \
                     _element.xpath(
                         '//*[text() = " Shield generator"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__count"]/text()')[
                         0][::-1]
            boat_value_dict["shield"] = shield
        except:
            boat_value_dict["shield"] = "-"
        try:
            # 雷达
            radar = _element.xpath(
                '//*[text() = " Radar"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__size"]/text()')[
                        0] + \
                    _element.xpath(
                        '//*[text() = " Radar"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__count"]/text()')[
                        0][::-1]
            boat_value_dict["radar"] = radar
        except:
            boat_value_dict["radar"] = "-"
        try:
            # 电脑
            computer = _element.xpath(
                '//*[text() = " Scanner"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__size"]/text()')[
                           0] + \
                       _element.xpath(
                           '//*[text() = " Scanner"]/following-sibling::*//*[@class="template-component__port"]/*[@class="template-component__count"]/text()')[
                           0][::-1]
            boat_value_dict["computer"] = computer
        except:
            boat_value_dict["computer"] = "-"
        try:
            # 自毁时间
            self_destruct_time = \
            boat_weapon['Hardpoints']['Components']['Avionics']['SelfDestruct']['InstalledItems'][0][
                'SelfDestructionType']
            self_destruct_time = self_destruct_time.split('_')[-1]
            boat_value_dict["self_destruct_time"] = self_destruct_time
        except:
            boat_value_dict["self_destruct_time"] = "-"

        def process_boat_value(weapon_parameter):

            if weapon_parameter == "weapon":
                try:
                    grade_list = boat_weapon['Hardpoints']['Weapons']['PilotWeapons']['InstalledItems']
                except:
                    boat_value_dict[weapon_parameter] = "-"
                    return
            elif weapon_parameter == "manned_turret":
                try:
                    grade_list = boat_weapon['Hardpoints']['Weapons']['MannedTurrets']['InstalledItems']
                except:
                    boat_value_dict[weapon_parameter] = "-"
                    return

            elif "multifunctional" in weapon_parameter:
                try:
                    if weapon_parameter == "multifunctional_salvage":
                        grade_list = boat_weapon['Hardpoints']['Weapons']['SalvageHardpoints']['CrewControlled'][
                            'InstalledItems']
                    elif weapon_parameter == "multifunctional_utility":
                        grade_list = boat_weapon['Hardpoints']['Weapons']['UtilityHardpoints']['InstalledItems']
                    else:
                        pass
                except:
                    boat_value_dict[weapon_parameter] = "-"
                    return
            else:
                raise Exception("process_boat_value调用错误，没有对应的：" + weapon_parameter)

            # 武器
            size_count = {}
            weapon_dict = {}
            for item in grade_list:
                size = item['Size']

                if weapon_parameter == "weapon" or "multifunctional" in weapon_parameter:
                    if 'SubWeapons' in item:
                        if 'SubWeapons' in item:
                            for i in item['SubWeapons']:
                                size = i["Size"]
                                if size in size_count:
                                    size_count[size] += 1
                                else:
                                    size_count[size] = 1
                        weapon_dict[size] = True
                    else:
                        if size in size_count:
                            size_count[size] += 1
                        else:
                            size_count[size] = 1
                # 以特定格式打印结果
            weapon = ''
            for size in size_count:
                if size in size_count:
                    count = size_count[size]
                    if weapon:
                        weapon += '+'
                    weapon += f'S{size}x{count}'
                    if size in weapon_dict and weapon_parameter == "weapon":
                        weapon += '(可动)'
            if "multifunctional" in weapon_parameter:
                return weapon

            boat_value_dict[weapon_parameter] = weapon

        # 武器
        process_boat_value("weapon")

        def get_grade_num(file):
            aaa_dict = {}
            for i in file:
                temporary = {}
                for sub_weapon in i['SubWeapons']:
                    if sub_weapon['Size'] in temporary:
                        temporary[sub_weapon["Size"]] += 1
                    else:
                        temporary[sub_weapon["Size"]] = 1
                for num in temporary:
                    name = f"S{num}x{temporary[num]}"

                    if name in aaa_dict:
                        aaa_dict[name] += 1
                    else:
                        aaa_dict[name] = 1
            result_value = ""
            for i in aaa_dict:
                result_value += f"{i}x{aaa_dict[i]}+"
            result_value = result_value[:-1]
            return result_value

        try:
            # 载人炮塔
            manned_turret = get_grade_num(boat_weapon['Hardpoints']['Weapons']['MannedTurrets']['InstalledItems'])
            boat_value_dict["manned_turret"] = manned_turret
        except:
            boat_value_dict["manned_turret"] = "-"
        # 遥控炮塔
        try:
            grade_list = boat_weapon['Hardpoints']['Weapons']['RemoteTurrets']['InstalledItems']
            remote_control_turret = get_grade_num(grade_list)
            boat_value_dict["remote_control_turret"] = remote_control_turret
        except:
            boat_value_dict["remote_control_turret"] = "-"
        try:
            # 导弹
            missile_dice = {}
            grade_list = boat_weapon['Hardpoints']['Weapons']['MissileRacks']['InstalledItems']
            for missile_rack in grade_list:
                if 'Missiles' in missile_rack:
                    for missile in missile_rack['Missiles']:
                        if missile["Size"] in missile_dice:
                            missile_dice[missile["Size"]] += 1
                        else:
                            missile_dice[missile["Size"]] = 1
                else:
                    continue
            result = ""
            for i in missile_dice:
                result += f"S{i}x{missile_dice[i]}+"
            result = result[:-1]
        except:
            result = ""
        try:
            # 炸弹
            missile_dice = {}
            grade_list = boat_weapon['Hardpoints']['Weapons']['BombRacks']['InstalledItems']
            for missile_rack in grade_list:
                if 'Bombs' in missile_rack:
                    for missile in missile_rack['Bombs']:
                        if missile["Size"] in missile_dice:
                            missile_dice[missile["Size"]] += 1
                        else:
                            missile_dice[missile["Size"]] = 1
                else:
                    continue
            Bombs_result = ""
            for i in missile_dice:
                Bombs_result += f"S{i}x{missile_dice[i]}+"
            Bombs_result = Bombs_result[:-1]
            boat_value_dict["missile"] = Bombs_result
        except:
            Bombs_result = ""
        if result == "" or Bombs_result == "":
            if result == "" and Bombs_result == "":
                boat_value_dict["missile"] = "-"
            else:
                boat_value_dict["missile"] = result + Bombs_result
        else:
            boat_value_dict["missile"] = result + "+" + Bombs_result
        # 多功能
        try:
            aaa = process_boat_value("multifunctional_salvage")
            bbb = process_boat_value("multifunctional_utility")
            boat_value_dict["multifunctional"] = "Salvage " + aaa + " Utility " + bbb
        except:
            boat_value_dict["multifunctional"] = "-"
        # 飞船图片
        boat_value_dict["boat_image"] = _element.xpath(
            '//*[@class ="infobox__content mw-collapsible-content"]//*[@class = "mw-file-description"]/img/@src')[0]

        # 采集版本
        match = re.search(r'gameversion="([^"]+)"', data_version)
        if match:
            boat_value_dict["collection_version"] = match.group(1)

        # 采集时间：
        current_time = datetime.now()
        current_time_str = current_time.strftime('%Y.%-m.%-d %H:%M')
        boat_value_dict["collection_time"] = current_time_str

        return boat_value_dict

class BoatPhoto:
    @staticmethod
    def get_all_boat():
        print("当前执行时间", datetime.now())

        #爬取一些固定数据，避免多次请求
        boat_json = json.loads(Request.get_html_encode("https://www.spviewer.eu/assets/json/ship-list-min.json"))
        ship_hardpoints = "https://www.spviewer.eu/assets/json/ship-hardpoints-min.json"
        boat_response = requests.get(ship_hardpoints)
        json_data = boat_response.content.decode('utf-8-sig')
        boat_weapon_list = json.loads(json_data)

        data_version = Request.get_html_encode("https://www.spviewer.eu/assets/js/data-version.js").decode('utf-8')

        try:
            # 读取配置文件
            config = json.loads(IniFileEditor().read_ini_file())

            # 获取船只名称列表
            name_list = GetExcelValue.get_boat_list(config["boat"]["boat_name_excel"])

            # 打乱列表顺序
            random.shuffle(name_list)

            # 将列表随机分成 10 份
            num_threads = 10
            chunk_size = len(name_list) // num_threads
            chunks = [name_list[i:i + chunk_size] for i in range(0, len(name_list), chunk_size)]

            # 如果有余数，将余数分配到最后一个分片中
            if len(name_list) % num_threads != 0:
                chunks[-1] += name_list[-(len(name_list) % num_threads):]

            boat_value = {"boat_json": boat_json,"ship_hardpoints":boat_weapon_list,"data_version":data_version}
            # 执行多线程任务
            def save_image_names(names):
                for i in names:
                    image_file, image_name = MakePhoto("boat", i).make_boat(boat_value=boat_value)
                    save_path = config['boat']['boat_name_excel'].split("boat")[
                                    0] + "storage_boat/" + image_name + ".jpeg"
                    common_method.pic_compress(image_file, save_path)
                    print("----------------成功储存", i, "到", save_path,"\n")

            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(save_image_names, chunk) for chunk in chunks]

                # 等待所有线程执行结束
                for future in futures:
                    future.result()

            # 获取当前活跃的线程数
            active_threads = threading.active_count()
            print(f"当前活跃的线程数为：{active_threads}")

            # 获取所有线程的列表
            all_threads = threading.enumerate()
            print(f"所有线程的列表为：{all_threads}")

            # 获取当前线程的ID
            current_thread_id = _thread.get_ident()
            print(f"当前线程的ID为：{current_thread_id}")
            print("所有数据执行完毕")

        except Exception as e:
            raise Exception("获取图片错误", e)
        finally:
            # 释放资源，确保程序正常退出
            ThreadPoolExecutor().shutdown(wait=False)