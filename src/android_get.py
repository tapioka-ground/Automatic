import os
import sys
import subprocess
import xml.etree.ElementTree as ET

class Android_subprocess():
    def __init__(self,):
        self.hash = ""





    def get_xml_tree():
        subprocess.run(["adb","shell","uiautomator","dump","/sdcard/view.xml"])
        subprocess.run(["adb","pull","/sdcard/view.xml"])