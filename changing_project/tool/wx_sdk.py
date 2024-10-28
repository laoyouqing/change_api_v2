import base64
import hashlib
import json
import random
import string
import time

import requests


class wx_mini_sdk:
    def __init__(self):
        pass

    def mini_login(self,appid,secret,js_code):
        response = requests.get(
            f"https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={js_code}&grant_type=authorization_code")
        re_dict = json.loads(response.text)
        return re_dict


    def get_access_token(self,appid,secret):
        response = requests.get(
            f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}")
        re_dict = json.loads(response.text)
        return re_dict



    def get_mobile(self,access_token,code):
        params = {
            "code":code
        }
        response = requests.post(
            f"https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={access_token}",json=params)
        re_dict = json.loads(response.text)
        return re_dict


    def send_tempalte_keyword(self, access_token, openid, template_id, page, data):
        '''发送订阅消息'''
        params = {
            "touser": openid,  # 用户openid
            "template_id": template_id,  # 所需下发的订阅模板id
            "page": page,  # 点击模板卡片后的跳转页面，仅限本小程序内的页面
            "data": data,  # 模板内容
            "miniprogram_state": 'trial',  # 跳转小程序类型：developer为开发版；trial为体验版；formal为正式版；默认为正式版
        }
        params = json.dumps(params)
        response = requests.post(
            f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}",
            data=params)
        re_dict = json.loads(response.text)
        return re_dict



class tl_pay_sdk:

    def __init__(self):
        self.notify_url=''   #异步通知


    def rsa_sign(self,param):
        '''生成签名'''
        stringA=''
        param.update({'key':'123456'})
        ks=sorted(param.keys())
        #参数排序
        for k in ks:
            stringA+=(k+'='+param[k]+'&')
        #拼接商户key
        stringSignTemp=stringA[:-1]
        #md5加密
        hash_md5=hashlib.md5(stringSignTemp.encode('utf8'))
        sign=hash_md5.hexdigest().upper()
        del param['key']
        return sign


    def tl_mini_pay(self, appid, orgid,mch_id, order_id, money, notify_url,cus_rsa_private_key, **kwargs):
        """通联小程序支付"""
        nonce_str = ''.join(random.sample(string.ascii_letters + string.digits, 30))  # 生成随机字符串，小于32位
        params = {
            'cusid': mch_id,
            'orgid': orgid,
            'appid': appid,  # 小程序ID
            'version': '12',
            'trxamt': str(int(money)),  # 标价金额/单位为分
            'reqsn': order_id,  # 生成的订单号
            "body": '充值',  # 支付说明
            'notify_url': notify_url,
            'paytype': "W06",  # 支付类型
            'randomstr': nonce_str,
            'signtype': 'MD5'
        }
        # 生成签名
        # 生成签名
        params['sign'] = self.rsa_sign(params)
        # python3一种写法
        return params


    def tl_refunds(self,orgid,cusid,appid,trxamt,reqsn,oldtrxid,cus_rsa_private_key):
        nonce_str = ''.join(random.sample(string.ascii_letters + string.digits, 30))  # 生成随机字符串，小于32位
        params = {
        'orgid': orgid,
        'cusid': cusid,
        'appid': appid,
        'trxamt': str(int(trxamt)), #退款金额
        'reqsn': reqsn, #商户退款订单号
        'oldtrxid': oldtrxid, #原交易的收银宝平台流水
        'randomstr':nonce_str,
        'signtype':'MD5',
        }
        # 生成签名
        params['sign'] = self.rsa_sign(params)
        response = requests.post('https://vsp.allinpay.com/apiweb/tranx/refund', data=params)
        re_dict = json.loads(response.text)
        return re_dict



class wx_pay_sdk:

    def sign_str(self,method, url_path,timestamp, nonce_str,request_body):
        """
        生成欲签名字符串
        """
        sign_list = [
            method,
            url_path,
            timestamp,
            nonce_str,
            request_body
        ]
        return '\n'.join(sign_list) + '\n'


    def sign_string(self,key_pem, unsigned_string):
        # 开始计算签名
        # 开始计算签名
        from Crypto.Signature import PKCS1_v1_5
        from Crypto.Hash import SHA256
        from Crypto.PublicKey import RSA
        # key = RSA.importKey(open(private_key_path).read())
        key = RSA.importKey(key_pem)
        signer = PKCS1_v1_5.new(key)
        signature = signer.sign(SHA256.new(unsigned_string.encode("utf8")))
        # base64 编码，转换为unicode表示并移除回车
        sign = base64.encodebytes(signature).decode("utf8").replace("\n", "")
        return sign



    def decrypt(self,nonce, ciphertext, associated_data,orgid):
        '''AEAD_AES_256_GCM解密'''
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import base64
        key = orgid
        key_bytes = str.encode(key)
        nonce_bytes = str.encode(nonce)
        ad_bytes = str.encode(associated_data)
        data = base64.b64decode(ciphertext)
        aesgcm = AESGCM(key_bytes)
        resp=aesgcm.decrypt(nonce_bytes, data, ad_bytes)

        return resp


    def mini_pay(self, sub_appid, sub_mch_id, order_id, money, openid, notify_url,serial_number,key_pem):
        '''普通商户小程序支付v3'''
        params = {
            'appid': sub_appid,  # 商应用ID
            'mchid': sub_mch_id,  # 直连商户的商户号
            "description": '充值',  # 支付说明
            'out_trade_no': order_id,  # 生成的订单号
            'amount': {"total": money, "currency": "CNY"},  # 标价金额
            'notify_url': notify_url,
            'payer': {"openid": openid},  # 支付者
        }
        params = json.dumps(params)
        now_date = str(int(time.time()))
        nonce_str = ''.join(random.sample(string.ascii_letters + string.digits, 30))
        sign_str = self.sign_str('POST', '/v3/pay/transactions/jsapi', now_date, nonce_str, params)
        # signature = self.sign_string('./apiclient_key.pem', sign_str)
        signature = self.sign_string(key_pem, sign_str)
        Authorization = 'WECHATPAY2-SHA256-RSA2048 mchid="%s",nonce_str="%s",signature="%s",timestamp="%s",serial_no="%s"' % (sub_mch_id, nonce_str, signature, now_date, serial_number)
        response = requests.post('https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi', data=params,
                                 headers={"Authorization": Authorization,
                                          "Content-Type": "application/json", "Accept": "application/json",
                                          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36"})

        re_dict = json.loads(response.text)
        print(re_dict)
        re_dict['xml'] = {}
        prepay_id = re_dict.get("prepay_id")
        if prepay_id:
            re_dict['xml']['return_code'] = 'SUCCESS'
            re_dict['xml']['result_code'] = 'SUCCESS'
        else:
            re_dict['xml']['return_code'] = re_dict['code']
            re_dict['xml']['result_code'] = re_dict['code']
            re_dict['xml']['return_msg'] = re_dict['message']
        data = {
            "appId": sub_appid,
            "nonceStr": nonce_str,
            "package": "prepay_id=" + prepay_id,
            "signType": 'RSA',
            "timeStamp": now_date,
        }
        sign_list = [sub_appid, now_date, nonce_str, "prepay_id=" + prepay_id]
        sign_str = '\n'.join(sign_list) + '\n'
        paySign = self.sign_string(key_pem, sign_str)
        data["paySign"] = paySign  # 加入签名
        return re_dict, data


    def refunds_v3(self,transaction_id,out_refund_no,refund,total,mchid,serial_number,key_pem,notify_url=''):
        '''普通商户-申请退款'''
        params = {
            'transaction_id':transaction_id,
            'out_refund_no':out_refund_no,
            'notify_url':notify_url,
            'amount':{
                'refund':refund,
                'total':total,
                'currency':'CNY'
            }
        }

        params = json.dumps(params)

        now_date = str(int(time.time()))
        nonce_str = ''.join(random.sample(string.ascii_letters + string.digits, 30))
        sign_str = self.sign_str('POST', '/v3/refund/domestic/refunds', now_date, nonce_str, params)
        signature = self.sign_string(key_pem, sign_str)
        Authorization = 'WECHATPAY2-SHA256-RSA2048 mchid="%s",nonce_str="%s",signature="%s",timestamp="%s",serial_no="%s"' % (
            mchid, nonce_str, signature, now_date, serial_number)

        response = requests.post('https://api.mch.weixin.qq.com/v3/refund/domestic/refunds', data=params,
                                 headers={"Authorization": Authorization,
                                          "Content-Type": "application/json", "Accept": "application/json",
                                          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36"})
        return response
