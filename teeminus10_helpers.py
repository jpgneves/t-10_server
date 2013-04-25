import ephem
import json
import requests
import threading
from datetime import datetime, timedelta

API_URLS = { 'iss': "http://api.open-notify.org/iss/?lat={0}&lon={1}&alt={2}&n={3}",
             'weather': {'city_now': "http://api.openweathermap.org/data/2.5/weather?q={0}",
                         'coord_now': "http://api.openweathermap.org/data/2.5/weather?lat={0}&lon={1}",
                         'city_forecast': "http://api.openweathermap.org/data/2.5/forecast?q={0}"
                     }
         }

ACS_URLS = { 'notify': "https://api.cloud.appcelerator.com/v1/push_notification/notify.json?key={0}",
             'login': "https://api.cloud.appcelerator.com/v1/users/login.json?key={0}",
             'subscribe': "https://api.cloud.appcelerator.com/v1/push_notifications/subscribe.json?key={0}"
         }

TIMERS = {}

def to_decimal(coord):
    '''Convert DDMMSS.SS to DD.MMSSSS'''
    tokens = str(coord).split(":")
    r = abs(int(tokens[0])) + abs(int(tokens[1])/60.0) + abs(float(tokens[2])/3600.0)
    #print r
    return r

def get_nighttime(city, date):
    '''Returns sunset and sunrise times for the given city at date'''
    location = ephem.city(city)
    sun = ephem.Sun()
    location.date = date.date()
    return (location.next_setting(sun).datetime(), location.next_rising(sun).datetime())

class WeatherData():
    def __init__(self, city):
        self.city = city

    def __do_get(self, url):
        r = requests.get(url)
        try:
            return json.loads(r.text)
        except ValueError:
            return {} # Something went wrong!

    def current_cloud_cover(self):
        url = API_URLS['weather']['city_now'].format(self.city)
        data = self.__do_get(url)
        return data['clouds']['all']

    def cloud_forecast(self, date):
        url = API_URLS['weather']['city_forecast'].format(self.city)
        data = self.__do_get(url)
        forecast = data['list']
        least_diff = 9999999999999
        closest_forecast = None
        for f in forecast:
            time_diff = (date - datetime.utcfromtimestamp(f['dt'])).total_seconds()
            if abs(time_diff) < least_diff:
                least_diff = time_diff
                closest_forecast = f
        return closest_forecast['clouds']['all']

class T10Helper():
    '''"Server" for handling alerts, checking weather, what not.'''
    def get_cloud_cover(self, city):
        '''Gets cloud cover in % for the given city'''
        url = API_URLS['weather']['city_search'].format(city)
        print url
        r = requests.get(url)
        try:
            result = json.loads(r.text)
        except ValueError:
            return '0'
        return result['data']['current_condition'][0]['cloudcover']

    def alert_next_passes(self, city, acc_cloud_cover, timeofday, device_id, count):
        '''Sets up alerts for up to the next 10 passes of the ISS over the given city. Alerts will be sent to the device that registered for them'''
        try:
            # Cancel previous timers.
            for t in TIMERS[city]:
                t.cancel()
        except KeyError:
            pass
        finally:
            TIMERS[city] = []
        location = ephem.city(city)
        url = API_URLS['iss'].format(to_decimal(location.lat), to_decimal(location.lon), int(location.elevation), count)
        #print url
        r = requests.get(url)
        result = json.loads(r.text)
        next_passes = result['response']
        # For every pass, set up a trigger for 10 minutes earlier and send it
        # to the 'space' channel
        real_response = []
        for p in next_passes:
            risetime = datetime.utcfromtimestamp(p['risetime'])
            weather_data = WeatherData(city)
            night_time = get_nighttime(city, risetime)
            # Skip if the pass is at the wrong time of day
            if timeofday == 'night' and not (night_time[0] < risetime < night_time[1]):
                print "{0} < {1} < {2} = {3}".format(night_time[0], risetime, night_time[1], (night_time[0] < risetime < night_time[1]))
                continue
            elif timeofday == 'day' and not (night_time[1] <= risetime <= night_time[0]):
                continue
            riseminus10 = risetime - timedelta(minutes=10)
            delay = (riseminus10 - datetime.utcnow()).total_seconds()
            print "Running in {0} seconds...".format(delay)
            def f():
                weather_data = WeatherData(city)
                cloud_cover = weather_data.cloud_cover()
                if cloud_cover <= acc_cloud_cover:
                    print "Cloud cover acceptable"
                    SERVER.push_to_ids_at_channel('space', [device_id], json.dumps({'location': city, 'cloudcover': cloud_cover}))
            t = threading.Timer(delay, f)
            TIMERS[city].append(t)
            t.start()
            cloud_forecast = weather_data.cloud_forecast(datetime.utcfromtimestamp(p['risetime']))
            real_response.append({'location': city, 'time_str': str(risetime), 'time': p['risetime'], 'cloudcover': float(cloud_forecast), 'trigger_time': str(riseminus10)})
            print real_response

        return real_response

class T10ACSHelper():
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
        r = requests.post(ACS_URLS['login'].format(self.key), data=payload)
        self.cookies = r.cookies

    def subscribe_device(self, channel, device_type, device_id):
        try:
            self.clients[channel].append(device_id)
        except KeyError:
            self.clients[channel] = [device_id]
            #print self.clients
        finally:
            url = ACS_URLS['subscribe'].format(self.key)
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
        payload = {'channel':channel, 'to_ids':string_ids, 'payload':json.dumps({'badge':2, 'sound':'default', 'alert':message})}
        url = ACS_URLS['notify'].format(self.key)
        #print url
        r = requests.post(url, data=payload, cookies=self.cookies)
