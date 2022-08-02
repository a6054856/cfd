"""
cron: 50 59 * * * *
new Env('财富岛兑换红包');
"""
import os
import re
import time
import json
import datetime
import requests
from notify import send
from ql_util import get_random_str
from ql_api import get_envs, disable_env, post_envs, put_envs

# 默认配置(看不懂代码也勿动)
cfd_start_time = -0.15
cfd_offset_time = 0.01

# 基础配置勿动
#cfd_url = "https://m.jingxi.com/jxbfd/user/ExchangePrize?strZone=jxbfd&bizCode=jxbfd&source=jxbfd&dwEnv=7&_cfd_t=1655280000000&dwType=3&dwLvl=15&ddwPaperMoney=100000&strPoolName=jxcfd2_exchange_hb_202205&sceneval=2&g_login_type=1"
cfd_url = "https://m.jingxi.com/jxbfd/user/ExchangePrize?strZone=jxbfd&bizCode=jxbfd&source=jxbfd&strDeviceId=205a305d21fe7b50&dwEnv=7&_cfd_t=1659163464799&ptag=138631.77.28&dwType=3&dwLvl=1&ddwPaperMoney=100000&strPoolName=jxcfd2_exchange_hb_202208&strPgtimestamp=1659163464764&strPhoneID=205a305d21fe7b50&strPgUUNum=2a288719de58a42bb76e7e12debd4c12&_stk=_cfd_t%2CbizCode%2CddwPaperMoney%2CdwEnv%2CdwLvl%2CdwType%2Cptag%2Csource%2CstrDeviceId%2CstrPgUUNum%2CstrPgtimestamp%2CstrPhoneID%2CstrPoolName%2CstrZone&_ste=1&h5st=20220730144424800%3B2811142658388447%3B92a36%3Btk02wa9fe1b7e18nneEGby9i9qokxEUg5tzYVKtR1QWD%2BE%2FhIo547KOlz1tzfC3TXOjwJ%2Ft6uALn41BfnHw5FRSrLR20%3B5a102bbf2a5c81fb4d2c2520febbc0d80b1105c570b671bab9b76a43f220fee7%3B3.1%3B1659163464800%3B62f4d401ae05799f14989d31956d3c5fcc829ed37fcdeed4a441c9247af14f05a5599b1932ed9018725b7f152a59a65a8ee3994f819b044bd6195b18bc929c667b2aa4d4086fa7da328843ece58e7b44adcb19efab73f0427565754effca6ae614d8c74cf92001d61251e382bf4d2b2546067947377f8c2e8b59a7b6abc66dd0bff98f36c468e9c28c9015f1de23d6e0&_=1659163464805&sceneval=2&g_login_type=1&callback=jsonpCBKJJ&g_ty=ls&appCode=msd1188198"
#cfd_url = "https://m.jingxi.com/jxbfd/user/ExchangePrize?strZone=jxbfd&bizCode=jxbfd&source=jxbfd&dwEnv=7&_cfd_t=1659146400000&dwType=3&dwLvl=1&ddwPaperMoney=100000&strPoolName=jxcfd2_exchange_hb_202208&sceneval=2&g_login_type=1"
pattern_pin = re.compile(r'pt_pin=([\w\W]*?);')
pattern_data = re.compile(r'\(([\w\W]*?)\)')
pattern_jsonp = re.compile(r'jsonp([\w\W]*?)')
remark = ""

# 判断新旧版青龙
ql_auth_path = '/ql/data/config/auth.json'
# 判断环境变量
flag = 'new'
if not os.path.exists(ql_auth_path):
    flag = 'old'


# 获取下个整点和时间戳
def get_date() -> str and int:
    # 当前时间
    now_time = datetime.datetime.now()
    # 把根据当前时间计算下一个整点时间戳
    integer_time = (now_time + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")
    time_array = time.strptime(integer_time, "%Y-%m-%d %H:%M:%S")
    time_stamp = int(time.mktime(time_array))
    return integer_time, time_stamp


# 获取要执行兑换的cookie
def get_cookie():
    ck_list = []
    pin = "null"
    cookie = None
    cookies = get_envs("CFD_COOKIE")
    for ck in cookies:
        if ck.get('status') == 0:
            ck_list.append(ck)
    if len(ck_list) >= 1:
        cookie = ck_list[0]
        # 新增备注
        global remark
        remark = cookie.get('remarks')
        if remark is None:
            remark = ""
        re_list = pattern_pin.search(cookie.get('value'))
        if re_list is not None:
            pin = re_list.group(1)
        print('共配置{}条CK,已载入用户[{}],备注为[{}]'.format(len(ck_list), pin, remark))
    else:
        print('共配置{}条CK,请添加环境变量,或查看环境变量状态'.format(len(ck_list)))
    return pin, cookie, remark

# 获取配置参数
def get_config():
    start_dist = {}
    start_times = get_envs("CFD_START_TIME")
    if len(start_times) >= 1:
        start_dist = start_times[0]
        start_time = float(start_dist.get('value'))
        print('从环境变量中载入时间变量[{}]'.format(start_time))
    else:
        start_time = cfd_start_time
        u_data = post_envs('CFD_START_TIME', str(start_time), '财富岛兑换时间配置,自动生成,勿动')
        if len(u_data) == 1:
            start_dist = u_data[0]
        print('从默认配置中载入时间变量[{}]'.format(start_time))
    return start_time, start_dist


# 抢购红包请求函数
def cfd_qq(def_start_time):
    # 进行时间等待,然后发送请求
    end_time = time.time()
    while end_time < def_start_time:
        end_time = time.time()
    # 记录请求时间,发送请求
    t1 = time.time()
    d1 = datetime.datetime.now().strftime("%H:%M:%S.%f")
    res = requests.get(cfd_url, headers=headers)
    print("打印返回结果如下：")
    print(res.text)
    t2 = time.time()
    # 正则对结果进行提取
    re_jsonp = pattern_jsonp.search(res.text)
    re_list = pattern_data.search(res.text)
    # 进行json转换
    if re_jsonp is None:
        data = json.loads(res.text)
    else:
        data = json.loads(re_list.group(1))
    msg = "原备注【"+remark + "】抢购结果：" + data['sErrMsg']
    msg_temp = data['sErrMsg']
    # 根据返回值判断
    if data['iRet'] == 0:
        # 抢到了
        msg = "原备注【"+remark + "】抢购结果：" + "可能抢到了,也可能是CK忘记加cid=1;请自行检查"
        if flag == "old":
            put_envs(u_cookie.get('_id'), u_cookie.get('name'), u_cookie.get('value'), msg)
            disable_env(u_cookie.get('_id'))
        elif flag == "new":
            put_envs(u_cookie.get('id'), u_cookie.get('name'), u_cookie.get('value'), msg)
            disable_env(u_cookie.get('id')) 
        send('财富岛抢购通知', '账号：【'+u_pin+'】，备注【'+ remark +'】\n您可能抢到了,也可能是CK忘记加cid=1;请自行检查')       
    elif data['iRet'] == 2016:
        # 需要减
        start_time = float(u_start_time) - float(cfd_offset_time)
        if flag == "old":
            put_envs(u_start_dist.get('_id'), u_start_dist.get('name'), str(start_time)[:8])
        elif flag == "new":
            put_envs(u_start_dist.get('id'), u_start_dist.get('name'), str(start_time)[:8])
    elif data['iRet'] == 2013:
        # 需要加
        start_time = float(u_start_time) + float(cfd_offset_time)
        # print(u_start_dist)
        if flag == "old":
            put_envs(u_start_dist.get('_id'), u_start_dist.get('name'), str(start_time)[:8])
        elif flag == "new":
            put_envs(u_start_dist.get('id'), u_start_dist.get('name'), str(start_time)[:8])
    elif data['iRet'] == 1014:
        # URL过期
        pass
    elif data['iRet'] == 2007:
        # 财富值不够
        if flag == "old":
            put_envs(u_cookie.get('_id'), u_cookie.get('name'), u_cookie.get('value'), msg)
            disable_env(u_cookie.get('_id'))
        elif flag == "new":
            put_envs(u_cookie.get('id'), u_cookie.get('name'), u_cookie.get('value'), msg)
            disable_env(u_cookie.get('id'))
        send('财富岛抢购通知', '账号：【'+u_pin+'】，备注【'+ remark +'】\n您的财富值不够')
    elif data['iRet'] == 9999:
        # 账号过期
        if flag == "old":
            put_envs(u_cookie.get('_id'), u_cookie.get('name'), u_cookie.get('value'), msg)
            disable_env(u_cookie.get('_id'))
        elif flag == "new":
            put_envs(u_cookie.get('id'), u_cookie.get('name'), u_cookie.get('value'), msg)
            disable_env(u_cookie.get('id'))
        send('财富岛抢购通知', '账号：【'+u_pin+'】，备注【'+ remark +'】\n您的抢购账号已失效')
    print("实际发送[{}]\n耗时[{:.3f}]\n用户[{}]，备注[{}]\n抢购结果[{}]".format(d1, (t2 - t1), u_pin, remark, msg_temp))


if __name__ == '__main__':
    print("- 程序初始化")
    print("脚本进入时间[{}]".format(datetime.datetime.now().strftime("%H:%M:%S.%f")))
    # 从环境变量获取url,不存在则从配置获取
    cfd_url = os.getenv("CFD_URL", cfd_url)
    # 获取cookie等参数
    u_pin, u_cookie, remark = get_cookie()
    # 获取时间等参数
    u_start_time, u_start_dist = get_config()
    # 预计下个整点为
    u_integer_time, u_time_stamp = get_date()
    print("抢购整点[{}]".format(u_integer_time))
    print("- 初始化结束\n")

    print("- 主逻辑程序进入")
    UA = "jdpingou;iPhone;5.11.0;15.1.1;{};network/wifi;model/iPhone13,2;appBuild/100755;ADID/;supportApplePay/1;hasUPPay/0;pushNoticeIsOpen/1;hasOCPay/0;supportBestPay/0;session/22;pap/JA2019_3111789;brand/apple;supportJDSHWK/1;Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148".format(
        get_random_str(45, True))
    if u_cookie is None:
        print("未读取到CFD_COOKIE,程序结束")
    else:
        headers = {
            "Host": "m.jingxi.com",
            "Accept": "*/*",
            "Connection": "keep-alive",
            'Cookie': u_cookie['value'],
            "User-Agent": UA,
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            "Referer": "https://st.jingxi.com/",
            "Accept-Encoding": "gzip, deflate, br"
        }
        u_start_sleep = float(u_time_stamp) + float(u_start_time)
        print("预计发送时间为[{}]".format(datetime.datetime.fromtimestamp(u_start_sleep).strftime("%H:%M:%S.%f")))
        if u_start_sleep - time.time() > 300:
            print("离整点时间大于5分钟,强制立即执行")
            cfd_qq(0)
        else:
            cfd_qq(u_start_sleep)
    print("- 主逻辑程序结束")
