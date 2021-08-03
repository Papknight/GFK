import json
import time
import pyautogui
import copy
from typing import List, Union, Optional, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs

from dictionary import GfkDictionary, Category, ComplexEncoder


class GfkHitlistScrapper:

    def __init__(self, log_in_url: str, hitlist_url: str):
        self.log_in_url: str = log_in_url
        self.hitlist_url: str = hitlist_url
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ['enable-automation'])
        driver_path: str = './chromedriver.exe'
        self.driver = webdriver.Chrome(executable_path=driver_path, options=options)
        self.gfk_dict: GfkDictionary = self.set_gfk_dict('gfk_dict.txt')
        self.hitlist_file = 'hitlist_data.csv'

    def set_gfk_dict(self, file_path):
        gfk_dict = GfkDictionary()
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()
        if len(data) > 0:
            json_str = json.loads(data)
            for category in json_str['categories']:
                gfk_dict.update_category(Category(**category))
        return gfk_dict

    def log_in(self) -> None:
        self.driver.get(self.log_in_url)
        time.sleep(3)
        if self.driver.current_url == 'https://gfkconnect.gfk.com/sites/Neonet/Pages/Default.aspx':
            return None
        self.driver.find_element_by_id('userNameInput').send_keys('patryk.nowak@neonet.pl')
        self.driver.find_element_by_id('passwordInput').send_keys('Neonet2021!!')
        self.driver.find_element_by_id('submitButton').click()
        return None

    def get_source_html(self, url) -> None:
        self.driver.get(url)
        time.sleep(5)
        source = self.driver.page_source
        soup = bs(source, 'html.parser')
        prettyHTML = soup.prettify()
        with open('source.txt', 'w', encoding='utf-8') as f:
            f.write(prettyHTML)
        return None

    def reset_category_filter(self, lvl):
        self.driver.find_element_by_xpath(
            f"//li[@class='product-list-item uitest-Li-PFF-SelectedProductMenuItemValueOption level{lvl}']").find_element_by_tag_name(
            'em').click()

    def create_dictionary(self, hd_screen: bool, change_period: bool = False):
        new_gfk_dict = GfkDictionary()

        self.driver.get(self.hitlist_url)
        time.sleep(5)
        self.driver.fullscreen_window()
        if change_period:
            self.change_period(hd_screen)
        self.click_category_menu()
        self.reset_category_filter(1)
        time.sleep(1)

        lvl1_list = [lvl1.text for lvl1 in self.get_loaded_list_items()]
        for lvl1 in lvl1_list:
            self.click_category_levels(lvl1)

            lvl2_list = [lvl2.text for lvl2 in self.get_loaded_list_items()]
            for lvl2 in lvl2_list:
                self.click_category_levels(lvl2)

                lvl3_list = [lvl3.text for lvl3 in self.get_loaded_list_items()]
                for lvl3 in lvl3_list:
                    self.click_category_levels(lvl3)
                    time.sleep(3)

                    brands = [brand.text for brand in self.get_loaded_list_items()]

                    features_menu = self.driver.find_elements_by_xpath(
                        "//li[@class='feature-list-item uitest-Li-FF-SelectedFeatureValueOption ng-scope']")
                    features = {}
                    for feature_elem in features_menu:
                        feature_name = feature_elem.find_element_by_xpath(
                            ".//div[@class='feature-selected-title ng-binding']").text
                        feature_elem.click()
                        features[feature_name] = [feature.text for feature in self.driver.find_elements_by_xpath(
                            "//li[@class='uitest-Li-FF-FeatureValueOption ng-binding ng-scope']") if
                                                  feature.text != '']
                    time.sleep(1)
                    price_classes = self.get_price_classes()

                    category = Category(lvl1, lvl2, lvl3, brands, features, price_classes)
                    new_gfk_dict.update_category(category)

                    self.reset_category_filter(3)

                self.reset_category_filter(2)

            self.reset_category_filter(1)
            pyautogui.move(0, -1, 0.5)

        self.gfk_dict = new_gfk_dict
        json_str = json.dumps(new_gfk_dict.reprJSON(), cls=ComplexEncoder, indent=4)
        with open('gfk_dict.txt', 'w', encoding='utf-8') as f:
            f.write(json_str)

    def get_category_filter_value(self, lvl):
        return self.driver.find_element_by_xpath(
            f"//li[@class='product-list-item uitest-Li-PFF-SelectedProductMenuItemValueOption level{lvl}']").find_element_by_tag_name(
            'em').text

    # usunąć em? chyba niepotrzebny

    def check_if_brand_is_filtered(self):
        return len(self.driver.find_elements_by_xpath(
            f"//li[@class='product-list-item uitest-Li-PFF-SelectedProductMenuItemValueOption level4']")) > 0

    def click_category_menu(self, index=0):
        # menu_selector = WebDriverWait(self.driver, 20).until(
        #     EC.visibility_of_all_elements_located((By.XPATH, "//span[@class='ng-binding ng-scope']")))[index]
        menu_selector = self.driver.find_elements_by_xpath("//span[@class='ng-binding ng-scope']")[index]
        menu_selector.click()

    def get_loaded_list_items(self):
        return self.driver.find_elements_by_xpath(
            "//li[@class='product-sublist-item uitest-Li-PFF-SelectedProductMenuSubItemValueOption data-status-loaded']")

    def click_category_levels(self, lvl, brand: bool = False) -> None:
        if not brand:
            self.driver.find_element_by_xpath(
                "//ul[@class='product-sublist-pane']").find_element_by_xpath(f"//li[contains(text(), '{lvl}')]").click()
            return None
        else:
            brands = self.driver.find_element_by_xpath(
                "//ul[@class='product-sublist-pane']").find_elements_by_xpath(f"//li[contains(text(), '{lvl}')]")
            for li in brands:
                # print(li.text.strip)
                if li.text.strip() == lvl:
                    li.click()
                    return None
            print('Nie znaleziono marki')

            # self.driver.find_element_by_xpath(
            #     "//ul[@class='product-sublist-pane']").find_element_by_xpath(f"//li[text()='{lvl}']").click()

    def get_feature_group_element(self, feature_group):
        time.sleep(1)
        for li in self.driver.find_elements_by_xpath(
                "//li[@class='feature-list-item uitest-Li-FF-SelectedFeatureValueOption ng-scope']"):
            fg = li.find_element_by_xpath(".//div[@class='feature-selected-title ng-binding']")
            if fg.text == feature_group:
                return fg
        return None

    def get_feature_element(self, feature):
        time.sleep(1)
        # pyautogui.move(0, -1, 0.5)
        for f in self.driver.find_elements_by_xpath(
                f"//li[(@class='uitest-Li-FF-FeatureValueOption ng-binding ng-scope')]"):
            if f.text == feature:
                return f
        return None

    def get_price_element(self, price_class):
        time.sleep(1)
        for pc in self.driver.find_elements_by_xpath(
                f"//li[(@class='uitest-Li-PC-PriceClassOption ng-binding ng-scope')]"):
            if pc.text == price_class:
                return pc
        return None

    def click_feature_element(self, feature):
        self.driver.find_element_by_xpath(
            "//ul[@class='ng-scope']").find_element_by_xpath(f".//li[contains(text(), '{feature}')]").click()

    def click_price_class_element(self, price_class):
        for pc in self.driver.find_elements_by_xpath(
                f"//li[(@class='uitest-Li-PC-PriceClassOption ng-binding ng-scope')]"):
            if pc.text == price_class:
                pc.click()
                return None
        return None

    def get_price_classes(self):
        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located(
            (By.XPATH,
             "//div[@class='priceclass-filter-selected-priceclass uitest-Div-PC-SelectedPriceClass']"))).click()
        return [price_class.text for price_class in self.driver.find_elements_by_xpath(
            "//li[@class='uitest-Li-PC-PriceClassOption ng-binding ng-scope']")]

    def reset_feature_filters(self):
        time.sleep(1)
        feature_groups = self.driver.find_elements_by_xpath(
            "//div[@class='feature-value-selected-title is-filter-all is-filter-other']")
        for fg in feature_groups:
            fg.find_element_by_xpath(".//em").click()
            time.sleep(1)

    def reset_price_filter(self):
        time.sleep(1)
        selectors = self.driver.find_elements_by_xpath(
            "//div[@class='priceclass-filter-selected-priceclass-title is-filter-all is-filter-other']")
        if len(selectors):
            selectors[0].find_element_by_xpath(".//em").click()

    def generate_scraping_list(self, categories: List[Category],
                               constr: Optional[List[str]] = None,
                               pos_type_all: bool = False, pos_types_specific: Optional[List[str]] = None,
                               brands_all: bool = False, brands_specific: Optional[List[str]] = None,
                               features_all: bool = False, features_specific: Optional[List[str]] = None,
                               price_all: bool = False, price_specific: Optional[List[str]] = None):
        # with open("to_scrap.txt", 'r') as text:
        #     scrap_lis = []
        #     lines = text.read().splitlines()
        #     for line in lines:
        #         if line in scrap_lis:
        #             pass
        #         else:
        #             scrap_lis.append(line)
        #     list_scrap = cat_lis[:]

        scraping_list = []
        index = 0
        with open("categories.txt", 'r') as textfile:
            cat_lis = []
            lines = textfile.read().splitlines()
            for line in lines:
                if line in cat_lis:
                    pass
                else:
                    cat_lis.append(line)
            category_list = cat_lis[:]

        for category in categories:
            if category not in cat_lis:
                if pos_types_specific is not None:
                    pos_types = pos_types_specific
                else:
                    pos_types = ['Total']
                    if pos_type_all:
                        pos_types.extend(['Offline', 'Online'])
                for pos_type in pos_types:
                    if brands_specific is not None:
                        brand_filters = brands_specific
                    else:
                        brand_filters = ['Total']
                        if brands_all:
                            brand_filters.extend(category.brands)
                    for brand in brand_filters:
                        if constr is not None:
                            construction_features = constr
                        else:
                            if 'CONSTR.2' in category.features.keys():
                                construction_features = ['BUILT IN/UNDER', 'FREESTANDING']
                            else:
                                construction_features = ['n/a']
                        for construction in construction_features:
                            feature_group_filters_keys = ['Total']
                            if features_all:
                                feature_group_filters_keys.extend(category.features.keys())
                                if 'CONSTR.2' in category.features.keys():
                                    feature_group_filters_keys.remove('CONSTR.2')
                            for feature_group in feature_group_filters_keys:
                                if features_all and feature_group == 'Total' or not features_all:
                                    feature_filters = ['Total']
                                else:
                                    feature_filters = category.features[feature_group]
                                for feature_filter in feature_filters:
                                    price_filters = ['Total']
                                    if price_all:
                                        price_filters.extend(category.price_classes)
                                    for price_filter in price_filters:
                                        new_item = {'index': index,
                                                    'category': category.name,
                                                    'pos_type': pos_type,
                                                    'brand': brand,
                                                    'constr': construction,
                                                    'feature_group': feature_group,
                                                    'feature_filter': feature_filter,
                                                    'price_class': price_filter,
                                                    'finished': False}
                                        if category.name in cat_lis:
                                            pass
                                        else:
                                            category_list.append(category.name)

                                            scraping_list.append(new_item)
                                            index += 1
            else:
                pass

        with open('categories.txt', 'w') as f:
            f.write('\n'.join(cat_lis))
        self.save_scraping_list(scraping_list)

    def set_hitlist_report(self, hd_screen: bool, change_period: bool = False):
        self.driver.get(self.hitlist_url)
        time.sleep(3)
        self.driver.fullscreen_window()
        if change_period:
            self.change_period(hd_screen)
        # self.toggle_ranks()

    def save_scraping_list(self, scraping_list: List[Dict[str, Union[str, int, bool]]],
                           file: str = 'scraping_list.txt') -> None:
        with open(file, 'w') as f:
            json.dump(scraping_list, f, indent=4)
            # f.write(json.dumps(scraping_list, indent=4))

    def gfk_hitlists_scraping(self, hd_screen: bool, change_period: bool = False) -> None:

        with open('scraping_list.txt', 'r') as f:
            scraping_list = json.load(f)

        index = 0
        for i in scraping_list:
            if i['finished'] is False:
                index = i['index']
                break

        while index < len(scraping_list):
            current_item = scraping_list[index]
            try:
                self.get_hitlist(current_item['category'], current_item['pos_type'], current_item['brand'],
                                 current_item['constr'], current_item['feature_group'], current_item['feature_filter'],
                                 current_item['price_class'], hd_screen)

                scraping_list[index]['finished'] = True
                self.save_scraping_list(scraping_list)
                index += 1
            except:
                print('Zepsuło się!')

                with open(self.hitlist_file, 'r') as f:
                    lines = f.readlines()
                with open(self.hitlist_file, 'w') as f:
                    end_index = len(lines)
                    for i in range(len(lines) - 1, -1, -1):
                        line_data = lines[i].split(';')
                        print(line_data)
                        line_data = line_data[:13]
                        if line_data[0] == current_item['pos_type'] and line_data[3] == current_item['category'] and \
                                line_data[5] == current_item['brand'] and line_data[6] == current_item['constr'] and \
                                line_data[8] == current_item['feature_group'] and line_data[10] == current_item[
                            'feature_filter'] and line_data[12] == current_item['price_class']:
                            end_index -= 1
                        else:
                            break
                    for j in lines[:end_index]:
                        f.write(j)

                # self.end_scraping()
                self.log_in()
                self.set_hitlist_report(hd_screen, change_period)
                pyautogui.move(0, -1, 0.5)
                continue
        return None

    def get_hitlist(self, category_name: str, pos_type: str, brand: str, constr: str, feature_group: str,
                    feature_filter: str, price_class: str, hd_screen: bool) -> None:

        self.check_and_change_pos_type_filters(pos_type, hd_screen)

        category = self.gfk_dict.get_category(category_name)
        self.click_category_menu()
        if self.get_category_filter_value(1) != category.lvl1:
            self.reset_category_filter(1)
            self.click_category_levels(category.lvl1)
            self.click_category_levels(category.lvl2)
            self.click_category_levels(category.name)
        elif self.get_category_filter_value(2) != category.lvl2:
            self.reset_category_filter(2)
            self.click_category_levels(category.lvl2)
            self.click_category_levels(category.name)
        elif self.get_category_filter_value(3) != category.name:
            self.reset_category_filter(3)
            self.click_category_levels(category.name)

        if self.check_if_brand_is_filtered():
            if self.get_category_filter_value(4) != brand:
                self.reset_category_filter(4)
        if brand != 'Total':
            time.sleep(2)
            self.click_category_levels(brand, True)

        self.reset_price_filter()
        self.reset_feature_filters()

        constr_changed = self.change_construction_type(constr)
        if not constr_changed:
            self.click_category_menu()
            return None

        if feature_group != 'Total':
            current_feature_group = self.get_feature_group_element(feature_group)
            if current_feature_group is None:
                self.click_category_menu()
                return None
            current_feature_group.click()
            current_feature = self.get_feature_element(feature_filter)
            if current_feature is None:
                self.click_category_menu()
                return None
            current_feature.click()

        time.sleep(1)
        price_selector = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.XPATH,
                                              "//div[@class='priceclass-filter-selected-priceclass uitest-Div-PC-SelectedPriceClass']")))

        # print(f'Pozycja selektora: {price_selector.location}')

        if price_class != 'Total':
            price_selector.click()
            if not self.get_price_element(price_class):
                self.click_category_menu()
                return None
            self.click_price_class_element(price_class)

        # testowanie pozycji kursora
        # print(f'kursor: {pyautogui.position()}')
        # new_position = self.driver.find_element_by_xpath(
        #     "//div[@class='priceclass-filter-selected-priceclass uitest-Div-PC-SelectedPriceClass']")
        # print(new_position.location)

        # na ekranie 1900x1080px:
        # szukamy pozycji selektora ceny i przesuwamy kursor o 60 pixeli poniżej; klikamy

        if hd_screen:
            self.click_apply(price_selector.location['x'] + 60, price_selector.location['y'] + 260)
        else:
            self.click_apply(price_selector.location['x'] + 60, price_selector.location['y'] + 60)

        self.get_hitlist_data(pos_type, category.lvl1, category.lvl2, category.name, brand, constr,
                              feature_group, feature_filter, price_class)
        return None

    def check_and_change_pos_type_filters(self, pos_type, hd_screen: bool) -> None:
        current_filters = self.driver.find_elements_by_xpath(
            "//div[@class = 'filter-options-container uitest-Div-FH-Container']/div/ul/li[@class = 'ng-binding ng-scope']")

        if pos_type == 'Total':
            for cf in current_filters:
                if cf.text in ['Offline', 'Online']:
                    self.change_pos_type_filter(pos_type, hd_screen)
        else:
            for cf in current_filters:
                if cf.text == pos_type:
                    return None
            self.change_pos_type_filter(pos_type, hd_screen)
        return None

    def change_construction_type(self, constr) -> bool:
        clicked = True
        if constr != 'n/a':
            clicked = False
            time.sleep(1)
            for x in self.driver.find_elements_by_xpath(
                    "//li[@class='feature-list-item uitest-Li-FF-SelectedFeatureValueOption ng-scope']"):
                fg_x = x.find_element_by_xpath(".//div[@class='feature-selected-title ng-binding']")
                if fg_x.text == 'CONSTR.2':
                    fg_x.click()
                    break
            time.sleep(1)
            for f_x in self.driver.find_elements_by_xpath(
                    f"//li[(@class='uitest-Li-FF-FeatureValueOption ng-binding ng-scope')]"):
                if f_x.text == constr:
                    f_x.click()
                    clicked = True
                    break
            time.sleep(1)
        return clicked

    def toggle_ranks(self):
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[@class='report-settings-container-toggle uitest-Div-SC-Toggle']"))).click()
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//span[contains(text(), 'Highlighting')]"))).click()
        self.driver.find_element_by_xpath("//input[@name='rank-comparison']").click()
        self.driver.find_element_by_xpath(
            "//div[@class='header-container-apply settings-container-apply uitest-Div-HC-Apply-']").click()
        time.sleep(1)

    def change_pos_type_filter(self, pos_type, hd_screen: bool):
        time.sleep(5)
        self.click_category_menu(1)
        pos_type_selector = self.driver.find_element_by_xpath(
            "//div[@class='postype-filter-selected-postype uitest-Div-PTF-SelectedPosType ng-binding']")
        pos_type_selector.click()
        for li in self.driver.find_elements_by_xpath(
                "//li[contains(@class, 'uitest-li-SF-SelectPosType')]"):
            if li.text == pos_type:
                li.click()
        if hd_screen:
            self.click_apply(pos_type_selector.location['x'] + 220, pos_type_selector.location['y'] + 200)
        else:
            self.click_apply(pos_type_selector.location['x'] + 60, pos_type_selector.location['y'] + 60)

    def change_period(self, hd_screen: bool):
        period_menu = self.driver.find_element_by_xpath(
            "//div[contains(@class, 'uitest-Div-HC-Container-periodFilter')]")
        period_menu.click()
        # menu_selector = WebDriverWait(self.driver, 20).until(
        #     EC.visibility_of_all_elements_located((By.XPATH, "//div[@class='header-container header-container-periodFilter uitest-Div-HC-Container-periodFilter']")))[0]
        # menu_selector.click()
        period_selector = self.driver.find_element_by_xpath(
            "//div[@class='uitest-Div-PF-SelectPeriodicity ng-binding period-filter-selected-period-more']")
        period_selector.click()
        for div in self.driver.find_elements_by_xpath(
                "//div[contains(@class, 'ng-scope period-filter-period-selection')]"):
            if div.text == "MAT":
                div.click()

        if hd_screen:
            self.click_apply(period_selector.location['x'] + 220, period_selector.location['y'] + 350)
        else:
            self.click_apply(period_selector.location['x'] + 60, period_selector.location['y'] + 220)
        time.sleep(5)

    @staticmethod
    def click_apply(x, y):
        pyautogui.click(x, y)
        time.sleep(3)

    def total_or_detail(self, name):
        if name == 'Total':
            return 'total'
        return 'detailed'

    def clear_hitlist_file(self):
        with open(self.hitlist_file, 'w') as f:
            f.write(
                # csv file header:
                'pos_type;category1;category2;category3;brand_details;brand;constr;feature_group_details;feature_group;feature_details;feature;price_class_details;price_class;top_type;rank_market;rank_s045;brand_description;item;sales_value_market;sales_value_s045;retailers_value_%_market;retailers_value_%_s045;sales_volume_market;sales_volume_s045;retailers_volume_%_market;retailers_volume_%_s045;asp_market;asp_s045\n')

    def get_hitlist_data(self, pos_type, cat_1, cat_2, cat_3, brand, constr, feature_group, feature_element,
                         price_class) -> None:

        time.sleep(5)
        # time.sleep(8)
        if len(self.driver.find_elements_by_xpath("//span[text()='There is no data to display.']")):
            return None

        brand_details = self.total_or_detail(brand)
        feature_group_details = self.total_or_detail(feature_group)
        feature_details = self.total_or_detail(feature_element)
        price_class_details = self.total_or_detail(price_class)

        basic_data = [pos_type, cat_1, cat_2, cat_3, brand_details, brand, constr, feature_group_details, feature_group,
                      feature_details, feature_element, price_class_details, price_class]

        table_body_rows = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//datatable-body[@class='datatable-body']"))).find_elements_by_xpath(
            ".//div[contains(@class, 'datatable-body-row')]")

        table_content_rows = self.driver.find_element_by_xpath(
            "//datatable-body[contains(@class, 'datatable-body') and contains(@class, 'main')]").find_elements_by_xpath(
            ".//div[contains(@class, 'datatable-body-row')]")

        if len(table_body_rows) == 13:
            cells_count = len(table_body_rows) - 1
        else:
            cells_count = len(table_body_rows)

        for i in range(cells_count):

            final_data = []
            final_data.extend(basic_data)

            if i == 0:
                final_data.append('summary')
            elif i == cells_count - 1:
                final_data.append('others')
            else:
                final_data.append('top10')

            final_data.extend([cell.text for cell in
                               table_body_rows[i].find_elements_by_xpath(
                                   ".//div[contains(@class, 'datatable-body-cell')]")])
            final_data.extend([cell.text for cell in table_content_rows[i].find_elements_by_xpath(
                ".//div[contains(@class, 'datatable-body-cell')]")])
            final_data.append('\n')

            with open(self.hitlist_file, 'a') as f:
                f.write(';'.join(final_data))

            final_data.clear()
        return None

    # do poprawy
    # def disable_percents(self, column_name):
    #     for div in self.driver.find_elements_by_xpath("//div[@class='datatable-header-cell-label-wrapper']"):
    #         print(div.text)
    #         if len(div.find_elements_by_xpath(f"//span[text()='{column_name}']")):
    #             print(div.text)
    #             div.find_element_by_xpath(".//span[@title='Remove column']").click()

    def categories_iterations(self, categories: List[Category], start_index: int = 0):
        print(f'Branża {categories[0].lvl1}')
        for category in categories[start_index:]:
            scraper.get_hitlists([category], pos_type_all=True, features=True, brands=True, price=True)
            print(f'Pobrano: {category.name} ({categories.index(category)} z {len(categories) - 1})')

    def end_scraping(self):
        self.driver.quit()


def prepare(scraper: GfkHitlistScrapper, hd_screen: bool, change_period: bool, clear_hitlist: bool) -> None:
    scraper.log_in()
    # scraper.get_source_html(scraper.hitlist_url)
    scraper.create_dictionary(hd_screen=hd_screen)
    scraper.gfk_dict.print_dict()
    if clear_hitlist:
        scraper.clear_hitlist_file()
    # scraper.set_hitlist_report(hd_screen, change_period)

    my_MDA_categories = scraper.gfk_dict.get_lvl1_categories('Major Domestic Appliances')
    # my_SDA_categories = scraper.gfk_dict.get_lvl1_categories('Small Domestic Appliances')
    # my_CE_categories = scraper.gfk_dict.get_lvl1_categories('Consumer Electronics')
    # my_MTG_categories = scraper.gfk_dict.get_lvl1_categories('Multifunctional Technical Good')
    # my_OE_categories = scraper.gfk_dict.get_lvl1_categories('Office Equipment')
    # my_Telecom_categories = scraper.gfk_dict.get_lvl1_categories('Telecom')
    # my_IT_categories = scraper.gfk_dict.get_lvl1_categories('Information Technology')
    # my_Photo_categories = scraper.gfk_dict.get_lvl1_categories('Photo')

    my_categories = []
    # my_categories.extend(my_CE_categories)
    my_categories.extend(my_MDA_categories)
    # my_categories.extend(my_SDA_categories)
    # my_categories.extend(my_Telecom_categories)
    # my_categories.extend(my_IT_categories)
    # my_categories.extend(my_MTG_categories)
    # my_categories.extend(my_OE_categories)
    # my_categories.extend(my_Photo_categories)

    # cat1 = scraper.gfk_dict.get_category('COOKING')
    # cat2 = scraper.gfk_dict.get_category('COOLING')
    # cat3 = scraper.gfk_dict.get_category('HOODS')
    # cat4 = scraper.gfk_dict.get_category('WASHINGMACHINES')
    # cat5 = scraper.gfk_dict.get_category('TUMBLEDRYERS')
    # cat6 = scraper.gfk_dict.get_category('FREEZERS')
    # cat7 = scraper.gfk_dict.get_category('MICROWAVE OVENS')

    # brands = ['SAMSUNG', 'ELECTROLUX', 'AMICA', 'BOSCH', 'BEKO', 'WHIRLPOOL', 'LG', 'SIEMENS', 'GORENJE', 'INDESIT',
    #           'CANDY']

    # my_categories = [cat2, cat3, cat5, cat6]

    # constr.2 types: 'BUILT IN/UNDER', 'FREESTANDING'
    scraper.generate_scraping_list(categories=my_categories, pos_type_all=True,
                                   pos_types_specific=['Offline', 'Online'],
                                   brands_all=False, features_all=True, price_all=True)
                                   # brands_all=True, brands_specific=brands, features_all=True, price_all=True)
    scraper.end_scraping()
    return None


def scraping_procedure(scraper:GfkHitlistScrapper, hd_screen, change_period):
    scraper.log_in()
    scraper.set_hitlist_report(hd_screen, change_period)
    scraper.gfk_hitlists_scraping(hd_screen, change_period)  # main scraping method
    scraper.end_scraping()


if __name__ == '__main__':
    log_in_url = 'https://federation.gfk.com/adfs/ls?wa=wsignin1.0&wtrealm=urn%3agfkconnect%3afederation.gfk.com&wctx=https%3a%2f%2fgfkconnect.gfk.com%2f_layouts%2fAuthenticate.aspx%3fSource%3d%252F&RedirectToIdentityProvider=AD+AUTHORITY&sec=true'
    # url = 'https://insightui.gfk.com/report/116a?docId=36458' # maj
    # url = 'https://insightui.gfk.com/report/116a?docId=41309' # czerwiec
    # url = 'https://insightui.gfk.com/report/116a?docId=45715'  # lipiec
    # url = 'https://insightui.gfk.com/report/116a?docId=50661'  # sierpień
    # url = 'https://insightui.gfk.com/report/116a?docId=66400'  # listopad
    # url = 'https://insightui.gfk.com/report/116a?docId=69499'  # grudzień 2020
    # url = 'https://insightui.gfk.com/report/116a?docId=72440'  # styczeń 2021
    # url = 'https://insightui.gfk.com/report/116a?docId=76491'  # luty 2021
    # url = 'https://insightui.gfk.com/report/116a?docId=81482' # marzec 2021
    # url = 'https://insightui.gfk.com/report/116a?docId=86087' # kwiecień 2021
    # url = 'https://insightui.gfk.com/report/116a?docId=91761' # maj 2021
    url = 'https://insightui.gfk.com/report/116a?docId=95268'  # czerwiec 2021

    hd_screen = True
    change_period = False

    scraper = GfkHitlistScrapper(log_in_url, url)
    prepare(scraper, hd_screen, change_period, clear_hitlist=False)
    # scraping_procedure(scraper, hd_screen, change_period)

    # 24h
    