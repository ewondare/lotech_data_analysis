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

class ShopCrawler:
    def __init__(self):
        self.baseURL = 'https://www.technolife.ir'
        self.website = 'technolife'
        self.data_path = './Data'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36', 
            'accept-language': 'en-US'
        }
        self.dataframe_names = ['technolife_laptops_url', 'technolife']
        self.technolife_laptops_url = pd.DataFrame(columns=['url'])
        self.technolife = pd.DataFrame(columns=['url', 'Title', 'Manufacturer', 'Model_Name', 'Category', 'Screen_Size', 'Screen', 'CPU', 'RAM', 'HDD', 'SSD', 'GPU', 'OS', 'OS_Version', 'Weight', 'Price', 'Available', 'Score', 'Quantity', 'Number_of_sellers', 'Discount'])
        self.flag_laptop = 0
        
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
        page_url = self.baseURL + '/product/list/164_163_130/تمامی-کامپیوترها-و-لپ-تاپ-ها?page='+ str(page)
        pagination_req_failed_count = 0
        while pagination_req_failed_count < 3:
            try:
                response = requests.get(page_url, headers=self.headers)
                if response.status_code != 200:
                    raise Exception(f"status code is: {response.status_code}")
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                laptops = soup.find_all('div' , attrs={'class' : 'relative w-full rounded-[10px] border bg-white pt-[52px] shadow-[0px_1px_4px_rgba(0,0,0,0.08)] xl:max-w-[32%] 2xl:w-[24%] 3xl:w-[19.2%]'})
                for laptop in laptops:
                    laptop_url = laptop.find('a')['href']
                    new_laptop_url.loc[len(new_laptop_url)] = [laptop_url]
                return new_laptop_url
                
            except Exception as e:
                pagination_req_failed_count += 1
                print(e)

    def crawl_pagination(self):
        print("get_all_books_url started")
        
        url = self.baseURL + '/product/list/164_163_130/تمامی-کامپیوترها-و-لپ-تاپ-ها?page=1'
        req_failed_count = 0

        while req_failed_count < 3:
            try:
                response = requests.get(url, headers=self.headers)
                if response.status_code != 200:
                    raise Exception(f"status code is: {response.status_code}")

                soup = BeautifulSoup(response.content, 'html.parser')
                
                pagination_count = int(soup.find('div' , attrs={'class' : 'mx-6 flex items-center justify-center xl:mx-8'}).find_all('a')[-1].text)

                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = (executor.submit(self.scrap_every_page, page) for page in range(1, pagination_count+1))
                    for future in as_completed(futures):
                        new_laptop_url = future.result()   

                        if new_laptop_url is not None:
                            for i in range(len(new_laptop_url)):
                                self.technolife_laptops_url.loc[len(self.technolife_laptops_url)] = [new_laptop_url['url'][i]]
                            print(len(self.technolife_laptops_url))
                            self.save_csv('technolife_laptops_url')
                        
                break

            except Exception as e:
                req_failed_count += 1
                print(e)

        print("get_all_books_url finished")
    
    def scrap_every_laptop_page(self, url):
        page_url = self.baseURL + url
        pagination_req_failed_count = 0

        while pagination_req_failed_count < 3:
            try:
                response = requests.get(page_url, headers=self.headers)
                if response.status_code != 200:
                    raise Exception(f"status code is: {response.status_code}")
                
                laptop_page = BeautifulSoup(response.content, 'html.parser')

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
                for i in range(len(self.technolife_laptops_url)):
                    new_url[self.technolife_laptops_url.iloc[i]['url']] = self.technolife_laptops_url.iloc[i]['url']
                
                for i in range(len(self.technolife)):
                    if self.technolife.iloc[i]['url'] in new_url:
                        new_url.pop(self.technolife.iloc[i]['url'])

                self.flag_laptop += len(self.technolife)
                
                
                self.technolife = pd.DataFrame(columns=['url', 'Title', 'Manufacturer', 'Model_Name', 'Category', 'Screen_Size', 'Screen', 'CPU', 'RAM', 'HDD', 'SSD', 'GPU', 'OS', 'OS_Version', 'Weight', 'Price', 'Available', 'Score', 'Quantity', 'Number_of_sellers', 'Discount'])



                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = (executor.submit(self.scrap_every_laptop_page, url) for url in new_url.values())
                                           
                    for future in as_completed(futures):
                        url, laptop_page = future.result()   
                        self.crawl_laptop_page_all(url, laptop_page)
                
                break

            except Exception as e:
                req_failed_count += 1
                print("2:",e)
                
        if len(self.technolife) > 0:
            self.flag_laptop += len(self.technolife)
            print(self.flag_laptop) 
            self.save_all_csv('technolife')

        print("get_all_books_pages finished")
        
    def crawl_laptop_page_all(self, url, laptop_page):
        title_tag = laptop_page.find('strong' , attrs={'class' : 'left-8 line-clamp-2 !text-lg font-semiBold !leading-[32px] text-gray-800'})
        if title_tag is not None:
            title = title_tag.text
        else:
            title = ""
        if "Dell" in title or "dell" in title or " دل " in title: 
           Manufacturer = "Dell" 
        elif "Lenovo" in title or "lenovo" in title or " لنوو " in title: 
           Manufacturer = "Lenovo" 
        elif "Acer" in title or "acer" in title or " ایسر " in title: 
           Manufacturer = "Acer" 
        elif "HP" in title or "hP" in title or " اچ پی " in title: 
           Manufacturer = "HP" 
        elif "Fujitsu" in title or "fujitsu" in title or " فوجیتسو " in title: 
           Manufacturer = "Fujitsu"
        elif "Asus" in title or "asus" in title or " ایسوس " in title: 
           Manufacturer = "Asus"
        elif "MSI" in title or "msi" in title or " ام اس آی " in title: 
           Manufacturer = "MSI"
        elif "Toshiba" in title or "toshiba" in title or " توشیبا " in title: 
           Manufacturer = "Toshiba"
        elif "Apple" in title or "apple" in title or " اپل " in title: 
           Manufacturer = "Apple"
        elif "Samsung" in title or "samsung" in title or " سامسونگ " in title: 
           Manufacturer = "Samsung" 
        elif "Huawei" in title or "huawei" in title or " هوآوی " in title: 
           Manufacturer = "Huawei" 
        elif "Microsoft" in title or "microsoft" in title or " ماکروسافت " in title: 
           Manufacturer = "Microsoft" 
        elif "Xiaomi" in title or "xiaomi" in title or " شیائومی " in title: 
           Manufacturer = "Xiaomi" 
        elif "Razer" in title or "razer" in title or " ریزر " in title: 
           Manufacturer = "Razer" 
        elif "Mediacom" in title or "mediacom" in title or " مدیاکام " in title: 
           Manufacturer = "Mediacom" 
        elif "Chuwi" in title or "chuwi" in title or " چووی " in title: 
           Manufacturer = "Chuwi" 
        elif "Google" in title or "google" in title or " گوگل " in title: 
           Manufacturer = "Google" 
        elif "LG" in title or "lg" in title or " ال جی " in title: 
           Manufacturer = "LG" 
        elif "Vero" in title or "vero" in title or " ورو " in title: 
           Manufacturer = "Vero" 
        else:
           Manufacturer = ""
           
        technical_specifications = laptop_page.find_all('div' , attrs={'class' : 'flex w-full flex-col rounded-[10px] bg-background-100 p-[12px] !pl-6 lg:rounded-[14px] lg:p-4 lg:px-6'})
        category = ""
        screen_Size = ""
        screen = "" 
        cpu = "" 
        ram = "" 
        hdd = ""
        ssd = ""
        gpu = "" 
        weight = ""
        for technical in technical_specifications:
            technical_p = technical.find_all('p')
            if technical_p[0].text == "سری لپ تاپ :":
                category = technical_p[1].text
            elif technical_p[0].text == "ابعاد نمایشگر :":
                screen_Size = technical_p[1].text
            elif technical_p[0].text == "وضوح تصویر :":
                screen = technical_p[1].text
            elif technical_p[0].text == "مدل پردازنده مرکزی :":
                cpu = technical_p[1].text
            elif technical_p[0].text == "ظرفیت حافظه RAM :":
                ram = technical_p[1].text
            elif technical_p[0].text == "ظرفیت حافظه HDD :":
                hdd = technical_p[1].text
            elif technical_p[0].text == "ظرفیت حافظه SSD :":
                ssd = technical_p[1].text
            elif technical_p[0].text == "سازنده پردازنده گرافیکی :":
                gpu = technical_p[1].text
            elif technical_p[0].text == "وزن :":
                weight = technical_p[1].text

        price_div = laptop_page.find('div' , attrs={'class' : 'flex max-w-max flex-col items-end'}) 
        if price_div is not None:  
            discount_p = price_div.find('p', attrs={'class' : 'mb-4 h-6 rounded-full bg-red-600 px-3 pb-[1px] pt-0.5 text-[15px] font-semiBold !leading-5 text-white xl:pt-[3px] xl:text-lg'})
            if discount_p is not None:
                discount = discount_p.text
            else:
                discount = ""
            price_div_p = price_div.find('div', attrs={'class' : 'flex items-center'}) 
            price_p = price_div_p.find_all('p')
            if len(price_p) == 2:
                price = price_p[1].text
            elif len(price_p) == 1:
                price = price_p[0].text
            else:
                price = ""
            
            Available = 1
        else:
            Available = 0
            discount = ""
            price = ""
            
        Number_of_sellers = ""
        user_opinion = laptop_page.find_all('p' , attrs={'class' : 'mx-2 text-xs font-semiBold text-green-800'})
        if user_opinion is not None:
            sum_rate = 0 
            for opinion in user_opinion:
                temp = re.findall(r'\d+', opinion.text)
                res = list(map(int, temp))
                sum_rate = sum_rate + int(res[0])
            if(len(user_opinion) != 0):
                score = sum_rate / len(user_opinion)
            else:
                score = ""                
        else:
            score = ""

        Model_Name = ""
        os = ""
        os_version = ""
        Quantity = ""
        
        if len(self.technolife) == 100:
            self.flag_laptop += 100
            print(self.flag_laptop)
            self.save_all_csv('technolife')
            self.technolife = pd.DataFrame(columns=['url', 'Title', 'Manufacturer', 'Model_Name', 'Category', 'Screen_Size', 'Screen', 'CPU', 'RAM', 'HDD', 'SSD', 'GPU', 'OS', 'OS_Version', 'Weight', 'Price', 'Available', 'Score', 'Quantity', 'Number_of_sellers', 'Discount'])
        print(url)
        self.technolife.loc[len(self.technolife)] = [
            url, 
            title, 
            Manufacturer, 
            Model_Name, 
            category, 
            screen_Size, 
            screen, 
            cpu, 
            ram, 
            hdd, 
            ssd, 
            gpu, 
            os, 
            os_version, 
            weight, 
            price, 
            Available,
            score, 
            Quantity, 
            Number_of_sellers, 
            discount
            ]
        
             
         
if __name__ == '__main__':
    crawler = ShopCrawler()
    crawler.start_crawling()
