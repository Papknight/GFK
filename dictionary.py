import json
from typing import List, Dict


class Category:

    def __init__(self, lvl1: str, lvl2: str, lvl3: str, brands: List[str], features: Dict[str, List[str]],
                 price_classes: List[str]):
        self.lvl1: str = lvl1
        self.lvl2: str = lvl2
        self.name: str = lvl3
        self.brands: List[str] = brands
        self.features: Dict[str, List[str]] = features
        self.price_classes: List[str] = price_classes

    def reprJSON(self):
        return dict(lvl1=self.lvl1, lvl2=self.lvl2, lvl3=self.name, brands=self.brands, features=self.features,
                    price_classes=self.price_classes)


class GfkDictionary:
    def __init__(self):
        self.categories = []

    def update_category(self, category: Category) -> None:
        if category.name in [cat.name for cat in self.categories]:
            print(f'Kategoria już występuje: {category.name}. Podmieniam!')
            for cat in self.categories:
                if cat.name == category.name:
                    self.categories.remove(cat)
                    break
        new_category = category
        self.categories.append(new_category)
        return None

    def get_lvl1(self) -> set:
        return {category.lvl1 for category in self.categories}

    def get_lvl2(self, lvl1) -> set:
        return {category.lvl2 for category in self.categories if category.lvl1 == lvl1}

    def get_lvl3(self, lvl1, lvl2) -> set:
        return {category for category in self.categories if category.lvl1 == lvl1 and category.lvl2 == lvl2}

    def print_dict(self, detailed=False) -> None:
        for lvl1 in self.get_lvl1():
            print(lvl1)
            for lvl2 in self.get_lvl2(lvl1):
                print('{:10}{}'.format('', lvl2))
                for lvl3 in self.get_lvl3(lvl1, lvl2):
                    print('{:20}{}'.format('', lvl3.name))
                    if detailed:
                        print('{:30}{}'.format('', str(lvl3.brands)))
                        print('{:30}{}'.format('', str(lvl3.features)))
                        print('{:30}{}'.format('', str(lvl3.price_classes)))
        return None

    def get_category(self, name) -> Category:
        return [category for category in self.categories if category.name == name][0]

    def get_lvl1_categories(self, name) -> List[Category]:
        return [cat for cat in self.categories if cat.lvl1 == name]

    def reprJSON(self) -> dict:
        return dict(categories=self.categories)


class ComplexEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, 'reprJSON'):
            return o.reprJSON()
        else:
            return json.JSONEncoder.default(self, o)
