import SimpleHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import SocketServer
import requests
import json

# It wouldn't be a hackathon without dirty hacks, right?
PORT = 8000
SERVER = None

class T10RequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        tokens = self.path.split('/')[1:]
        print tokens
        if len(tokens) >= 3 and tokens[0] == "subscribe":
            SERVER.subscribe_device("general", tokens[1], tokens[2])
        SERVER.push_to_channel("general", "Foo!")

class ACSServer():
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
    #a.push_to_channel("general", "Hello!")
