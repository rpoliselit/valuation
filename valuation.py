import pandas as pd
import math
import requests
from bs4 import BeautifulSoup

soup = None
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

def request_data(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

def request_from_fundamentus(asset = None):
    url = 'https://www.fundamentus.com.br/detalhes.php?papel=' + asset
    return request_data(url)

def extract_index(index, soup, tag1 = 'td', tag2 = 'td'):
    html_tag = soup.select_one(f'{tag1}:-soup-contains("{index}")')
    if html_tag:
        num_text = html_tag.find_next(tag2).text
        if '-' in num_text:
            return None
        num_float = float(num_text.replace(',', '.').strip('%'))
    return round(num_float, 2)

class stocks:

    def __init__(self, assets = None):
        self.assets = assets
        self.indexes = {'Cotação', 'Div. Yield' ,'P/L', 'P/VP', 'VPA', 'LPA'}
        self.data = {'Ações' : [], 'Preço Justo (Graham)' : [], 'Preço Justo (IBOVESPA)' : []}
        self.df = None

    def ibovespa_statusinvest(self, show = False):
        url = 'https://statusinvest.com.br/indices/ibovespa'
        indexes = {'P/L' : None, 'P/VP': None}
        soup = request_data(url)
        for index in indexes:
            indexes[index] = extract_index(index, soup, tag1 = 'h3', tag2 = 'strong')
        if show:
            print("| IBOVESPA | P/L = ", indexes['P/L'], ' | P/VP = ', indexes['P/VP'], ' |')
        return indexes['P/L'] * indexes['P/VP']

    def intrinsic_value(self, LPA, VPA, BG = 22.5):
        # PL == PE = 15.0
        # PVP == price to book value = 1.5
        # VPA == book value
        # LPA == EPS
        # BG = PL * PVP
        price = math.sqrt(BG * LPA * VPA)
        return round(price, 2)

    def make_dataframe(self):
        LPA = None
        VPA = None
        IBOV = self.ibovespa_statusinvest(show=True)
        for asset in self.assets:
            self.data['Ações'].append(asset)
            resp = request_from_fundamentus(asset)
            for index in self.indexes:
                index_value = extract_index(index,resp)
                if index not in self.data:
                    self.data[index] = []
                self.data[index].append(index_value)
                LPA = index_value if index == 'LPA' else LPA
                VPA = index_value if index == 'VPA' else VPA
            self.data['Preço Justo (Graham)'].append(self.intrinsic_value(LPA, VPA))
            self.data['Preço Justo (IBOVESPA)'].append(self.intrinsic_value(LPA, VPA, BG = IBOV))
        self.df = pd.DataFrame(data=self.data)


    def info(self):
        self.make_dataframe()
        print('----------------------------------------------------------------------------')
        print(self.df)
        print('----------------------------------------------------------------------------')

class fiis:

    def __init__(self, assets = None):
        #ASSETS LIST
        self.assets = assets
        self.indexes = {'Cotação', 'Div. Yield', 'P/VP', 'VP/Cota', 'Qtd imóveis', 'Vacância Média'}
        self.data = {'FIIs': []}
        self.df = None

    def make_dataframe(self):
        for asset in self.assets:
            self.data['FIIs'].append(asset)
            resp = request_from_fundamentus(asset)
            for index in self.indexes:
                if index in self.data:
                    self.data[index].append(extract_index(index,resp))
                else:
                    self.data[index] = [extract_index(index,resp)]
        self.df = pd.DataFrame(data=self.data)
    
    def info(self):
        self.make_dataframe()
        print('----------------------------------------------------------------------------')
        print(self.df)
        print('----------------------------------------------------------------------------')