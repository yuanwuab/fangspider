# -*- coding: utf-8 -*-
import scrapy
import re
from fang.items import NewHouseItem,ESFHouseItem

class SfwSpider(scrapy.Spider):
    name = 'sfw'
    allowed_domains = ['fang.com']
    start_urls = ['http://www.fang.com/SoufunFamily.htm']

    def parse(self, response):
        trs = response.xpath("//div[@class='outCont']//tr")
        province = None
        for tr in trs:
            tds = tr.xpath(".//td[not(@class)]")
            province_td = tds[0]
            province_text = province_td.xpath(".//text()").get()
            province_text = re.sub(r"\s","",province_text)
            if province_text:
                province = province_text

            # 不爬取海外的城市的房源
            if province == '其它':
                continue

            city_td = tds[1]
            city_links = city_td.xpath(".//a")
            for city_link in city_links:
                city = city_link.xpath(".//text()").get()
                city_url = city_link.xpath(".//@href").get()
                # 构建新房的url链接
                url_module = city_url.split("//")
                scheme = url_module[0]
                domain = url_module[1]
                if 'bj.' in domain:
                    newhouse_url = 'http://newhouse.fang.com/house/s/'
                    esf_url = 'http://esf.fang.com/'
                else:
                    newhouse_url = scheme + '//' + "newhouse." + domain + "house/s/"
                    # 构建二手房的url链接
                    esf_url = scheme + "//" + "esf." + domain

                # yield scrapy.Request(url=newhouse_url,callback=self.parse_newhouse,meta={"info":(province,city)})

                yield scrapy.Request(url=esf_url,callback=self.parse_esf,meta={"info":(province,city)})

    def parse_newhouse(self,response):
        province,city = response.meta.get('info')
        lis = response.xpath("//div[contains(@class,'nl_con')]/ul/li")
        for li in lis:
            name = li.xpath(".//div[@class='nlcd_name']/a/text()").get().strip()
            house_type_list = li.xpath(".//div[contains(@class,'house_type')]/a/text()").getall()
            house_type_list = list(map(lambda x:re.sub(r"\s","",x),house_type_list))
            rooms = list(filter(lambda x:x.endswith("居"),house_type_list))
            area = "".join(li.xpath(".//div[contains(@class,'house_type')]/text()").getall())
            area = re.sub(r"\s|－|/","",area)
            address = li.xpath(".//div[@class='address']/a/@title").get()
            district_text = "".join(li.xpath(".//div[@class='address']/a//text()").getall())
            district = re.search(r".*\[(.+)\].*",district_text).group(1)
            sale = li.xpath(".//div[contains(@class,'fangyuan')]/span/text()").get()
            price = "".join(li.xpath(".//div[@class='nhouse_price']//text()").getall())
            price = re.sub(r"\s|广告","",price)
            origin_url = li.xpath(".//div[@class='nlcd_name']/a/@href").get()

            item = NewHouseItem(name=name,rooms=rooms,area=area,address=address,district=district,sale=sale,price=price,origin_url=origin_url,province=province,city=city)
            yield item

        next_url = response.xpath("//div[@class='page']//a[@class='next']/@href").get()
        if next_url:
            yield scrapy.Request(url=response.urljoin(next_url),callback=self.parse_newhouse,meta={"info":(province,city)})


    def parse_esf(self,response):
        province,city = response.meta.get('info')
        dls = response.xpath("//div[@class='houseList']/dl")
        for dl in dls:
            item = ESFHouseItem(province=province,city=city)
            item['name'] = dl.xpath(".//p[@class='mt10']/a/span/text()").get()
            infos = dl.xpath(".//p[@class='mt12']/text()").getall()
            infos = list(map(lambda x:re.sub(r"\s","",x),infos))
            for info in infos:
                if "厅" in info:
                    item['rooms'] = info
                elif '层' in info:
                    item['floor'] = info
                elif '向' in info:
                    item['toward'] = info
                else:
                    item['year'] = info.replace("建筑年代：","")
            item['address'] = dl.xpath(".//p[@class='mt10']/span/@title").get()
            item['area'] = dl.xpath(".//div[contains(@class,'area')]/p/text()").get()
            item['price'] = "".join(dl.xpath(".//div[@class='moreInfo']/p[1]//text()").getall())
            item['unit'] = "".join(dl.xpath(".//div[@class='moreInfo']/p[2]//text()").getall())
            detail_url = dl.xpath(".//p[@class='title']/a/@href").get()
            item['origin_url'] = response.urljoin(detail_url)
            yield item
        next_url = response.xpath("//a[@id='PageControl1_hlk_next']/@href").get()
        yield scrapy.Request(url=response.urljoin(next_url),callback=self.parse_esf,meta={"info":(province,city)})





