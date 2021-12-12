import requests
from pandas import DataFrame
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_transactions(wallet, threshold=0):
	transactions =  DataFrame(requests.get("https://api.blockchair.com/bitcoin/dashboards/address/{wallet}?transaction_details=true".format(wallet=wallet)).json()['data'][wallet]['transactions']).set_index('time')
	transactions.balance_change /= 10e7
	return transactions[transactions.balance_change.abs() > threshold]

def get_top_wallets():
	chrome_options = Options()
	chrome_options.add_argument("--headless")
	driver = webdriver.Chrome(options=chrome_options)
	driver.get("https://btc.com/btc/top-address")
	sleep(3)
	rows = driver.find_elements(By.TAG_NAME, "tr")
	top_address = DataFrame(columns=list(map(lambda x: x.text, rows[0].find_elements(By.TAG_NAME, "th"))))
	for row in rows[1:]:
		top_address.loc[len(top_address)] = list(map(lambda x: x.text, row.find_elements(By.TAG_NAME, "td")))
	top_address.set_index('Ranking', inplace=True)
	driver.quit()
	return top_address