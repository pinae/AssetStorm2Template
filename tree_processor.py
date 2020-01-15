# -*- coding: utf-8 -*-
import requests
import re


class IllegalAssetStormStructureError(Exception):
    pass


class TreeProcessor(object):
    def __init__(self, asset_storm_url="https://assetstorm.pinae.net"):
        self.asset_storm_url = asset_storm_url
        self.template_cache = {}

    def get_template(self, asset_type_name: str) -> dict:
        if asset_type_name in self.template_cache.keys():
            return self.template_cache[asset_type_name]
        response = requests.get(
            self.asset_storm_url + "/get_template",
            params={
                "type_name": asset_type_name,
                "template_type": "proof_html"})
        return response.text

    def run(self, tree: dict) -> str:
        if "type" not in tree:
            raise IllegalAssetStormStructureError
        consumable_template = self.get_template(tree["type"])
        for key in tree.keys():
            key_list_regex = r"^(?P<start_part>[\s\S]*?){{for\(" + key + \
                             r"\)}}(?P<list_template>[\s\S]*?){{endfor}}(?P<end_part>[\s\S]*)"
            key_regex = r"^(?P<start_part>[\s\S]*?){{" + key + r"}}(?P<end_part>[\s\S]*)"
            list_matches = re.match(key_list_regex, consumable_template, re.MULTILINE)
            while list_matches:
                list_content = ""
                for list_item in tree[key]:
                    consumable_list_template = list_matches.groupdict()["list_template"]
                    matches = re.match(key_regex, consumable_list_template, re.MULTILINE)
                    while matches:
                        if type(list_item) is dict:
                            item_text = self.run(list_item)
                        else:
                            item_text = list_item
                        consumable_list_template = matches.groupdict()["start_part"] + \
                                                   item_text + \
                                                   matches.groupdict()["end_part"]
                        matches = re.match(key_regex, consumable_list_template, re.MULTILINE)
                    list_content += consumable_list_template
                consumable_template = list_matches.groupdict()["start_part"] + \
                                      list_content + \
                                      list_matches.groupdict()["end_part"]
                list_matches = re.match(key_list_regex, consumable_template, re.MULTILINE)
            matches = re.match(key_regex, consumable_template, re.MULTILINE)
            while matches:
                if type(tree[key]) is dict:
                    key_text = self.run(tree[key])
                else:
                    key_text = tree[key]
                consumable_template = matches.groupdict()["start_part"] + \
                                      key_text + \
                                      matches.groupdict()["end_part"]
                matches = re.match(key_regex, consumable_template, re.MULTILINE)
        return consumable_template
