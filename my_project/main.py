# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


# Press the green button in the gutter to run the script.
import configparser

from my_project.common import IniFileEditor, GetValue, MakePhotos
from my_project.ptojectAPI import MakePhoto

if __name__ == '__main__':
    # print(GetValue("fkbaicai").get_card())
    # make_photos().photo_to_photo("/Users/haiboyuan/Desktop/th.jpeg","/Users/haiboyuan/Desktop/th (1).jpeg",0,0)
    # open("/Users/haiboyuan/Desktop/th.jpeg")
    # config = IniFileEditor().read_ini_file()
    # section = dict(config["card"])
    # print(section,type(section))
    # print(IniFileEditor("./config.ini").read_ini_file())
    # MakePhoto().make_card('fkbaicai')
    # print(MakePhotos("/Users/haiboyuan/Desktop/1.png").recognize_text())
    config = configparser.ConfigParser()
    config.read('config.ini')

    # make_photos().text_to_photo()
    # getIni().get_card()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
