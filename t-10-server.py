import SimpleHTTPServer
import SocketServer
import ephem
import requests
import json
import string
import threading
from BaseHTTPServer import BaseHTTPRequestHandler
from datetime import datetime, timedelta

# It wouldn't be a hackathon without dirty hacks, right?
PORT = 8000
SERVER = None
TIMERS = {} # {"London": [<Thread>], ...}

def to_decimal(coord):
    tokens = str(coord).split(":")
    r = abs(int(tokens[0])) + abs(int(tokens[1])/60.0) + abs(float(tokens[2])/3600.0)
    print r
    return r

def get_nighttime(city):
    now = datetime.utcnow()
    location = ephem.city(city)
    sun = ephem.Sun()
    location.date = now
    return (location.next_setting(sun).datetime(), location.next_rising(sun).datetime())

class T10Server():
    '''"Server" for handling alerts, checking weather, what not.'''
    def __init__(self):
        self.iss_api = "http://api.open-notify.org/iss/?lat={0}&lon={1}&alt={2}&n={3}"
        self.weather_api = "http://api.worldweatheronline.com/free/v1/weather.ashx?q={0}&format=json&date={1}&key=jr7r87s8x3knpud3ehs5uzue" # Yep, API keys everywhere :(

    def get_cloud_cover(self, city, when='today'):
        '''Gets cloud cover in % for the given city'''
        url = self.weather_api.format(city, when)
        print url
        r = requests.get(self.weather_api.format(city, when))
        try:
            result = json.loads(r.text)
        except ValueError:
            return '0' # We most likely went over quota for the free API
        print result
        return result['data']['current_condition'][0]['cloudcover']

    def alert_next_passes(self, city, acc_cloud_cover, timeofday, device_id, count):
        try:
            for t in TIMERS[city]:
                t.cancel()
        except KeyError:
            pass
        finally:
            TIMERS[city] = []
        location = ephem.city(city)
        url = self.iss_api.format(to_decimal(location.lat), to_decimal(location.lon), int(location.elevation), count)
        print url
        r = requests.get(url)
        result = json.loads(r.text)
        next_passes = result['response']
        # For every pass, set up a trigger for 10 minutes earlier and send it
        # to the 'space' channel
        real_response = []
        for p in next_passes:
            risetime = datetime.utcfromtimestamp(p['risetime'])
            nighttime = get_nighttime(city)
            print timeofday, risetime, nighttime[0], nighttime[1]
            # Skip if the pass is at the wrong time of day
            if timeofday == 'night' and (risetime < nighttime[0] or risetime > nighttime[1]):
                continue
            elif timeofday == 'day' and (risetime >= nighttime[0] or risetime <= nighttime[1]):
                continue
            riseminus10 = risetime - timedelta(minutes=10)
            delay = (riseminus10 - datetime.utcnow()).total_seconds()
            print "Running in {0} seconds...".format(delay)
            def f():
                cloud_cover = self.get_cloud_cover(city)
                if float(cloud_cover) <= float(acc_cloud_cover):
                    print "Cloud cover acceptable"
                    SERVER.push_to_ids_at_channel('space', [device_id], json.dumps({'location': city, 'cloudcover': cloud_cover}))
            t = threading.Timer(delay, f)
            TIMERS[city].append(t)
            t.start()
            cloud_forecast = self.get_cloud_cover(city, str(datetime.utcfromtimestamp(p['risetime']).date()))
            real_response.append({'location': city, 'time_str': str(risetime), 'time': p['risetime'], 'cloudcover': float(cloud_forecast), 'trigger_time': str(riseminus10)})

        return real_response

    def wave(self, city):
        '''Send a "wave" message, so they can start waving to the ISS!'''
        try:
            for t in TIMERS[city]:
                t.cancel()
        except KeyError:
            pass
        finally:
            TIMERS[city] = []
        if city == "iss":
            #push to space instead :P
            channel = 'space'
        else:
            channel = 'earth'
        SERVER.push_to_channel(channel, json.dumps({'location': city}))


class T10RequestHandler(BaseHTTPRequestHandler):
    '''Dirty quick request handler'''
    def do_POST(self):
        tokens = self.path.split('/')[1:]
        print tokens
        if len(tokens) >= 3 and tokens[0] == "subscribe":
            # /subscribe/earth/ios/DEVICEID
            SERVER.subscribe_device(tokens[1], tokens[2], tokens[3])
            self.send_response(200)
            message = "ok"
        elif len(tokens) >= 4 and tokens[0] == "add_event":
            # /add_event/London/CLOUDCOVER/TIMEOFDAY/DEVICEID
            passes = T10Server().alert_next_passes(tokens[1], tokens[2], tokens[3], tokens[4], 10)
            self.send_response(200)
            message = json.dumps(passes)
        elif len(tokens) >= 2 and tokens[0] == "wave":
            # /wave/London
            T10Server().wave(tokens[1])
            self.send_response(200)
            message = "ok"
        else:
            self.send_response(418) # We're a teapot :D
            message = "I'm a teapot"
        self.end_headers()
        self.wfile.write(message)
        return

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
            self.push_to_ids_at_channel(channel, self.clients[channel], message)
        except KeyError:
            return

    def push_to_ids_at_channel(self, channel, ids, message):
        print "Pushing {0} to {1}".format(message, channel)
        string_ids = ",".join(ids)
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
