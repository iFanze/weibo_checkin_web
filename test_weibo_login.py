from weibo import APIClient, APIError
from weibo_login import WeiboLogin, WeiboLoginError


APP_KEY = "3226611318"
APP_SECRET = "4f94b19d1d30c6bce2505e69d22cd62e"
CALLBACK_URL = "https://api.weibo.com/oauth2/default.html"

print("start login...")

client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)

code = ''
try:
    code = WeiboLogin("ichen0201@sina.com", "s2013h1cfr", APP_KEY, CALLBACK_URL).get_code()
except WeiboLoginError as e:
    print("Login Fail [%s]: %s" % (e.error_code, e.error))
    exit(1)

print("code: %s" % code)

r = client.request_access_token(code)

access_token = r.access_token
expires_in = r.expires_in

print("token: %s" % access_token)
print("expires in %s" % expires_in)

client.set_access_token(access_token, expires_in)

# print(client.statuses.user_timeline.get())
# print(client.statuses.update.post(status=u'测试OAuth 2.0发微博'))
# print(client.statuses.upload.post(status=u'测试OAuth 2.0带图片发微博', pic=open('/Users/Fanze/Pictures/Wallpapers/4yzPVohNuVI.jpg')))

print(client.place.nearby.pois.get(lat=30.524821, long=114.354375))
# print(client.place.poi_timeline.get(poiid="B2094750D26FA1FD4999"))


# r = client.statuses.user_timeline.get(uid="1689924681")
# for st in r.statuses:
#     print(st.text)
