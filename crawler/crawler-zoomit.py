from asyncio.windows_events import NULL
from decimal import ROUND_UP
from pickle import FALSE, TRUE
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import os
import re
import datetime
import time as t
from lxml import html

class ShopCrawler:
    def __init__(self):
        self.baseURL = 'https://www.zoomit.ir/'
        self.data_path = './Data'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36', 
            'accept-language': 'en-US'
        }
        self.dataframe_names    = ['zoomit_laptops_url', 'zoomit']
        self.zoomit_laptops_url = pd.DataFrame(columns=['url'])
        self.zoomit             = pd.DataFrame(columns=['url', 'Title', 'Manufacturer', 'Model_Name', 'Screen_Size', 'Resolution', 'CPU', 'RAM', 'RAM_type', 'Storage', 'Storage_type', 'GPU', 'GPU_RAM', 'Size', 'Weight', 'Score', 'Battery_life', 'Price'])
        self.flag_laptop        = 0
        
    def start_crawling(self):
        self.create_data_directory()
        
        for df_name in self.dataframe_names:
            self.load_csv(df_name)
            
        # get all books url    
        # self.crawl_pagination()
                   
        self.crawl_laptop_page()      
        
                  
    def create_data_directory(self):
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
            
    def load_csv(self, df_name):
        file_path = os.path.join(self.data_path, df_name + '.csv')

        if not os.path.exists(file_path):
            df_columns = getattr(self, df_name).columns
            df = pd.DataFrame(columns=df_columns)
            df.to_csv(file_path, index=False)

        setattr(self, df_name, pd.read_csv(file_path))
     
    def save_csv(self, df_name):
        file_path = os.path.join(self.data_path, df_name + '.csv')
        df = getattr(self, df_name)
        df.to_csv(file_path, index=False)
           
    def save_all_csv(self, df_name):
        file_path = os.path.join(self.data_path, df_name + '.csv')
        df = getattr(self, df_name)
        df.to_csv(file_path, mode='a', index=False, header=False) 
   
                
    def scrap_every_page(self, page):
        new_laptop_url = pd.DataFrame(columns=['url'])
        page_url = self.baseURL + '/product/list/laptop/page/'+ str(page)
        pagination_req_failed_count = 0
        while pagination_req_failed_count < 3:
            try:
                response = requests.get(page_url, headers=self.headers)
                if response.status_code != 200:
                    raise Exception(f"status code is: {response.status_code}")
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                laptops = soup.find_all('div' , attrs={'class' : 'row productSummery'})
                for laptop in laptops:
                    laptop_url = laptop.find('div', attrs={'class' : 'col-sm-4 col-md-3 col-xs-8 productSummery__title'}).find('a')['href']
                    new_laptop_url.loc[len(new_laptop_url)] = [laptop_url]
                return new_laptop_url
                
            except Exception as e:
                pagination_req_failed_count += 1
                print(e)

    def crawl_pagination(self):
        print("get_all_books_url started")
        
        req_failed_count = 0

        while req_failed_count < 3:
            try:
                
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = (executor.submit(self.scrap_every_page, page) for page in range(1, 56))
                    for future in as_completed(futures):
                        new_laptop_url = future.result()   

                        if new_laptop_url is not None:
                            for i in range(len(new_laptop_url)):
                                self.zoomit_laptops_url.loc[len(self.zoomit_laptops_url)] = [new_laptop_url['url'][i]]
                            print(len(self.zoomit_laptops_url))
                            self.save_all_csv('zoomit_laptops_url')
                        
                break

            except Exception as e:
                req_failed_count += 1
                print(e)

        print("get_all_books_url finished")
    
    def scrap_every_laptop_page(self, url):
        page_url = url
        pagination_req_failed_count = 0

        while pagination_req_failed_count < 3:
            try:
                response = requests.get(page_url, headers=self.headers)
                if response.status_code != 200:
                    raise Exception(f"status code is: {response.status_code}")
                
                laptop_page = BeautifulSoup(response.content, 'html5lib')
                
                return url, laptop_page
                
            except Exception as e:
                pagination_req_failed_count += 1
                print("1:",e)

    def crawl_laptop_page(self):
        print("get_all_books_page started")
        
        req_failed_count = 0
        while req_failed_count < 3:
            try:
                new_url = {}
                for i in range(len(self.zoomit_laptops_url)):
                    new_url[self.zoomit_laptops_url.iloc[i]['url']] = self.zoomit_laptops_url.iloc[i]['url']
                
                for i in range(len(self.zoomit)):
                    if self.zoomit.iloc[i]['url'] in new_url:
                        new_url.pop(self.zoomit.iloc[i]['url'])

                self.flag_laptop += len(self.zoomit)
                
                
                self.zoomit = pd.DataFrame(columns=['url', 'Title', 'Manufacturer', 'Model_Name', 'Screen_Size', 'Resolution', 'CPU', 'RAM', 'RAM_type', 'Storage', 'Storage_type', 'GPU', 'GPU_RAM', 'Size', 'Weight', 'Score', 'Battery_life', 'Price'])



                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = (executor.submit(self.scrap_every_laptop_page, url) for url in new_url.values())
                                           
                    for future in as_completed(futures):
                        url, laptop_page = future.result()   
                        self.crawl_laptop_page_all(url, laptop_page)
                
                break

            except Exception as e:
                req_failed_count += 1
                print("2:",e)
                
        if len(self.zoomit) > 0:
            self.flag_laptop += len(self.zoomit)
            print(self.flag_laptop) 
            self.save_all_csv('zoomit')

        print("get_all_books_pages finished")
        
    def crawl_laptop_page_all(self, url, laptop_page):
        print(url)
        title_tag = laptop_page.find('div' , attrs={'class' : 'ProductTitle'}).find('h1')
        
        if title_tag is not None: 
            title = title_tag.text
        else:
            title = ""
            
        title_en_tag = laptop_page.find('div' , attrs={'class' : 'ProductTitle'}).find('h2')
        
        if title_en_tag is not None:
            title_en = title_en_tag.text
            if "ASUS" in title_en:
                model = "ASUS"
                manufacturer = title_en.replace("ASUS", '')
            elif "MICROSOFT" in title_en:
                model = "MICROSOFT"
                manufacturer = title_en.replace("MICROSOFT", '')
            elif "MSI" in title_en:
                model = "MSI"
                manufacturer = title_en.replace("MSI", '')
            elif "VAIO" in title_en:
                model = "VAIO"
                manufacturer = title_en.replace("VAIO", '')
            elif "LENOVO" in title_en:
                model = "LENOVO"
                manufacturer = title_en.replace("LENOVO", '')
            elif "ACER" in title_en:
                model = "ACER"
                manufacturer = title_en.replace("ACER", '')
            elif "SAMSUNG" in title_en:
                model = "SAMSUNG"
                manufacturer = title_en.replace("SAMSUNG", '')
            elif "FUJITSU" in title_en:
                model = "FUJITSU"
                manufacturer = title_en.replace("FUJITSU", '')
            elif "APPLE" in title_en:
                model = "APPLE"
                manufacturer = title_en.replace("APPLE", '')
            elif "HUAWEI" in title_en:
                model = "HUAWEI"
                manufacturer = title_en.replace("HUAWEI", '')
            elif "XIAOMI" in title_en:
                model = "XIAOMI"
                manufacturer = title_en.replace("XIAOMI", '')
            elif "LG" in title_en:
                model = "LG"
                manufacturer = title_en.replace("LG", '')
            elif "HP" in title_en:
                model = "HP"
                manufacturer = title_en.replace("HP", '')
            elif "DELL" in title_en:
                model = "DELL"
                manufacturer = title_en.replace("DELL", '')
            elif "RAZER" in title_en:
                model = "RAZER"
                manufacturer = title_en.replace("RAZER", '')
            elif "HONOR" in title_en:
                model = "HONOR"
                manufacturer = title_en.replace("HONOR", '')
            elif "I-LIFE" in title_en:
                model = "I-LIFE"
                manufacturer = title_en.replace("I-LIFE", '')
            elif "GOOGLE" in title_en:
                model = "GOOGLE"
                manufacturer = title_en.replace("GOOGLE", '')
            elif "GIGABYTE" in title_en:
                model = "GIGABYTE"
                manufacturer = title_en.replace("GIGABYTE", '')
            elif "TOSHIBA" in title_en:
                model = "TOSHIBA"
                manufacturer = title_en.replace("TOSHIBA", '')
            elif "X.VISION" in title_en:
                model = "X.VISION"
                manufacturer = title_en.replace("X.VISION", '')
            else:
                manufacturer = ""
                model = ""
        else:
            manufacturer = ""
            model = ""
          
        tbody = laptop_page.find_all('tbody' , attrs={'class' : 'specificationsBody'})
        
        screen_size = resolution = cpu = ram = ram_type = storage = storage_type = gpu = gpu_ram = size = weight = battery_life = None
        
        for tb in tbody:
            tr_tbody = tb.findAll('tr')
            for tr in tr_tbody:
                td_tr = tr.findAll('td')
                if td_tr[0].text == "اندازه صفحه‌نمایش":
                    screen_size = td_tr[1].text
                elif td_tr[0].text == "رزولوشن":
                    resolution = td_tr[1].text
                elif td_tr[0].text == "پردازنده مرکزی":
                    cpu = td_tr[1].text
                elif td_tr[0].text == "حافظه‌ی رم":
                    ram = td_tr[1].text
                elif td_tr[0].text == "نوع حافظه‌ی رم":
                    ram_type = td_tr[1].text
                elif td_tr[0].text == "حافظه‌ی ذخیره‌سازی":
                    storage = td_tr[1].text
                elif td_tr[0].text == "نوع حافظه‌ی ذخیره‌سازی":
                    storage_type = td_tr[1].text
                elif td_tr[0].text == "پردازنده‌ گرافیکی مجزا":
                    gpu = td_tr[1].text
                elif td_tr[0].text == "حافظه‌ی اختصاصی پردازنده‌ی گرافیکی":
                    gpu_ram = td_tr[1].text
                elif td_tr[0].text == "ابعاد":
                    size = td_tr[1].text
                elif td_tr[0].text == "وزن":
                    weight = td_tr[1].text
                elif td_tr[0].text == "حجم باتری":
                    battery_life = td_tr[1].text
        
    
        score_tag = laptop_page.find('span' , attrs={'class' : 'percent fa-num'})
        if score_tag is not None:
            score = score_tag.text
        else:
            score = ""
        
        price_tag = laptop_page.find('a' , attrs={'class' : 'summary-product--price fa-num hidden-xs hidden-sm'}).find('span')
        if price_tag is not None:
            price = price_tag.find('span').text
        else:
            price = ""
        
        if len(self.zoomit) == 100:
            self.flag_laptop += 100
            print(self.flag_laptop)
            self.save_all_csv('zoomit')
            self.zoomit = pd.DataFrame(columns=['url', 'Title', 'Manufacturer', 'Model_Name', 'Screen_Size', 'Resolution', 'CPU', 'RAM', 'RAM_type', 'Storage', 'Storage_type', 'GPU', 'GPU_RAM', 'Size', 'Weight', 'Score', 'Battery_life', 'Price'])
        
        self.zoomit.loc[len(self.zoomit)] = [
            url, 
            title, 
            manufacturer, 
            model, 
            screen_size, 
            resolution, 
            cpu, 
            ram, 
            ram_type, 
            storage, 
            storage_type, 
            gpu, 
            gpu_ram, 
            size, 
            weight, 
            score,
            battery_life, 
            price
            ]
         
if __name__ == '__main__':
    crawler = ShopCrawler()
    crawler.start_crawling()
