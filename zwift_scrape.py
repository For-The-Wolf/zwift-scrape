from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from argparse import ArgumentParser
import numpy as np
from os import path,listdir,mkdir
import pandas as pd
import sys
import re

def zwift_scrape(urlpage,headless = False):
    opts = Options()
    if headless:
        opts.headless = True
    print('Scraping data from: {}.'.format(urlpage))
    finishData =[]

    platform = sys.platform
    driverPath = './drivers/geckodriver-{}'.format(platform)
    if platform == 'win32':
        driverPath += '.exe'
    with webdriver.Firefox(executable_path=driverPath,service_log_path = './drivers/logs/geckodriver-{}_log.log'.format(platform), options = opts) as driver:
        driver.implicitly_wait(10)
        driver.get(urlpage)
        raceName = driver.find_element(By.XPATH, "//*[@id=\"header_details\"]/div[1]/h3").text
        raceName = re.sub(r'[^A-Za-z0-9 ]+', '', raceName)
        print('Downloading data for {}'.format(raceName))
        pages = driver.find_elements(By.XPATH,"//*[@id=\"table_event_results_final_paginate\"]/ul/li")[1:-1]
        nPages = len(pages)
        results = driver.find_element(By.XPATH,"//*[@id=\"table_event_results_final\"]/tbody")
        print('Collecting finish data for all riders...')
        for n in range(2,nPages+2):
            if n >2:
                button = driver.find_element(By.XPATH,"//*[@id=\"table_event_results_final_paginate\"]/ul/li[{}]/a".format(n))
                name1 = results.find_elements(By.TAG_NAME,"tr")[0].find_elements(By.TAG_NAME,"td")[2].text
                driver.execute_script('arguments[0].click();',button)
                while results.find_elements(By.TAG_NAME,"tr")[0].find_elements(By.TAG_NAME,"td")[2].text == name1:
                    results = driver.find_element(By.XPATH,"//*[@id=\"table_event_results_final\"]/tbody")
                    sleep(0.5)
            rows = results.find_elements(By.TAG_NAME, "tr") 
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                category = cols[0].text
                name = toName(cols[2].text) 
                time = finishTime(cols[3].text) 
                finishData += [{'Name':name, 'Category':category, 'Time':time}]
        print('Found {} riders.'.format(len(finishData)))
        toPrimes = driver.find_element(By.XPATH,"//*[@id=\"zp_submenu\"]/ul/li[4]/a")
        toPrimes.click()
        cButtons = driver.find_elements(By.XPATH,"//*[@id=\"table_scroll_overview\"]/div[1]/div[1]/button")
        categoryBottons = [but for but in cButtons if not (but.text=='' or but.text =='All')]
        pButtons = driver.find_elements(By.XPATH,"//*[@id=\"table_scroll_overview\"]/div[1]/div[2]/button")
        primeButtons = [but for but in pButtons if not but.text == '']
        primeResults = driver.find_element(By.XPATH,"//*[@id=\"table_event_primes\"]/tbody")
        while True:
            try:
                testCell = primeResults.find_elements(By.TAG_NAME,"tr")[0].find_elements(By.TAG_NAME,"td")[3].text
            except IndexError:
                sleep(0.5)
            else:
                break
        presults = {}
        primeButtons.reverse()
        for catBut in categoryBottons:
            category = catBut.text
            print('Collecting prime data for category {}...'.format(category))
            presults[category] = {}
            catBut.click()
            for primeBut in primeButtons:
                prime = primeBut.text
                presults[category][prime] = {}
                primeBut.click()
                testCell2 = testCell
                while testCell == testCell2:
                    try:
                        testCell2 = driver.find_element(By.XPATH,"//*[@id=\"table_event_primes\"]/tbody").find_elements(By.TAG_NAME,"tr")[0].find_elements(By.TAG_NAME,"td")[3].text
                    except StaleElementReferenceException:
                        testCell2 = testCell
                    sleep(0.5)

                testCell = testCell2
                primeResults = driver.find_element(By.XPATH,"//*[@id=\"table_event_primes\"]/tbody")
                rows = primeResults.find_elements(By.TAG_NAME,"tr")
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME,"td")
                    lap = cols[0].text
                    splitName = cols[1].text
                    scores = {toName(cols[n].text): primeTime(cols[n+1].text,prime) for n in range(2,len(cols),2) if not cols[n].text == ''}
                    combinedName = '{}_{}'.format(lap,splitName)
                    presults[category][prime][combinedName] = scores
        print('Closing connection to {}'.format(urlpage))
    print('Formatting scraped data...')
    finishResults = formatFinishes(finishData)
    primeResults = formatPrimes(presults)
    print('Done.')
    
    return raceName,finishResults,primeResults



def toName(string):
    #print(string)
    name = string.split('\n')[0]
    #name = re.sub(r'[^A-Za-z0-9 ]+', '', name)
    #name = name.split(' ')[0]+' '+name.split(' ')[1]
    return name

def secsToMS(string):
    flt = float(string)
    return int(flt*1000)

def hrsToMS(string):
    ints = [int(t) for t in string.split(':')]
    ints.reverse()
    time = 0
    for n,t in enumerate(ints):
        time += 1000*t*(60**n)
    return time

def toTime(string):
    if len(string.split('.')) == 1:
        return hrsToMS(string)
    else:
        return secsToMS(string)

def finishTime(string):
    timeStrs = string.split('\n')
    if len(timeStrs) == 1:
        return toTime(timeStrs[0])
    else:
        time = toTime(timeStrs[0])
        if (timeStrs[0].split('.') == 1) and (timeStrs.split('.') < 1): 
            tString = timeStrs[1].split('.')[1]
            tString = tString.replace('s','')
            tString = '0.'+tString
            if float(tString) < 0.5:
                time -= 1000 - secsToMS(tString)
            else:
                time += secsToMS(tString)
        return time

def primeTime(string,prime):
    if prime == 'First over line':
        if string == '':
            return 0
        else:
            string = string.replace('+','')
            string = string.replace('s','')
            return toTime(string)
    else:
        return finishTime(string)

def getFinishPositions(sortP):
    currCat = None
    pos = 1
    positions = []
    for cat in sortP['Category']:
        if currCat != cat:
            currCat = cat
            pos = 1
        positions += [pos]
        pos += 1
    return positions

def getPrimePositions(sortP):
    currDesc = None
    pos = 1
    positions = []
    for _,row in sortP.iterrows():
        desc = '{}_{}_{}'.format(row['Category'],row['Split'],row['Prime'])
        if desc != currDesc:
            currDesc = desc
            pos = 1
        positions += [pos]
        pos += 1
    return positions

def formatFinishes(data):
    categories = list(set([x['Category'] for x in data]))
    toFile = {'Name':[],'Category':[],'Time (ms)':[]}
    for rider in data:
        toFile['Name'] += [rider['Name']]
        toFile['Category'] += [rider['Category']]
        toFile['Time (ms)'] += [rider['Time']]
    fPand =  pd.DataFrame.from_dict(toFile)
    sortedData = fPand.sort_values(by=['Category','Time (ms)'])
    positions = getFinishPositions(sortedData)
    sortedData['Position'] = positions
    return sortedData

def formatPrimes(data):
    keys = ['Category', 'Prime', 'Split', 'Rider', 'Time (ms)']
    columns = [[] for _ in keys]
    for key0, data0 in data.items():
        for key1, data1 in data0.items():
            for key2, data2 in data1.items():
                for name, time in data2.items():
                    for index, value in enumerate((key0, key1, key2, name, time)):
                        columns[index].append(value)
    pPand = pd.DataFrame(dict(zip(keys, columns)))
    sortedData = pPand.sort_values(by=['Category','Split','Prime','Time (ms)'])
    positions = getPrimePositions(sortedData)
    sortedData['Position'] = positions
    return  sortedData

def mkdirAndSave(name,data,filePath):
    if not path.exists(filePath):
        mkdir(filePath)
    savePath = path.join(filePath,name+'.csv')
    data.to_csv(savePath,index=False)



#def exportPrimes(primes):
def main():
    parser = ArgumentParser(description = "Scrape all race time data (finish position and primes)  from a zwiftpower URL")
    parser.add_argument('URL',      help = "URL to scrape ZwiftPower results from.")
    settings = parser.parse_args()
    name, finishes, primes = scrapeZwift(settings.URL)
    name = re.sub(r'[^A-Za-z0-9 ]+', '', name)
    if settings.saveName:
        name = settings.saveName
    savePath = path.join('./',name)
    mkdirAndSave('finishes',finishes,savePath)
    mkdirAndSave('primes',primes,savePath)


if __name__=='__main__':
    main()
    