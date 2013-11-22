t-10_server
===========

[![Build Status](https://travis-ci.org/jpgneves/t-10_server.png)](https://travis-ci.org/jpgneves/t-10_server)


Server for the T-10 (T minus ten) #spaceapps 2013 project: http://spaceappschallenge.org/project/t-10/

App code at https://github.com/stereoket/T-10

Project by Kate Arkless Gray (@SpaceKate), João Neves (@jpgneves), Ketan Majmudar (@ketan) and Dario Lofish (@dariolofish).

Follow us on @TeeMinus10, and visit us at http://teeminus10.com

Weather data provided by: http://openweathermap.org

ISS location data provided by: http://open-notify.org and Celestrak (http://celestrak.net)

Timezone information provided through GeoNames.org (http://geonames.org).

Powered by Python, with support of the following (awesome) libraries provided by the OSS community:

* PyEphem (http://rhodesmill.org/pyephem/) for computation of ISS passes, times, and sunset/sunrise for a given location.

* Flask (http://flask.pocoo.org/) for providing the web application, together with Flask-RESTful (http://flask-restful.readthedocs.org/en/latest/) to provide a RESTful API.

* Requests (http://docs.python-requests.org/en/latest/) for client-side interfacing with other web services.

How to use
==========
Set up a Python virtualenv and then run the following from the t-10_server directory:

    $ pip install -r requirements.txt
    $ python ./teeminus10_api.py

You can configure options (hostname, port) by editing the teeminus10.config file.
