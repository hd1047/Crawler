#!/usr/bin/env python
# coding: utf-8

# In[1]:



import requests
import xlwt
import xlrd
import traceback
import xlsxwriter
import sys
defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)
base_url = "http://api.map.baidu.com/place/v2/search?query={}&bounds={}&page_num={}&page_size=20&scope=2&filter=sort_name:distance|sort_rule:1&output=json&ak={}"


# In[2]:


# 距离和经纬度的转换
# latlng = []
# distance 米
import math
def latlng_trans(latlng, distance):
    lat = latlng[0]
    lng = latlng[1]
    lat_change = distance / 1000.0 / 111
    lat_top_right = lat + lat_change
    lng_change_1 = distance / 1000.0 / (math.cos(lat_top_right / 180 * math.pi) * 111)
    lng_top_right = lng + lng_change_1
    lat_bott_left = lat - lat_change
    lng_change_2 = distance / 1000.0 / (math.cos(lat_bott_left / 180 * math.pi) * 111)
    lng_bott_left = lng - lng_change_2
    return [lat_bott_left,lng_bott_left],[lat_top_right,lng_top_right]


# In[3]:


def get_url(keyword,radius,lat_lng,baidu_ak, page=0):
    trans_latlng = latlng_trans(lat_lng, radius)
    url = base_url.format(keyword, str(trans_latlng[0][0]) + ',' + str(trans_latlng[0][1])                                + ',' + str(trans_latlng[1][0]) + ',' + str(trans_latlng[1][1]), page, baidu_ak)
    return url


# In[4]:


def get_four_areas(url,keyword,baidu_ak):
    #分割的原则是将输入的经纬度范围平均分成四份
    areas=[]
    boundary = url.split('=')[2].split('&')[0].split(',')
    w1=float(boundary[0])
    j1=float(boundary[1])
    w2=float(boundary[2])
    j2=float(boundary[3])
    wei=(float(w2) - float(w1)) / 2
    jing=(float(j2) - float(j1)) / 2
    area1=[w1,j1,w1 + wei,j1 + jing]
    area1=','.join([str(x) for x in area1])
    area2=[w1,j1 + jing,w1 + wei,j2]
    area2 = ','.join([str(x) for x in area2])
    area3=[w1 + wei,j1,w2,j1 + jing]
    area3 = ','.join([str(x) for x in area3])
    area4=[w1 + wei,j1 + jing,w2,j2]
    area4 = ','.join([str(x) for x in area4])
    areas=[area1,area2,area3,area4]
    for index, area in enumerate(areas):
        url_temp = base_url.format(keyword,area,str(0),baidu_ak)
        print('第'+str(index+1)+'个分割图形url：'+url_temp)
        yield url_temp


# In[5]:


def parse_url(url, keyw, name, baidu_ak):
    hos_filter = ['医疗;综合医院', "医疗;专科医院", "医疗;诊所"]
    try:
        html = requests.get(url)
        data = html.json()
        if data['total'] > 0 and data['total'] < 400:
            print('total is ' + str(data['total']))
            page_numbers = int(data['total'] / 20) + 1
            for result in data['results']:
                try:
                    if result['name'] not in name: 
                        if result['name'].find('院务处') == -1 and result['name'].find('中药库') == -1 and result['name'].find('后勤楼') == -1 and result['name'].find('院史馆') == -1 and result['name'].find('后勤仓库') == -1:
                            if result['detail_info']['tag'] in hos_filter:
                                name.append(result['name'])
                except:
                    print(result)
            if page_numbers > 1:
                for page in range(1, page_numbers):
                    url2 = url.replace('page_num=0', 'page_num=' + str(page))
                    try:
                        html = requests.get(url2)
                        data = html.json()
                        for result in data['results']:
                            try:
                                if result['name'] not in name: 
                                    if result['name'].find('院务处') == -1 and result['name'].find('中药库') == -1 and result['name'].find('后勤楼') == -1 and result['name'].find('院史馆') == -1 and result['name'].find('后勤仓库') == -1:
                                        if result['detail_info']['tag'] in hos_filter:
                                            name.append(result['name'])
                            except:
                                print(result)
                    except:
                        print('page unreadable')
            print('length is ' + str(len(name)))
        elif data['total'] == 400:
            print("该url:" + url + ' 区域过大，准备分割')
            url_4 = get_four_areas(url, keyw, baidu_ak)
            for url_temp in url_4:
                parse_url(url_temp, keyw, name, baidu_ak)
    
    except Exception as e:
        print(e)


# In[6]:


def func_hospital(city, branch_no, baidu_ak, radius, workbook):
    #workbook = xlrd.open_workbook(r'C:\Users\JingWenChen\Desktop\branch_from_web.xlsx')
    city_sheet = workbook.sheet_by_name(city) 
    branch_no_city = [int(city_sheet.col_values(4)[i]) for i in range(1, city_sheet.nrows)]
    lat_lng_city = [[city_sheet.col_values(2)[i],city_sheet.col_values(3)[i]] for i in range(1,city_sheet.nrows)]
    latlng_dict = dict(zip(branch_no_city, lat_lng_city))
    lat_lng = latlng_dict[branch_no] #获取所选支行的经纬度
    keyword = '医院'
    url = get_url(keyword,radius,lat_lng,baidu_ak)
    
    name = []
    parse_url(url,keyword,name,baidu_ak)
    num = len(name)

    return num 


