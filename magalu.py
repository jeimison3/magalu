from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

import re
import urllib.parse

import traceback

import csv


import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders



import time

def limpar(inp):
    return (" ".join(str(inp).replace(","," ").splitlines())).strip()

def parsing(tag, cep, ignore_list):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--window-size=1400x1080")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(executable_path="chromedriver.exe", options=chrome_options)
    try:
        driver.get("https://www.magazineluiza.com.br/busca/%s/?itens=200" % (urllib.parse.quote(str(tag))) )
        #time.sleep(10)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'product')))

        #buscar = driver.find_element_by_id("inpHeaderSearch").send_keys(testando)

        #driver.find_element_by_id("inpHeaderSearch").send_keys(Keys.ENTER)
        #paginacao = driver.current_url
        #varios = (paginacao + "?")
        #driver.get(varios)
        all_products = driver.find_elements_by_class_name("product-li")
        produtos = []


        if all_products:
            for i in all_products:
                if i.get_attribute('href') not in ignore_list:
                    produtos.append(i.get_attribute('href'))
            print("Lista preparada. Testando valores.")
            for idx, acesso in enumerate(produtos):
                driver.get(acesso) # Acessa

                delay = 5 # seconds
                try:
                    myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'input__zipcode')))
                    try:
                        myElem.send_keys(cep)
                        myElem.send_keys(Keys.ENTER) # Testa frete
                    except Exception as e:
                        pass
                    print("=> %d de %d: OK" % (idx+1, len(produtos)))
                        
                    

                    myTable = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'freight-product__table')))
                    all_fretes = driver.find_elements_by_class_name("freight-product__box-info")
                    fretes = []
                    
                    if all_fretes:
                        for i in all_fretes:
                            titulo_frete = ""
                            valor_frete = ""
                            prazo_frete = ""
                            indisponivel = False
                            
                            for j in i.find_elements_by_xpath(".//span[@class='freight-product__box-item-delivery-type-text']"):
                                titulo_frete = j.text
                            
                            for j in i.find_elements_by_xpath(".//span[@class='freight-product__box-item-delivery-days-text']"):
                                prazo_frete = j.text
                            
                            for j in i.find_elements_by_xpath(".//span[@class='freight-product__freight-text-price']"):
                                valor_frete = j.text

                            for j in i.find_elements_by_xpath(".//span[@class='freight-product__box-item-unavailable']"):
                                indisponivel = True

                            if valor_frete == "":
                                for j in i.find_elements_by_xpath(".//span[@class='js-freight-price']"):
                                    valor_frete = j.text
                            
                            fretes.append( [titulo_frete, prazo_frete, valor_frete, indisponivel] )
                            
                    
                    
                    titulo = driver.find_elements_by_xpath("//h1[@class='header-product__title']")
                    for i in titulo:
                        titu_product = (i.text)

                    for bold in driver.find_elements_by_xpath("//span[@class='price-template__text']"):
                        moeda = (bold.text)

                    for price in driver.find_elements_by_xpath("//span[@class='price-template__text']"):
                        uniq = float(re.findall( r"[-+]?\d*\.\d+|\d+", str(price.text).replace(",",".") )[0] )

                        with open('links.csv', 'a', encoding="utf-8") as arquivo:
                            if len(fretes):
                                for f in fretes:
                                    if not f[3]: # Não indisponível
                                        #print("f=",f)
                                        valor = 0.0 if (f[0] == "Retirar na loja" or f[2] == "Frete grátis") else float(re.findall( r"[-+]?\d*\.\d+|\d+", str(f[2]).replace(",",".") )[0] )
                                        moeda = "R$"
                                        if valor > 0:
                                            moeda = str(f[2]).split(" ")[0]
                                        arquivo.writelines("{},{},{},{},{},{},{},{}\n".format(acesso, limpar(titu_product), limpar(moeda), limpar(uniq), limpar(f[0]), limpar(f[1]), limpar(moeda), valor))
                            else:
                                arquivo.writelines("{},{},{},{},,,,\n".format(acesso, limpar(titu_product), limpar(moeda), limpar(uniq)))
                            #arquivo.writelines("Produto: {} Valor:{} Link:{} Fretes: {} \n".format(titu_product, uniq, acesso, fretes))

                except Exception as e:
                    traceback.print_exc()
                    #print("Pulando item. Problema identificado (TIMEOUT/SEM CEP).")
                    print("Problema em: %s" % (acesso))
                    print("=> %d de %d: FAIL -> TIMEOUT/CRASH" % (idx+1, len(produtos)))

        else:
            print("Nada foi encontrado :(")
    except SystemError:
        print("OPS, houve algum erro na busca !")


def get_acessados():
    links = []
    try:
        with open('links.csv', encoding="utf-8") as csvfile:
            spamreader = csv.reader(csvfile)
            for row in spamreader:
                links.append(row[0])
    except IOError:
        pass
    return links

def menu():
    print('''
    
 |  \/  |   __ _    __ _    __ _  | |  _   _ 
 | |\/| |  / _` |  / _` |  / _` | | | | | | |
 | |  | | | (_| | | (_| | | (_| | | | | |_| |
 |_|  |_|  \__,_|  \__, | t \__,_| |_|  \__,_|
                   |___/             1.1 beta
    edit by jeimison3
                   
    ''')




menu()
conhecidos = get_acessados()
item = input("Qual produto deseja buscar?: ")
cep = input("Qual CEP usar?: ")
parsing(item, cep, conhecidos)
