t-10_server
===========

Server for the T-10 (T minus ten) #spaceapps 2013 project: http://spaceappschallenge.org/project/t-10/

App code at https://github.com/stereoket/T-10

Project by Kate Arkless Gray (@SpaceKate), João Neves (@jpgneves), Ketan Majmudar (@stereoket) and Dario Lofish (@dariolofish).

Follow us on @TeeMinus10

Weather data provided by: http://openweathermap.org

ISS location data provided by: http://open-notify.org and Celestrak (http://celestrak.net)

How to use
==========
Set up a Python virtualenv and then run the following from the t-10_server directory:

    $ pip install -r requirements.txt
    $ python ./teeminus10_api.py

You can configure options (hostname, port) by editing the teeminus10.config file.
