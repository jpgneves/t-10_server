import SimpleHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import SocketServer
import ephem
import requests
import json
import string

# It wouldn't be a hackathon without dirty hacks, right?
PORT = 8000
SERVER = None

def to_decimal(coord):
    tokens = str(coord).split(":")
    r = abs(int(tokens[0])) + abs(int(tokens[1])/60.0) + abs(float(tokens[2])/3600.0)
    print r
    return r

class T10Server():
    '''"Server" for handling alerts, checking weather, what not.'''
    def __init__(self):
        self.iss_api = "http://api.open-notify.org/iss/?lat={0}&lon={1}&alt={2}&n={3}"
        self.weather_api = "http://api.worldweatheronline.com/free/v1/weather.ashx?q=%%location%%&format=json&date=today&key=jr7r87s8x3knpud3ehs5uzue"

    def get_cloud_cover(self, city):
        r = requests.get(string.replace(self.weather_api, "%%location%%", city))
        result = json.loads(r.text)
        print result
        return result['data']['current_condition'][0]['cloudcover']

    def get_next_passes(self, city, count):
        location = ephem.city(city)
        url = self.iss_api.format(to_decimal(location.lat), to_decimal(location.lon), int(location.elevation), count)
        print url
        r = requests.get(url)
        result = json.loads(r.text)
        next_passes = result['response']
        return next_passes


class T10RequestHandler(BaseHTTPRequestHandler):
    '''Dirty quick request handler'''
    def do_POST(self):
        tokens = self.path.split('/')[1:]
        print tokens
        if len(tokens) >= 3 and tokens[0] == "subscribe":
            SERVER.subscribe_device(tokens[1], tokens[2], tokens[3])
            SERVER.push_to_channel(tokens[1], "Foo!")
            s = T10Server()
            s.get_cloud_cover("London")
            s.get_next_passes("London", 5)
        self.send_response(200)

class ACSServer():
    '''Handles connections to Appcelerator Cloud Services and does push notifications'''
    def __init__(self, user, password, key):
        self.key = key
        self.user = user
        self.password = password
        self.__login()
        self.clients = {}

    def __login(self):
        '''Need to login to appcelerator'''
        payload = {'login':self.user, 'password':self.password}
        r = requests.post("https://api.cloud.appcelerator.com/v1/users/login.json?key=" + self.key, data=payload)
        self.cookies = r.cookies

    def subscribe_device(self, channel, device_type, device_id):
        try:
            self.clients[channel].append(device_id)
        except KeyError:
            self.clients[channel] = [device_id]
            print self.clients
        finally:
            url = "https://api.cloud.appcelerator.com/v1/push_notifications/subscribe.json?key=vjCQ6KRqplmkektlpbEjiDQ2nYReubkP"
            payload = {'type':device_type, 'device_id':device_id, 'channel':'channel'}
            r = requests.post(url, data=payload, cookies=self.cookies)

    def push_to_channel(self, channel, message):
        try:
            string_ids = ",".join(self.clients[channel])
        except KeyError:
            return
        print string_ids
        payload = {'channel':channel, 'to_ids':string_ids, 'payload':json.dumps({'badge':2, 'sound':'default', 'alert':message})}
        url = "https://api.cloud.appcelerator.com/v1/push_notification/notify.json?key=" + self.key
        print url
        r = requests.post(url, data=payload, cookies=self.cookies)
        print r.text


if __name__ == '__main__':
    handler = T10RequestHandler
    httpd = SocketServer.TCPServer(("", PORT), handler)

    SERVER = ACSServer("t10admin", "3Wd2EXRfQV", "mIuLKF9z8RCMJsYKPsl15nmfqCbSBdWZ")

    httpd.serve_forever()
