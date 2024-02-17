import valuation as val
import assets_list as assets

if __name__ == '__main__':
    stocks_list = assets.stocks_list
    fiis_list = assets.fiis_list
    if fiis_list:
        val.fiis(fiis_list).info()
    if stocks_list:
        val.stocks(stocks_list).info()