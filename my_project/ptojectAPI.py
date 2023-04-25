import json

from PIL import Image
from common import IniFileEditor, MakePhotos, GetValue, Request


class MakePhoto:
    def __init__(self,interface,name):
        self.config = json.loads(IniFileEditor().read_ini_file())

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

        if isinstance(old_dict,dict) or isinstance(old_dict,str):
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
            get_value = MakePhotos(self.template_image).recognize_text(self.section["ttf_path"], self.section["font_size"]
                                                                          ,self.section["adjust_coor"]
                                                                          ,self.section["font_color"],self.section["save_path"])
            get_value = self._replace_dict(get_value, self.parameter_dic)
            IniFileEditor().set_value("card_parameter_dictionary","template_path",self.template_image_name)
            IniFileEditor().write_value("card_template",get_value)
            IniFileEditor().set_value("card","need_change","false")
        # 获取名片信息
        msg = Request.get_json(GetValue(self.name).get_card())
        # 判断舰队图标是否为空
        if msg["ass_image_path"] == "need_empty":
            msg["ass_image_path"] = self.no_fleet
        # 绘制舰队图标
        self.back_ground_image = MakePhotos(self.back_ground_image) \
            .photo_to_photo(msg["ass_image_path"], self.template["ass_image_size"], self.template["ass_image_coordinate"])

        self.back_ground_image = MakePhotos(self.back_ground_image) \
            .photo_to_photo(msg["medal_image_path"], self.template["medal_image_size"], self.template["medal_image_coordinate"],hierarchy="upper")

        self.back_ground_image = MakePhotos(self.back_ground_image) \
            .photo_to_photo(msg["user_image_path"], self.template["user_image_size"], self.template["user_image_coordinate"])


        self.back_ground_image = MakePhotos(self.back_ground_image).text_to_photo(msg, self.section["ttf_path"]
                                          ,self.section["font_size"] ,self.section["font_color"],self.template)
        # 将图像保存为 PNG 格式

        return self.back_ground_image

    def make_boat(self):


        if self.template_image_name != self.parameter_dic["template_path"] or self.section["need_change"] != "false":
            get_value = MakePhotos(self.template_image).recognize_text(self.section["ttf_path"], self.section["font_size"]
                                                                          ,self.section["adjust_coor"]
                                                                          ,self.section["font_color"],self.section["save_path"])
            get_value = self._replace_dict(get_value, self.parameter_dic)
            # 自动回填模版地址
            IniFileEditor().set_value("boat_parameter_dictionary","template_path",self.template_image_name)
            # 回填模版地址坐标
            IniFileEditor().write_value("boat_template",get_value)
            # 将判断改变字段回填false
            IniFileEditor().set_value("boat","need_change","false")
            # 获取名片信息
            msg = Request.get_json(GetValue(self.name).get_card())

