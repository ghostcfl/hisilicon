import asyncio
import re
import os
import requests
import json
from pyppeteer import launch
from pyquery import PyQuery

url = "http://www.hisilicon.com"


async def run():
    b = await launch({"headless": True, 'autoClose': True, "args": [f'--window-size={1600},{900}']})
    p = await b.newPage()
    await p.setViewport({"width": 1600, "height": 900})
    await p.goto(url)
    content = await p.content()
    doc = PyQuery(content)
    for c in doc("ul.sec-menu3.sec-menu.sec-mune2 li").items():
        nav_url = url + c.find("a").attr("href")
        match = re.search("Products", nav_url, re.I)
        category = nav_url.split("/")[-1]
        if match:
            if not os.path.exists(category):
                os.mkdir(category)
            await p.goto(nav_url)
            while 1:
                try:
                    await p.waitForSelector("#p_more", visible=True, timeout=5000)
                except Exception as e:
                    # print(e)
                    product_content = await p.content()
                    break
                else:
                    await p.click("#p_more")
                    await asyncio.sleep(2)
            doc = PyQuery(product_content)
            product_list = doc("#ul_productlistinner li").items()
            result = []
            for product in product_list:
                item = {}
                item['category'] = category
                item['title'] = product.find("div.title h3").text().strip()
                item['sub_title'] = product.find("div.subh3").text().strip()
                if not os.path.exists(category + "/" + item["sub_title"]):
                    os.mkdir(category + "/" + item["sub_title"])
                features = product.find("dl").items()
                for f in features:
                    f_title = f.find('dt').text().strip()
                    x = f_title.replace(" ", "_").replace(":", "").lower()
                    if not item.get(x):
                        item[x] = []
                    for dd in f.find("dd").items():
                        item[x].append(dd.text().strip())
                result.append(item)
                item['pdf_url'] = url + product.find("a").attr("href")
                fail_url = re.search("javascript", item['pdf_url'], re.I)
                if not fail_url:
                    response = requests.get(item['pdf_url'])
                    with open(category + "/" + item['sub_title'] + "/" + item['sub_title'] + ".pdf", "wb") as pdf:
                        pdf.write(response.content)
                else:
                    item['pdf_url'] = None
                with open(category + "/" + item['sub_title'] + "/" + item['sub_title'] + ".json", 'w') as js:
                    js.write(json.dumps(item, indent=4))



if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())
