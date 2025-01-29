import datetime
import pandas as pd
import math
import requests
from bs4 import BeautifulSoup

soup = None
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

def create_timestamp():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d")

def request_data(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

def request_from_fundamentus(asset = None):
    url = 'https://www.fundamentus.com.br/detalhes.php?papel=' + asset
    return request_data(url)

def extract_index(index, soup, tag1 = 'td', tag2 = 'td', text = False):
    html_tag = soup.select_one(f'{tag1}:-soup-contains("{index}")')
    if html_tag:
        num_text = html_tag.find_next(tag2).text
        if text:
            return num_text
        if '-' in num_text:
            return None
        num_float = float(num_text.replace(',', '.').strip('%'))
    return round(num_float, 2)

class stocks:

    def __init__(self, assets = None):
        self.assets = assets
        self.indexes = {'Cotação', 'Div. Yield' ,'P/L', 'P/VP', 'VPA', 'LPA'}
        self.data = {'Ações' : [], 'Preço Justo (Graham)' : [], 'Preço Justo (IBOVESPA)' : [], 'Preço Justo (IBRX)' : [], 'Preço Justo (IDIV)' : []}
        self.df = None
        self.ibov_pl = None
        self.ibov_pvp = None
        self.ibrx_pl = None
        self.ibrx_pvp = None
        self.idiv_pl = None
        self.idiv_pvp = None
        self.timestamp = create_timestamp()

    def ibovespa_statusinvest(self, show = False):
        url = 'https://statusinvest.com.br/indices/ibovespa'
        indexes = {'P/L' : None, 'P/VP': None}
        soup = request_data(url)
        for index in indexes:
            indexes[index] = extract_index(index, soup, tag1 = 'h3', tag2 = 'strong')
        if show:
            self.ibov_pl = indexes['P/L']
            self.ibov_pvp = indexes['P/VP']
            print(f"|  IBOVESPA  | P/L =  {indexes['P/L']:5.2f}  | P/VP =  {indexes['P/VP']:4.2f}  |")
        return indexes['P/L'] * indexes['P/VP']

    def ibrx_statusinvest(self, show = False):
        url = 'https://statusinvest.com.br/indices/indice-brasil-100'
        indexes = {'P/L' : None, 'P/VP': None}
        soup = request_data(url)
        for index in indexes:
            indexes[index] = extract_index(index, soup, tag1 = 'h3', tag2 = 'strong')
        if show:
            self.ibrx_pl = indexes['P/L']
            self.ibrx_pvp = indexes['P/VP']
            print(f"| BRASIL 100 | P/L =  {indexes['P/L']:5.2f}  | P/VP =  {indexes['P/VP']:4.2f}  |")
        return indexes['P/L'] * indexes['P/VP']

    def idiv_statusinvest(self, show = False):
        url = 'https://statusinvest.com.br/indices/indice-dividendos'
        indexes = {'P/L' : None, 'P/VP': None}
        soup = request_data(url)
        for index in indexes:
            indexes[index] = extract_index(index, soup, tag1 = 'h3', tag2 = 'strong')
        if show:
            self.idiv_pl = indexes['P/L']
            self.idiv_pvp = indexes['P/VP']
            print(f"| DIVIDENDOS | P/L =  {indexes['P/L']:5.2f}  | P/VP =  {indexes['P/VP']:4.2f}  |")
        return indexes['P/L'] * indexes['P/VP']

    def intrinsic_value(self, LPA, VPA, BG = 22.5):
        # PL == PE = 15.0
        # PVP == price to book value = 1.5
        # VPA == book value
        # LPA == EPS
        # BG = PL * PVP = 22.5
        price = math.sqrt(BG * LPA * VPA)
        return round(price, 2)

    def make_dataframe(self):
        LPA = None
        VPA = None
        IBOV = self.ibovespa_statusinvest(show=True)
        IBRX = self.ibrx_statusinvest(show=True)
        IDIV = self.idiv_statusinvest(show=True)
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
            self.data['Preço Justo (IBRX)'].append(self.intrinsic_value(LPA, VPA, BG = IBRX))
            self.data['Preço Justo (IDIV)'].append(self.intrinsic_value(LPA, VPA, BG = IDIV))
        self.df = pd.DataFrame(data=self.data)

    def info(self):
        self.make_dataframe()
        self.df.to_excel(f'spreedsheets/Stocks_{self.timestamp}.xlsx', index = False)
        print('----------------------------------------------------------------------------')
        print(self.df)
        print('----------------------------------------------------------------------------')

class fiis:

    def __init__(self, assets = None):
        # ASSETS LIST
        self.assets = assets
        self.indexes = {'Cotação', 'Div. Yield', 'P/VP', 'VP/Cota', 'Qtd imóveis', 'Vacância Média'}
        self.data = {'FIIs': [], 'Liq. Méd. Diária': []}
        self.df = None
        self.timestamp = create_timestamp()

    def liquidity_statusinvest(self, asset = None):
        # daily liquidity
        url = 'https://statusinvest.com.br/fundos-imobiliarios/' + asset
        soup = request_data(url)
        data = extract_index('Liquidez média diária', soup, tag1 = 'span', tag2 = 'strong', text = True)
        return data

    def make_dataframe(self):
        for asset in self.assets:
            self.data['FIIs'].append(asset)
            resp = request_from_fundamentus(asset)
            for index in self.indexes:
                if index in self.data:
                    self.data[index].append(extract_index(index,resp))
                else:
                    self.data[index] = [extract_index(index,resp)]
            self.data['Liq. Méd. Diária'].append(self.liquidity_statusinvest(asset))
        self.df = pd.DataFrame(data=self.data)
    
    def info(self):
        self.make_dataframe()
        self.df.to_excel(f'spreedsheets/FIIs_{self.timestamp}.xlsx', index = False)
        print('----------------------------------------------------------------------------')
        print(self.df)
        print('----------------------------------------------------------------------------')
