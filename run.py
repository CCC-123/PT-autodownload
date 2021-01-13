# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os 
import shutil
import transmissionrpc
import time

#settings
#=========================================================
mode = 'test'
#mode = 'work'
diskSize = 150 #GB


username = ''
password = ''
#TODO:strategy

searchCycle = 3600 #seconds
downloadWaitTime = 30 #seconds


#=========================================================
def getLatestFileName(waitTime, path):
    # method to get the downloaded file name
    time.sleep(waitTime)
    lists = os.listdir(path)	
    lists.sort(key=lambda fn: os.path.getmtime(path+'/' + fn))	
    print 'new file is : ' + lists[-1]	
    return lists[-1]

def FIFO(source):
    while(len(state)):
        if(freeSize > source.size):
            break 
        oldSource = state.pop(0)
        path = os.path.join(downloadPath, oldSource.savepath)
        shutil.rmtree(path) 
        global freeSize
        freeSize += oldSource.size 

    state.append(source)


class Seed:
    def __init__(self, name):
        self.name = name
        self.savepath = name.encode('utf-8')
        self.size = 0
        self.livetime = 0
        self.upload = 0
        self.download = 0


#登录
req_url = "https://pt.sjtu.edu.cn"
chrome_options=Options()
if not mode == 'test':
    chrome_options.add_argument('--headless')
downloadPath = os.path.join(os.getcwd(), 'download')
if not os.path.exists(downloadPath):
    os.makedirs(downloadPath)
prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory':  downloadPath}
chrome_options.add_experimental_option('prefs', prefs)
browser = webdriver.Chrome(chrome_options=chrome_options)
browser.get(req_url)
usernameInput = browser.find_element_by_name("username")
usernameInput.send_keys(username)
passwordInput = browser.find_element_by_name("password")
passwordInput.send_keys(password)
browser.find_element_by_xpath("//input[@value='登录']").click()



#记录首页种子，等待新资源
browser.find_element_by_partial_link_text('种').click()
freeSeedList = browser.find_elements_by_class_name('free_bg')
history = []
state = []
for freeSeed in freeSeedList:
    seedName = freeSeed.find_element_by_xpath( "./td[2]/table/tbody/tr/td[1]/a").get_attribute('title')
    history.append(seedName) 
if mode == 'test':
    history.pop(0)
    print(history)
    
#打开transmission
tc = transmissionrpc.Client(address='127.0.0.1', port=9091)
freeSize = diskSize  

while True:
    sourceList = browser.find_elements_by_class_name('free_bg')
    for source in sourceList:
        sourceName = source.find_element_by_xpath( "./td[2]/table/tbody/tr/td[1]/a").get_attribute('title')
        if sourceName not in history:
            #判定空间           
            tmpSeed = Seed(sourceName)
            size =  freeSeed.find_element_by_xpath( "./td[5]").text.split('\n')[0]
            if size[1] == 'GB':
                tmpSeed.size = float(size[0]) 
            if size[1] == 'MB':
                tmpSeed.size = float(size[0]) / 1000    
            history.append(tmpSeed)
            if(tmpSeed.size > diskSize):
                continue  #放不下
            FIFO(tmpSeed)

            #开始下载种子
            print('Download \n', sourceName)
            source.find_element_by_xpath( "./td[2]/table/tbody/tr/td[3]/a[1]").click()
            cwd = os.getcwd()
            latestFile = getLatestFileName(downloadWaitTime, downloadPath)  #wait time
            tc.add_torrent(torrent = os.path.join(downloadPath, latestFile), download_dir = os.path.join(downloadPath, tmpSeed.savepath))
    time.sleep(searchCycle)

browser.close()
browser.quit()