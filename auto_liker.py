import re
import json
import requests
import robobrowser

import sys

MOBILE_USER_AGENT = "Tinder/7.5.3 (iPhone; iOS 10.3.2; Scale/2.00)"
FB_AUTH = "https://www.facebook.com/v2.6/dialog/oauth?redirect_uri=fb464891386855067%3A%2F%2Fauthorize%2F&display=touch&state=%7B%22challenge%22%3A%22IUUkEUqIGud332lfu%252BMJhxL4Wlc%253D%22%2C%220_auth_logger_id%22%3A%2230F06532-A1B9-4B10-BB28-B29956C71AB1%22%2C%22com.facebook.sdk_client_state%22%3Atrue%2C%223_method%22%3A%22sfvc_auth%22%7D&scope=user_birthday%2Cuser_photos%2Cuser_education_history%2Cemail%2Cuser_relationship_details%2Cuser_friends%2Cuser_work_history%2Cuser_likes&response_type=token%2Csigned_request&default_audience=friends&return_scopes=true&auth_type=rerequest&client_id=464891386855067&ret=login&sdk=ios&logger_id=30F06532-A1B9-4B10-BB28-B29956C71AB1&ext=1470840777&hash=AeZqkIcf-NEW6vBd"

headers = {
    'app_version': '6.9.4',
    'platform': 'ios',
    "content-type": "application/json",
    "User-agent": "Tinder/7.5.3 (iPhone; iOS 10.3.2; Scale/2.00)",
    "Accept": "application/json"
}

host = 'https://api.gotinder.com'

def get_fb_access_token(email, password):
    s = robobrowser.RoboBrowser(user_agent=MOBILE_USER_AGENT, parser="lxml")
    s.open(FB_AUTH)
    f = s.get_form()
    f["pass"] = password
    f["email"] = email
    s.submit_form(f)
    f = s.get_form()
    try:
        s.submit_form(f, submit=f.submit_fields['__CONFIRM__'])
        access_token = re.search(
            r"access_token=([\w\d]+)", s.response.content.decode()).groups()[0]
        print("Acquired fb access token")
        return access_token
    except Exception as ex:
        print("access token could not be retrieved. Check your username and password.")
        print("Official error: %s" % ex)
        return {"error": "access token could not be retrieved. Check your username and password."}

def get_fb_id(access_token):
    response = requests.get("https://graph.facebook.com/me?access_token=" + access_token)
    print("Using fb_id " + response.json()["id"])
    return response.json()["id"]

def auth_with_tinder(fb_token, fb_id):
    response = requests.post(host + '/auth', data=json.dumps({'facebook_token': fb_token, 'facebook_id': fb_id}), headers=headers)
    headers['X-Auth-Token'] = response.json()['token']
    print("Authenticated with tinder")

def get_recs():
    response = requests.get(host + '/user/recs', headers=headers)
    print(response.status_code)
    recs = response.json()
    rec_ids = []
    for rec in recs['results']:
        rec_ids.append(rec['_id'])
    return rec_ids

def get_no_likes():
    response = requests.get(host + '/meta', headers=headers)
    return response.json()['rating']['likes_remaining']

def like(rec):
    response = requests.get(host + '/like/' + rec, headers=headers)
    if response.status_code == 200:
        print("liked " + rec)


if len(sys.argv) != 3:
    print("Usage: python3 " + sys.argv[0] + " fb_email fb_password")
else:
    fb_email = sys.argv[1]
    fb_password = sys.argv[2]

    #get fb user access token
    token = get_fb_access_token(fb_email, fb_password)

    #get fb id
    fb_id = get_fb_id(token)

    #authenticate with tinder
    auth_with_tinder(token, fb_id)

    #get number of available likes
    no_likes = get_no_likes()

    print("You got " + str(no_likes) + " likes remaining")

    while no_likes > 0 :
        recs = get_recs()
        for rec in recs:
            like(rec)
            no_likes = no_likes - 1
