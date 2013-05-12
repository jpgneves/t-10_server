from flask import Flask
from flask import request
from flask import session
from flask_oauth import OAuth
#from flask_login import LoginManager, current_user
from flask.ext.restful import reqparse, abort, Api, Resource
import flask.ext.restful as restful
import json
import types
from ConfigParser import SafeConfigParser
from teeminus10_helpers import T10Helper, T10ACSHelper

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
t10_helper = T10Helper(acs_helper)

class Alert(Resource):
    def get(self):
        return {'response': []}
    def put(self):
        data = request.json
        if data is not None:
            try:
                city = data['location']['city']
                coord = (0.0, 0.0)
            except KeyError:
                city = None
                coord = (data['location']['latitude'], data['location']['longitude'])
            finally:
                device_id = data['device_id']
                next_passes = t10_helper.alert_next_passes(data['max_cloud_cover'], data['time_of_day'], device_id, city=city, coord=coord)
                print next_passes
                return {'response': next_passes}
    def delete(self, alert_id):
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
