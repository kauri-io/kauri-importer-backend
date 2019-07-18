from bs4 import BeautifulSoup
from my_parser import parse_post_detail
import configparser

page_url = 'https://medium.com/gitcoin/counterfactual-loan-repayment-828a59d9b730'

config = configparser.RawConfigParser()
config.read('config.ini')
token = config['GATEWAY']['JWT_TOKEN']
content = parse_post_detail(page_url, token)
print(content)
