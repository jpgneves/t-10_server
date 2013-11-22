from flask import Flask
from flask import request
from flask import session
from flask_oauth import OAuth
#from flask_login import LoginManager, current_user
from flask.ext.restful import reqparse, abort, Api, Resource
import flask.ext.restful as restful
import json
import logging
import logging.handlers
import types
from ConfigParser import SafeConfigParser
from teeminus10_helpers import T10Helper, T10ACSHelper, T10TZHelper

logger = logging.getLogger('teeminus10')
logger.setLevel(logging.DEBUG)

rfh = logging.handlers.RotatingFileHandler('teeminus10.log', maxBytes=10*1024*1024, backupCount=10) # 10 MB per log file
rfh.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
rfh.setFormatter(formatter)

logger.addHandler(rfh)

app = Flask("T-10")
api = restful.Api(app)

#login_manager = LoginManager()
#login_manager.init_app(app)

#oauth = OAuth()
#twitter = oauth.remote_app('twitter',
#    base_url='https://api.twitter.com/1/',
#    request_token_url='https://api.twitter.com/oauth/request_token',
#    access_token_url='https://api.twitter.com/oauth/access_token',
#    authorize_url='https://api.twitter.com/oauth/authenticate',
#    consumer_key='<your key here>',
#    consumer_secret='<your secret here>'
#)

config = SafeConfigParser({'host': '0.0.0.0', 'port': '5000', 'debug': 'False'})
config.read("./teeminus10.config")
acs_helper = T10ACSHelper(config.get('ACS', 'user'), config.get('ACS', 'password'), config.get('ACS', 'key'))
tz_helper = T10TZHelper(config.get('Geonames', 'user'))
t10_helper = T10Helper(acs_helper, tz_helper)

class Alert(Resource):
    def get(self):
        return {'response': []}
    def put(self):
        data = request.json
        if data is not None:
            city = ""
            coord = (0.0, 0.0)
            try:
                city = data['location']['city']
            except KeyError:
                coord = (data['location']['latitude'], data['location']['longitude'])
            finally:
                device_id = data['device_id']
                next_passes = t10_helper.alert_next_passes(data['max_cloud_cover'], data['time_of_day'], device_id, city=city, coord=coord)
                logging.debug("Request for passes: {0}".format(next_passes))
                return {'response': next_passes}
    def delete(self):
        data = request.json
        t10_helper.delete_alerts(data['location']['city'])
        return {'response': 'ok'}

class Wave(Resource):
    def post(self, alert_id=None):
        if alert_id is None:
            self.do_wave_back()
        else:
            self.do_wave_start(alert_id)

    def do_wave_start(self):
        pass

    def do_wave_back(self):
        pass

class ISSPass(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lat', type=float, default=0.0)
        parser.add_argument('lon', type=float, default=0.0)
        parser.add_argument('alt', type=int, default=0)
        parser.add_argument('count', type=int, default=10)

        args = parser.parse_args()

        return t10_helper.get_next_passes(args['lat'], args['lon'], args['alt'], args['count'], True)

class ISSLocation(Resource):
    def get(self):
        """Returns the current location of the ISS

        :statuscode 200: A response object is returned as follows

          .. sourcecode:: js

             {
               'latitude': LAT,
               'longitude': LON
             }

        """
        return t10_helper.get_current_iss_location()

api.add_resource(ISSLocation, '/location')
api.add_resource(ISSPass, '/passes')
api.add_resource(Alert, '/alerts', '/alerts/<int:alert_id>')
api.add_resource(Wave, '/alerts/wave/start/<int:alert_id>', '/alerts/wave/back')

#@app.route('/login')
#def login():
#    if current_user.is_authenticated():
#        return redirect('/')

if __name__ == '__main__':
    host = config.get('TeeMinus10', 'host')
    port = int(config.get('TeeMinus10', 'port'))
    debug = bool(config.get('TeeMinus10', 'debug'))
    app.run(host=host, port=port, debug=debug)
