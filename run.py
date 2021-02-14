# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import transmissionrpc
import time
import yaml
import re

import strategy


diskSize = 150 #GB

history = []
state = []
freeSize = diskSize  


class Seed:
    """
    seedType:
        free_bg:     免费
        twoup_bg:    双倍上传
        halfdown_bg: 50%下载
        d30down_bg:  30%下载
        d70down_bg:  70%下载
        空:           一般种子
    """
    def __init__(self, name):
        self.name = name
        self.seedId = 0
        self.seedType = 0
        self.comments = 0
        self.livetime = 0
        self.size = 0
        self.upload = 0
        self.download = 0
        self.complete = 0

    def __init__(self, name, seedId, seedType, comments, livetime, size, upload, download, complete):
        self.name = name
        self.seedId = seedId
        self.seedType = seedType
        self.comments = comments
        self.livetime = livetime
        self.size = size
        self.upload = upload
        self.download = download
        self.complete = complete

#=========================================================
def defaultInput(name, default):
    res = input(f"{name}[{default}]: ")
    if res == '':
        return default
    return res

class AutoPT:
    def __init__(self):
        self.initConfig()
        self.initTransmission()
        self.initBrowser()
        self.login()

    def initConfig(self):
        def loadConfig():
            with open(os.path.join(os.getcwd(), 'config.yaml'), 'rb') as f:
                settings = yaml.load(f, Loader=yaml.Loader)
            self.downloadPath = settings['path']['downloadPath']
            self.torrentDownloadPath = settings['path']['torrentDownloadPath']
            self.username = settings['login']['username']
            self.password = settings['login']['password']
            self.mode = settings['mode']
            self.downloadWaitTime = settings['downloadWaitTime']
            self.searchCycle = settings['searchCycle']
        if os.path.exists(os.path.join(os.getcwd(), 'config.yaml')):
            loadConfig()
        else:
            settings = {}
            settings['mode'] = defaultInput('mode', 'test')
            settings['downloadWaitTime'] = int(defaultInput('downloadWaitTime', 60))
            settings['searchCycle'] = int(defaultInput('searchCycle', 600))
            settings['login'] = {}
            settings['login']['username'] = defaultInput('username', 'xxxxxxx')
            settings['login']['password'] = defaultInput('password', 'xxxxxxx')
            settings['path'] = {}
            settings['path']['downloadPath'] = defaultInput("downloadPath", os.path.join(os.getcwd(), 'download'))
            settings['path']['torrentDownloadPath'] = defaultInput("torrentDownloadPath", os.path.join(os.getcwd(), 'torrent'))
            with open(os.path.join(os.getcwd(), 'config.yaml'), 'w') as f:
                f.write(yaml.dump(settings))
            loadConfig()
        if not os.path.exists(self.downloadPath):
            os.makedirs(self.downloadPath)
        if not os.path.exists(self.torrentDownloadPath):
            os.makedirs(self.torrentDownloadPath)

    def initBrowser(self):
        self.seedIdPattern = re.compile(r"id\=(\d+)")
        req_url = "https://pt.sjtu.edu.cn"
        chrome_options = Options()
        if self.mode != 'test':
            chrome_options.add_argument('--headless')
        prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory':  self.torrentDownloadPath}
        chrome_options.add_experimental_option('prefs', prefs)
        self.browser = webdriver.Chrome(options=chrome_options)
        self.browser.get(req_url)

    def initTransmission(self):
        self.tc = transmissionrpc.Client(address='127.0.0.1', port=9091)

    def login(self):
        usernameInput = self.browser.find_element_by_name("username")
        usernameInput.send_keys(self.username)
        passwordInput = self.browser.find_element_by_name("password")
        passwordInput.send_keys(self.password)
        try:
            self.browser.find_element_by_xpath("/html/body/table[2]/tbody/tr/td/form/span/span/img")
            checkcodeInput = self.browser.find_element_by_name("checkcode")
            checkcode = input("checkcode: ")
            checkcodeInput.send_keys(checkcode)
        except:
            pass
        self.browser.find_element_by_xpath("//input[@value='登录']").click()

    def parseSeedByURL(self, URL):
        self.browser.get(URL)
        seeds = []
        for i in range(50):
            seedRow = self.browser.find_element_by_xpath(f"/html/body/table[3]/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[{i+2}]")
            seedType = seedRow.get_attribute('class')
            title = seedRow.find_element_by_xpath("./td[2]/table/tbody/tr/td[1]/a").get_attribute('title')
            seedIdURL = seedRow.find_element_by_xpath("./td[2]/table/tbody/tr/td[1]/a").get_attribute('href')
            seedId = int(self.seedIdPattern.findall(seedIdURL)[0])
            comments = seedRow.find_element_by_xpath("./td[3]").text
            livetime = seedRow.find_element_by_xpath("./td[4]").text.split('\n')    
            size = seedRow.find_element_by_xpath("./td[5]").text.split('\n')
            up = seedRow.find_element_by_xpath("./td[6]").text
            down = seedRow.find_element_by_xpath("./td[7]").text
            complete = seedRow.find_element_by_xpath("./td[8]").text
            seeds.append(Seed(title, seedId, seedType, comments, livetime, size, up, down, comments))
            # print(f"{title} {seedId} {seedType} {comments} {livetime} {size} {up} {down} {complete}")
        return seeds

    def downloadSeedById(self, id):
        seed_url = f"https://pt.sjtu.edu.cn/download.php?id={id}"
        self.browser.get(seed_url)
        time.sleep(5)
        for _ in range(self.downloadWaitTime):
            time.sleep(1)
            ls = os.listdir(self.torrentDownloadPath)
            for l in ls:
                if f"[{id}]" in l:
                    return os.path.join(self.torrentDownloadPath, l)
        return False

    def loop(self):
        #TODO
        while True:
            seedURL = "https://pt.sjtu.edu.cn/torrents.php"
            seeds = self.parseSeedByURL(seedURL)
            for seed in seeds:
                for fun in strategy.strategyPriorityQueue:
                    res = fun(seed, self)
                    if res == strategy.DOWNLOAD:
                        filename = self.downloadSeedById(seed.seedId)
                        if filename:
                            self.tc.add_torrent(torrent = f"file://{filename}", download_dir = os.path.join(self.downloadPath, seed.name))
                    elif res == strategy.NODOWN:
                        break
                    elif res == strategy.PADDING:
                        pass
                    else:
                        pass
            time.sleep(self.searchCycle)

    def quit(self):
        self.browser.close()
        self.browser.quit()


# =========================================

if __name__ == '__main__':
    autopt = AutoPT()
    autopt.loop()

"""
    recordHistory(browser)
    while True:
        try:
            browser.refresh()
            sourceList = browser.find_elements_by_class_name('free_bg')
            for source in sourceList:
                sourceName = source.find_element_by_xpath( "./td[2]/table/tbody/tr/td[1]/a").get_attribute('title')
                if sourceName not in history:
                    #判定空间           
                    tmpSeed = Seed(sourceName)
                    size =  source.find_element_by_xpath( "./td[5]").text.split('\n')
                    print(size)
                    if size[1] == 'GB':
                        tmpSeed.size = float(size[0]) 
                    if size[1] == 'MB':
                        tmpSeed.size = float(size[0]) / 1000    
                    history.append(sourceName)
                    if(tmpSeed.size > diskSize):
                        continue  #放不下
                    FIFO(tmpSeed)

                    #开始下载种子
                    print('Download \n', sourceName)
                    source.find_element_by_xpath( "./td[2]/table/tbody/tr/td[3]/a[1]").click()
                    cwd = os.getcwd()
                    latestFile = getLatestFileName(downloadWaitTime, torrentDownloadPath)  #wait time
                    
        except Exception as e:
            print('Error:', e)
        time.sleep(searchCycle)
"""