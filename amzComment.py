# -*- codeing = utf-8 -*-
# @Time : 2020/9/15 23:10
# @Author : Cj
# @File : amzLogin.py
# @Software : PyCharm


from selenium import webdriver
from time import sleep
import configparser,traceback,zipfile,string,multiprocessing,os
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException
from logger import Logger
from fake_useragent import UserAgent
from register import register

all_log = Logger('log/amz_comment_all.log', level='debug')
error_log = Logger('log/amz_comment_error.log', level='error')
# desired_capabilities = DesiredCapabilities.CHROME  # 修改页面加载策略
# desired_capabilities["pageLoadStrategy"] = "none"  # 注释这两行会导致最后输出结果的延迟，即等待页面加载完成再输出

# 打包Google代理插件
def create_proxyauth_extension(proxy_host, proxy_port, proxy_username, proxy_password, scheme='http', plugin_path=None):
    if plugin_path is None:
        # 插件地址
        plugin_path = 'D:/Python/vimm_chrome_proxyauth_plugin2.zip'

    manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

    background_js = string.Template(
        """
        var config = {
                mode: "fixed_servers",
                rules: {
                  singleProxy: {
                    scheme: "${scheme}",
                    host: "${host}",
                    port: parseInt(${port})
                  },
                  bypassList: ["foobar.com"]
                }
              };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "${username}",
                    password: "${password}"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """
    ).substitute(
        host=proxy_host,
        port=proxy_port,
        username=proxy_username,
        password=proxy_password,
        scheme=scheme,
    )
    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_path

def doComment(account):
    options = webdriver.ChromeOptions()
    ua = account['ua']
    if ua == "":
        ua = UserAgent().chrome
    options.add_argument("user-agent=" + ua)
    ip_type = account['ip_type']
    if ip_type == "socks5":
        options.add_argument('--proxy-server=socks5://' + account['ip']+":"+account['port'])
    elif ip_type == "http":
        options.add_argument('--proxy-server=http://' + account['ip']+":"+account['port'])
    else:
        path_config = configparser.RawConfigParser()
        path_config.read("system.ini", encoding="utf-8")
        file_path = path_config['config']['path']+account['ip']+".zip"
        if not os.path.exists(file_path):
            create_proxyauth_extension(
                proxy_host=account['ip'],
                proxy_port=int(account['port']),
                proxy_username=account['account'],
                proxy_password=account['password'],
                plugin_path=file_path
            )
        options.add_extension(file_path)
    # options.add_argument("--start-maximized")
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("log-level=3")
    options.add_argument('blink-settings=imagesEnabled=false')
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(500, 400)
    coo = account['cookies'].replace("false","False").replace("null","None").replace("true","True")
    try:
        driver.get("https://www.baidu.com/")
        for cookie in eval(coo):
            try:
                cookie.pop('sameSite')
            except:
                pass
            driver.add_cookie(cookie_dict=cookie)
        asin_list = account['asin']
        for asin in asin_list.split(","):
            all_log.logger.info("***%s开始留言***"%asin)
            review_url = "https://www.amazon.de/product-reviews/" + asin + "?ie=UTF8&reviewerType=all_reviews"
            driver.get(review_url)
            try:
                while True:
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.ID, 'cm_cr-review_list')))
                    review_div_list = driver.find_elements_by_xpath(
                        '//div[@data-a-expander-name="review_comment_expander"]')
                    for review_div in review_div_list:
                        review_div.find_element_by_xpath('./a').click()
                        sleep(0.5)
                        try:
                            #美国
                            # WebDriverWait(review_div, 8).until(
                            #     EC.visibility_of_element_located(
                            #         (By.XPATH, './/textarea[contains(@placeholder,"Respond to this review")]')))
                            #德国
                            WebDriverWait(review_div, 8).until(
                                EC.visibility_of_element_located(
                                    (By.XPATH, './/textarea[contains(@placeholder,"Antworten Sie auf diese Bewertung")]')))
                        except TimeoutException:
                            #美国
                            # WebDriverWait(review_div, 5).until(
                            #     EC.visibility_of_element_located(
                            #         (By.XPATH, './/span[contains(text(),"Comment")]')))
                            # review_div.find_element_by_xpath('.//span[contains(text(),"Comment")]/..').click()
                            # WebDriverWait(review_div, 5).until(
                            #     EC.visibility_of_element_located(
                            #         (By.XPATH, './/textarea[contains(@placeholder,"Respond to this review")]')))
                            #德国
                            WebDriverWait(review_div, 5).until(
                                EC.visibility_of_element_located((By.XPATH, './div/div/span')))
                            review_div.find_element_by_xpath('./div/div/span/span').click()
                            WebDriverWait(review_div, 5).until(
                                EC.visibility_of_element_located(
                                    (By.XPATH, './/textarea[contains(@placeholder,"Antworten Sie auf diese Bewertung")]')))
                        #美国
                        # review_div.find_element_by_xpath(
                        #     './/textarea[contains(@placeholder,"Respond to this review")]').send_keys(
                        #     account['comment'])
                        # review_div.find_element_by_xpath('.//span[text()="Post a comment"]/../..').click()
                        #德国
                        review_div.find_element_by_xpath(
                            './/textarea[contains(@placeholder,"Antworten Sie auf diese Bewertung")]').send_keys(
                            account['comment'])
                        review_div.find_element_by_xpath('.//span[text()="Einen Kommentar einsenden"]/../..').click()
                        sleep(0.5)
                        review_div.find_element_by_xpath('./a').click()
                        sleep(1)
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.visibility_of_element_located(
                                (By.XPATH, './/li[@class="a-last"]')))
                        driver.find_element_by_class_name('a-last').click()
                        sleep(1.5)
                    except TimeoutException:
                        all_log.logger.info("已到最后一页")
                        break
                all_log.logger.info("***%s留言结束***"%asin)
            except Exception as e:
                traceback.print_exc()
                error_log.logger.error("---%s留言报错%s---"%(asin,e))
    except Exception as e:
        traceback.print_exc()
        error_log.logger.error("---%s留言报错%s---" % (account['asin'], e))
    finally:
        driver.quit()



    # keyword = account['keyword']
    # driver.get("https://www.amazon.com/s?k=" + keyword + "&ref=nb_sb_noss")
    # WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, '//div[@data-index="0"]')))
    # divs = driver.find_elements_by_xpath('//div[@data-index="0"]/../div')
    # for div in divs:
    #     asin = div.get_attribute("data-asin")
    #     if asin:
    #         print(asin)
    #         review_url = "https://www.amazon.com/product-reviews/" + asin + "?ie=UTF8&reviewerType=all_reviews"
    #         js = 'window.open("' + review_url + '")'
    #         driver.execute_script(js)
    #         driver.switch_to.window(driver.window_handles[1])
    #         try:
    #             while True:
    #                 WebDriverWait(driver, 10).until(
    #                     EC.visibility_of_element_located((By.ID, 'cm_cr-review_list')))
    #                 review_div_list = driver.find_elements_by_xpath(
    #                     '//div[@data-a-expander-name="review_comment_expander"]')
    #                 for review_div in review_div_list:
    #                     review_div.find_element_by_xpath('./a').click()
    #                     sleep(0.5)
    #                     try:
    #                         WebDriverWait(review_div, 3).until(
    #                             EC.visibility_of_element_located(
    #                                 (By.XPATH, './/textarea[contains(@placeholder,"Respond to this review")]')))
    #                     except TimeoutException:
    #                         WebDriverWait(review_div, 5).until(
    #                             EC.visibility_of_element_located(
    #                                 (By.XPATH, './/span[contains(text(),"Comment")]')))
    #                         review_div.find_element_by_xpath('.//span[contains(text(),"Comment")]/..').click()
    #                         WebDriverWait(review_div, 5).until(
    #                             EC.visibility_of_element_located(
    #                                 (By.XPATH, './/textarea[contains(@placeholder,"Respond to this review")]')))
    #                     review_div.find_element_by_xpath(
    #                         './/textarea[contains(@placeholder,"Respond to this review")]').send_keys(
    #                         account['comment'])
    #                     review_div.find_element_by_xpath('.//span[text()="Post a comment"]/../..').click()
    #                     sleep(0.5)
    #                     review_div.find_element_by_xpath('./a').click()
    #                     sleep(1)
    #                 try:
    #                     WebDriverWait(driver, 5).until(
    #                         EC.visibility_of_element_located(
    #                             (By.XPATH, './/li[@class="a-last"]')))
    #                     driver.find_element_by_class_name('a-last').click()
    #                     sleep(1.5)
    #                 except TimeoutException as e:
    #                     print("已到最后一页")
    #                     break
    #         except:
    #             traceback.print_exc()
    #         driver.close()
    #         driver.switch_to.window(driver.window_handles[0])


if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        reg = register()
        validation = reg.checkAuthored()
        config = configparser.RawConfigParser()
        config.read("config.ini", encoding="utf-8")
        process_list = []
        all_log.logger.info("执行的线程数为%s"%(len(config)-1))
        for i, acc in enumerate(config):
            if i > 0:
                process = multiprocessing.Process(target=doComment,args=(config[acc],))
                process.start()
                process_list.append(process)
        for p in process_list:
            p.join()
        all_log.logger.info("执行结束")
    except Exception as e:
        traceback.print_exc()
        error_log.logger.error("程序出错：%s"%e)

