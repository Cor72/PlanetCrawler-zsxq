import re
import requests
import json
import os
import calendar
import pdfkit
import shutil
import datetime
import urllib.request
import uuid
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.parse import unquote
import base64
import time

# ================== 配置区域 ==================
TARGET_YEAR = 2026  # <--- 修改这里：你想爬取哪一年？
ZSXQ_ACCESS_TOKEN = 'C5000000-12F9-4503-B272-C712345671AF_76Aasfq23456yu'    # 必须修改为最新的Token
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/567.00 (KHTML, like Gecko) Chrome/111.1.1.1 Safari/347.36'
GROUP_ID = '554555555555'                         # 知识星球中的小组ID
# =============================================

# 以下为脚本默认配置，通常不需要修改
PDF_FILE_NAME = 'PlantCrawl.pdf'
DOWLOAD_PICS = False
DOWLOAD_COMMENTS = True
ONLY_DIGESTS = False
FROM_DATE_TO_DATE = False  # 默认值，会被主程序覆盖
EARLY_DATE = ''
LATE_DATE = ''
DELETE_PICS_WHEN_DONE = True
DELETE_HTML_WHEN_DONE = True
COUNTS_PER_TIME = 30
DEBUG = False
DEBUG_NUM = 120
SLEEP_FLAG = True
SLEEP_SEC = 2

html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
</head>
<body>
<h1>{title}</h1>
<br>{author} - {cretime}<br>
<p>{text}</p>
</body>
</html>
"""
htmls = []
num = 0

def get_data(url):

    OVER_DATE_BREAK = False
    global htmls, num

    # 1. 生成时间戳
    timestamp = str(int(time.time()))
    
    # 2. 计算签名
    sign_str = ZSXQ_ACCESS_TOKEN + timestamp
    signature = hashlib.sha1(sign_str.encode('utf-8')).hexdigest()

    headers = {
        'Cookie': 'zsxq_access_token=' + ZSXQ_ACCESS_TOKEN,
        'User-Agent': 'Dalian Zuoyou It Technology Co., Ltd./2.92.0 (iPhone; iOS 15.5; Scale/3.00)', 
        'x-version': '2.92.0',
        'x-timestamp': timestamp,         
        'x-signature': signature,
        'x-request-id': str(uuid.uuid4()),
        'Origin': 'https://wx.zsxq.com',
        'Connection': 'keep-alive'
    }
    
    rsp = requests.get(url, headers=headers)
    with open('temp.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(rsp.json(), indent=2, ensure_ascii=False))
    
    with open('temp.json', encoding='utf-8') as f:
        json_data = json.loads(f.read())
        
        if not json_data.get('resp_data'):
            print("请求失败，API 返回信息如下：")
            print(json.dumps(json_data, indent=2, ensure_ascii=False))
            return []

        topics = json_data.get('resp_data').get('topics')
        if not topics:
            print("未获取到 topics 数据。")
            return []

        for topic in topics:
            # 这里读取的是全局变量 FROM_DATE_TO_DATE 和 EARLY_DATE
            if FROM_DATE_TO_DATE and EARLY_DATE.strip():
                if topic.get('create_time') < EARLY_DATE.strip():
                    OVER_DATE_BREAK = True
                    break

            content = topic.get('question', topic.get('talk', topic.get('task', topic.get('solution'))))
            if not content: continue # 防止空内容报错

            anonymous = content.get('anonymous')
            if anonymous:
                author = '匿名用户'
            else:
                author = content.get('owner').get('name')

            cretime = (topic.get('create_time')[:23]).replace('T', ' ')

            text = content.get('text', '')
            text = handle_link(text)
            title = str(num) + '_' + cretime[:16]
            num += 1
            if topic.get('digested') == True:
                title += '_精华'

            if DOWLOAD_PICS and content.get('images'):
                soup = BeautifulSoup(html_template, 'html.parser')
                images_index = 0
                for img in content.get('images'):
                    img_url = img.get('large').get('url')
                    local_url = './images/' + str(num - 1) + '_' + str(images_index) + '.jpg'
                    images_index += 1
                    download_image(img_url, local_url)
                    img_tag = soup.new_tag('img', src=encode_image(local_url))
                    soup.body.append(img_tag)
                html_img = str(soup)
                html = html_img.format(title=title, text=text, author=author, cretime=cretime)
            else:
                html = html_template.format(title=title, text=text, author=author, cretime=cretime)

            if topic.get('question'):
                answer_author = topic.get('answer').get('owner').get('name', '')
                answer = topic.get('answer').get('text', "")
                answer = handle_link(answer)

                soup = BeautifulSoup(html, 'html.parser')
                answer_tag = soup.new_tag('p')

                answer = '【' + answer_author + '】 回答：<br>' + answer
                soup_temp = BeautifulSoup(answer, 'html.parser')
                answer_tag.append(soup_temp)

                soup.body.append(answer_tag)
                html = str(soup) 
            
            files = content.get('files')
            if files:
                files_content = '<i>文件列表(需访问网站下载) :<br>'
                for f in files:
                    files_content += f.get('name') + '<br>'
                files_content += '</i>'
                soup = BeautifulSoup(html, 'html.parser')
                files_tag = soup.new_tag('p')
                soup_temp = BeautifulSoup(files_content, 'html.parser')
                files_tag.append(soup_temp)
                soup.body.append(files_tag)
                html = str(soup)

            comments = topic.get('show_comments')
            if DOWLOAD_COMMENTS and comments:
                soup = BeautifulSoup(html, 'html.parser')
                hr_tag = soup.new_tag('hr')
                soup.body.append(hr_tag)
                for comment in comments:
                    comment_str = ''
                    if comment.get('repliee'):
                        comment_str = '[' + comment.get('owner').get('name') + ' 回复 ' + comment.get('repliee').get('name') + '] : ' + handle_link(comment.get('text'))
                    else:
                        comment_str = '[' + comment.get('owner').get('name') + '] : ' + handle_link(comment.get('text'))

                    comment_tag = soup.new_tag('p')
                    soup_temp = BeautifulSoup(comment_str, 'html.parser')
                    comment_tag.append(soup_temp)
                    soup.body.append(comment_tag)
                html = str(soup)

            htmls.append(html)

    if DEBUG and num >= DEBUG_NUM:
       return htmls

    if OVER_DATE_BREAK:
        return htmls

    next_page = rsp.json().get('resp_data').get('topics')
    if next_page:
        create_time = next_page[-1].get('create_time')
        if create_time[20:23] == "000":
            end_time = create_time[:20]+"999"+create_time[23:]
            str_date_time = end_time[:19]
            delta = datetime.timedelta(seconds=1)
            date_time = datetime.datetime.strptime(str_date_time, '%Y-%m-%dT%H:%M:%S')
            date_time = date_time - delta
            str_date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
            end_time = str_date_time + end_time[19:]
        else :
            res = int(create_time[20:23])-1
            end_time = create_time[:20]+str(res).zfill(3)+create_time[23:]
        end_time = quote(end_time)
        if len(end_time) == 33:
            end_time = end_time[:24] + '0' + end_time[24:]
        
        # 注意：这里的 start_url 需要在函数外部可访问，或者作为参数传递
        # 由于原代码结构，这里最好在全局构建好基础URL，这里只负责拼接 end_time
        # 为简化修改，建议将 start_url 的构建逻辑移到循环外或作为参数传入
        # 这里我做一个简单的修正，让 next_url 能正确生成
        
        # 获取当前的基础URL (不含 end_time)
        # 这里的 url 是传入的参数，我们需要去掉旧的 end_time
        base_url = url.split('&end_time=')[0]
        next_url = base_url + '&end_time=' + end_time

        if SLEEP_FLAG:
            time.sleep(SLEEP_SEC)
        print(f"正在翻页: {next_url}")
        get_data(next_url)

    return htmls

def encode_image(image_url):
    with open(image_url, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return 'data:image/png;base64,' + encoded_string.decode('utf-8')

def download_image(url, local_url):
    try:
        urllib.request.urlretrieve(url, local_url)
    except urllib.error.ContentTooShortError:
        print('Network not good. Reloading ' + url)
        download_image(url, local_url)

def handle_link(text):
    soup = BeautifulSoup(text, "html.parser")

    mention = soup.find_all('e', attrs={'type' : 'mention'})
    if len(mention):
        for m in mention:
            mention_name = m.attrs['title']
            new_tag = soup.new_tag('span')
            new_tag.string = mention_name
            m.replace_with(new_tag)

    hashtag = soup.find_all('e', attrs={'type' : 'hashtag'})
    if len(hashtag):
        for tag in hashtag:
            tag_name = unquote(tag.attrs['title'])
            new_tag = soup.new_tag('span')
            new_tag.string = tag_name
            tag.replace_with(new_tag)

    links = soup.find_all('e', attrs={'type' : 'web'})
    if len(links):
        for link in links:
            title = unquote(link.attrs['title'])
            href = unquote(link.attrs['href'])
            new_a_tag = soup.new_tag('a', href=href)
            new_a_tag.string = title
            link.replace_with(new_a_tag)

    text = str(soup)
    text = re.sub(r'<e[^>]*>', '', text).strip()
    text = text.replace('\n', '<br>')
    return text

def make_pdf(htmls):
    html_files = []
    for index, html in enumerate(htmls):
        file = str(index) + ".html"
        html_files.append(file)
        with open(file, "w", encoding="utf-8") as f:
            f.write(html)

    options = {
        "page-size": "Letter",
        "margin-top": "0.75in",
        "margin-right": "0.75in",
        "margin-bottom": "0.75in",
        "margin-left": "0.75in",
        "encoding": "UTF-8",
        "custom-header": [("Accept-Encoding", "gzip")],
        "cookie": [
            ("cookie-name1", "cookie-value1"), ("cookie-name2", "cookie-value2")
        ],
        "outline-depth": 10,
    }

    pdf_error_flag = False
    try:
        pdfkit.from_file(html_files, PDF_FILE_NAME, options=options)
    except Exception as e:
        pdf_error_flag = True
        print("电子书生成失败！")
        pass

    if DELETE_HTML_WHEN_DONE:
        for file in html_files:
            if os.path.exists(file):
                os.remove(file)

    if not pdf_error_flag:
        print(f"电子书生成成功：{PDF_FILE_NAME}")

if __name__ == '__main__':
    images_path = r'./images'
    if DOWLOAD_PICS:
        if os.path.exists(images_path):
            shutil.rmtree(images_path)
        os.mkdir(images_path)

    # 关键修正：声明全局变量，以便在循环中修改它们供 get_data 函数使用
    # global FROM_DATE_TO_DATE, EARLY_DATE, LATE_DATE, PDF_FILE_NAME, htmls, num

    # 构造基础 URL (v2 接口)
    base_api_url = ''
    if ONLY_DIGESTS:
        base_api_url = 'https://api.zsxq.com/v2/groups/' + GROUP_ID + '/topics?scope=digests&count=' + str(COUNTS_PER_TIME)
    else:
        base_api_url = 'https://api.zsxq.com/v2/groups/' + GROUP_ID + '/topics?count=' + str(COUNTS_PER_TIME)

    for month in range(1, 13):
        print(f"\n========== 开始爬取 {TARGET_YEAR} 年 {month} 月的数据 ==========")

        # 1. 计算该月的起始和结束时间
        _, days_in_month = calendar.monthrange(TARGET_YEAR, month)
        
        # 起始时间：月初第一天 (用于 get_data 内部的判断)
        EARLY_DATE = f'{TARGET_YEAR}-{month:02d}-01T00:00:00.000+0800'
        # 结束时间：月末最后一天 (用于 URL 参数)
        LATE_DATE = f'{TARGET_YEAR}-{month:02d}-{days_in_month}T23:59:59.999+0800'

        # 2. 开启时间区间过滤
        FROM_DATE_TO_DATE = True
        
        # 设置当月的 PDF 文件名
        PDF_FILE_NAME = f'公周_{TARGET_YEAR}_{month:02d}.pdf'

        # 3. 重置全局变量 (防止数据累加)
        htmls = []
        num = 0
        
        # 构造当月的请求 URL (从月末开始往前爬)
        url = base_api_url + '&end_time=' + quote(LATE_DATE.strip())
        
        # 4. 开始爬取
        try:
            make_pdf(get_data(url))
        except Exception as e:
            print(f"爬取 {month} 月时发生错误: {e}")
            continue

        print(f"========== {TARGET_YEAR} 年 {month} 月完成，等待 3 秒后继续 ==========")
        time.sleep(3)

    print("\n所有月份爬取完毕！")

    if DOWLOAD_PICS and DELETE_PICS_WHEN_DONE:
        shutil.rmtree(images_path)