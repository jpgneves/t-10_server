from flask import Flask
from flask import request
from flask import session
from flask_oauth import OAuth
#from flask_login import LoginManager, current_user
from flask.ext.restful import reqparse, abort, Api, Resource
import flask.ext.restful as restful
import json
import types
from ConfigParser import ConfigParser
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

t10_helper = T10Helper()
config = ConfigParser()
config.read("teeminus10.config")
acs_helper = T10ACSHelper(config.get('ACS', 'user'), config.get('ACS', 'password'), config.get('ACS', 'key'))

class Alert(Resource):
    def get(self):
        print request.headers
        return {'response': [{'id': 3}]}
    def put(self):
        data = request.json
        if data is not None:
            try:
                city = data['location']['city']
            except KeyError:
                city = "Stockholm" # Default while I don't fix this.
            finally:
                return {'response': t10_helper.alert_next_passes(city, data['max_cloud_cover'], data['time_of_day'], "foo", 10)}
    def delete(self, alert_id):
        return {'response': 'ok'}

api.add_resource(Alert, '/alerts', '/alerts/<int:alert_id>')

#@app.route('/login')
#def login():
#    if current_user.is_authenticated():
#        return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
