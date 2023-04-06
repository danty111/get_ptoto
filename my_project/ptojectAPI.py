import json
import os

from PIL import Image
from my_project.common import IniFileEditor, MakePhotos, GetValue, Request


class MakePhoto:
    def __init__(self):
        self.config = json.loads(IniFileEditor().read_ini_file())
        self.back_ground_image = Image.open(self.config["card"]["background"])
        self.template_image_name = self.config["card"]["background"].replace(".", "_template.")
        self.template_image = Image.open(self.template_image_name)

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

    def make_card(self, name):
        # 获取卡片配置参数
        section = self.config["card"]
        # 获取名片位置参数
        template = self.config["card_template"]
        # 获取名称对应字典
        parameter_dic = self.config["parameter_dictionary"]
        # 识别模版
        if self.template_image_name != parameter_dic["template_path"]:
            get_value = MakePhotos(self.template_image).recognize_text(section["ttf_path"], section["font_size"]
                                                                          ,section["adjust_coor"]
                                                                          ,section["font_color"],section["save_path"])
            get_value = self._replace_dict(get_value, parameter_dic)
            get_value["template_path"] = self.template_image_name
            IniFileEditor().write_value("card_template",get_value)
        # 获取名片信息
        msg = Request.get_json(GetValue(name).get_card())
        self.back_ground_image = MakePhotos(self.back_ground_image) \
            .photo_to_photo(msg["ass_image_path"], template["ass_image_size"], template["ass_image_coordinate"])
        self.back_ground_image = MakePhotos(self.back_ground_image) \
            .photo_to_photo(msg["user_image_path"], template["user_image_size"], template["user_image_coordinate"])

        self.back_ground_image = MakePhotos(self.back_ground_image).text_to_photo(msg, section["ttf_path"], template)
        # 将图像保存为 PNG 格式

        return self.back_ground_image
