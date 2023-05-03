from dash import Dash, html, Input, Output
import dash_daq as daq
import dash
import dash_bootstrap_components as dbc
import Freenove_DHT as DHT
import time
import paho.mqtt.client as mqtt
from dash import dcc
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import paho.mqtt.client as mqtt_client

from email.header import decode_header
import paho.mqtt.subscribe as subscribe

import imaplib
from datetime import datetime
import threading
import email
import time
import sqlite3


import RPi.GPIO as GPIO
from time import sleep

username = 'Unknown'
rfid = 'User RFID'
desirePic = 'https://media.tenor.com/w-ddWw98CpIAAAAd/asta-black-clover.gif'
desireTemperature = 15
desireHumidity = 40
desireLight = 1000



last_username = None
light_in = 1000
last_rfid_message = None



DHTPin = 17  # define the pin of DHT11
LEDPin = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(LEDPin, GPIO.OUT)
GPIO.setup(DHTPin, GPIO.IN)

email_sent = False
email_sent2 = False
email_received = False
GPIO.setwarnings(False)
last_email_received_time = 0
fan_should_be_on = False

app = Dash(__name__, external_stylesheets=['./assets/dashboard.css'])


def on_message(client, userdata, msg):
    global light_in, last_rfid_message
    if msg.topic == "lightIntensity":
        light_in = int(msg.payload.decode("utf-8"))
    elif msg.topic == "IoTLab/rfid":
        last_rfid_message = msg.payload.decode("utf-8")

mqtt_client_instance = mqtt_client.Client()
mqtt_client_instance.on_message = on_message
mqtt_client_instance.connect("192.168.2.67")
mqtt_client_instance.subscribe("lightIntensity")
mqtt_client_instance.subscribe("IoTLab/rfid")
mqtt_client_instance.loop_start()


def readUser():
    global last_rfid_message
    global userNumber
    global sentRFID
    global last_username
    userNumber = str(last_rfid_message)
    print(userNumber)

    dbconnect = sqlite3.connect("iotproject.db")
    dbconnect.row_factory = sqlite3.Row
    cursor = dbconnect.cursor()
    select_stmt = "SELECT * FROM user WHERE user_rfid = ?"
    cursor.execute(select_stmt, (userNumber,))

    for row in cursor:

        if userNumber == row['user_rfid']:
            rfid = row['user_rfid']
            username = row['username']
            desirePic = row['user_pic']
            desireTemperature = row['user_temp']
            desireHumidity = row['user_humid']
            desireLight = row['user_light']

            if username != last_username:  
                sendEmailRFID(username)
                last_username = username  

            print("User: "+str(userNumber), username,
                  str(desireTemperature), str(desireHumidity)+" ")
            return userNumber, username, desirePic, desireTemperature, desireHumidity, desireLight

    username = 'Unknown'
    rfid = 'User RFID'
    desirePic = 'https://media.tenor.com/w-ddWw98CpIAAAAd/asta-black-clover.gif'
    desireTemperature = 15
    desireHumidity = 40
    desireLight = 1000
    sentRFID = False

    return userNumber, username, desirePic, desireTemperature, desireHumidity, desireLight
    dbconnect.close()


def readLight():
    global light_in
    return light_in


    

def control_LED_and_send_email(light_intensity):
    global email_sent2
    if light_intensity < desireLight and not email_sent2:
        GPIO.output(LEDPin, GPIO.HIGH)
        sendLightEmail2()
        print("mail sent")
        email_sent2 = True
    elif light_intensity >= desireLight:
        GPIO.output(LEDPin, GPIO.LOW)
        email_sent2 = False


def sendEmailRFID(username):

    smtp_server = "smtp-mail.outlook.com"
    port = 587  # For starttls
    sender_email = "iot_maxter77@outlook.com"
    receiver_email = "iot_maxter77@outlook.com"
    password = "Itachi123&"
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    TEXT = "User " + username +  " entered at " + current_time + " time"

    subject = "User entry notification"
    body = TEXT

    # Create the MIME object
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    # Attach the body to the email
    msg.attach(MIMEText(body, "plain"))

    # Send the email
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls()
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

def check_email_reply():
    global email_received
    imap_url = "imap-mail.outlook.com"
    email_address = "iot_maxter77@outlook.com"
    password = "Itachi123&"
    imap = imaplib.IMAP4_SSL(imap_url)
    # imap.starttls()  # Remove this line
    imap.login(email_address, password)
    imap.select("Inbox")
    # Search for the latest email
    result, data = imap.uid('search', None, "ALL")
    latest_email_uid = data[0].split()[-1]
    result, data = imap.uid('fetch', latest_email_uid, '(RFC822)')
    raw_email = data[0][1]
    email_message = email.message_from_bytes(raw_email)
    fan_on = False
    # Check if the body of the email contains "YES"
    if email_message.get_content_maintype() == 'multipart':
        for part in email_message.get_payload():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True)
                try:
                    body = body.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        body = body.decode('iso-8859-1')
                    except UnicodeDecodeError:
                        body = body.decode('utf-16')
                if "YES" in body.upper() and not email_received:
                    email_received = True
                    fan_on = True
    imap.close()
    return fan_on


sidebar_style = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '200px',
    'padding': '20px',
    'background-color': 'grey',  # change the background color
    'color': 'white'  # change the font color
}


app.layout = html.Div([
    html.Div(
        id="sidebar",
        style=sidebar_style,
        children=[
            html.H2('User Info'),
            html.Img(id='my-pic', src=desirePic,
                     style={'width': '100px', 'heigth': '100px', 'border-radius': '50px'}),
            html.P(id='my-rfid', children=[rfid]),
            html.H2(id='my-username', children=[username]),
            html.Hr(),
            daq.NumericInput(
                id='my-light-desire',
                label='Desired Light',
                value=desireLight,
                
            ),
            html.Hr(),
            daq.NumericInput(
                id='my-temp-desire',
                label='Desired Temperature',
                value=desireTemperature,
           ),
            html.Hr(),
            daq.NumericInput(
                id='my-humid-desire',
                label='Desired Humidity',
                value=desireHumidity,
            ),

        ]
    ),

    html.Div(
        id="app-Header",
        children=[
            html.Div('IOT Masters',
                     className="app-header--title")
        ]
    ),

        

    html.Div(
        dcc.Interval(
            id='interval-component',
            interval=2000,
            n_intervals=0
        )
    ),





    html.Div(
        id="switch_area",
        children=[
            html.H2('Temperature', className="tempTitle"),
            daq.Thermometer(
                id='temp-indicator',
                min=0,
                max=105,
                value=5,
                showCurrentValue=True,
                units="C",
                style={
                    'margin-bottom': '5%'
                }
            ),

        ]
    ),
    html.Div(
        id="humidity-area",
        children=[
            html.H2('Humidity', className="tempTitle"),
            daq.Gauge(
                id='humidity-indicator',
                color={"gradient": True, "ranges": {
                    "green": [0, 6], "yellow":[6, 8], "red":[8, 10]}},
                value=2,
                max=100,
                min=0,
                showCurrentValue=True,
                units="%",
                style={
                    'margin-bottom': '5%'
                }
            ),

        ]
    ),



    html.Div(
        id="fan-area",
        children=[
            html.H2('Fan Status'),

            html.Div(children=[
                html.Img(
                    id='FanOn', src='https://cdn.dribbble.com/users/3892547/screenshots/11096911/ezgif.com-resize.gif', ),

            ]),
            html.Div(children=[
                html.Img(
                    id='FanOff', src='https://cdn-icons-png.flaticon.com/512/925/925993.png', ),
            ]),
            daq.Indicator(
                id='fan-indicator',
                value=True,
                color="#00cc96"
            )
        ]
    ),



    html.Div(
        id="light-intensity-area",
        children=[
            html.H2('Light Intensity', className="tempTitle"),
            daq.Gauge(
                id='light-intensity-indicator',
                color={"gradient": True, "ranges": {
                    "green": [0, 300], "yellow":[300, 600], "red":[600, 1023]}},
                value=300,
                max=1023,
                min=0,
                showCurrentValue=True,
                units="",
                style={
                    'margin-bottom': '5%'
                }
            ),
            html.Div(children=[
                html.Img(id='my-lightBulbOn', src='https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Light_bulb_%28yellow%29_icon.svg/1200px-Light_bulb_%28yellow%29_icon.svg.png',
                         style={'display': 'none', 'height': '100px', 'width': '100px', 'margin-top': '-60px', 'margin-left': '70px'}),
            ]),
            html.Div(children=[
                html.Img(id='my-lightBulbOff', src='https://cdn-icons-png.flaticon.com/512/18/18310.png',
                         style={'display': 'block', 'height': '100px', 'width': '100px', 'margin-top': '-60px', 'margin-left': '70px'}),
            ]),

            html.Div(
                id="email-notification",
                children=[
                    html.P("", id="email-notification-text")
                ],
                className="email-notification",
            ),
            html.Div(
        dcc.Interval(
        id='light-intensity-interval',
        interval=2000,  # in milliseconds
        n_intervals=0
    )

),

        html.Div(
        dcc.Interval(
        id='tempAndHumid-intensity-interval',
        interval=2000,  # in milliseconds
        n_intervals=0
    )
    
),

html.Div(
        id="switch_area2",
        children=[
            html.H2('LED SWITCH'),
            daq.BooleanSwitch(id='our-boolean-switch', on=False),
            html.Div(id='boolean-switch-result'),
             html.Div(children=[
                        html.Img(id='my-lightBulbOn2',src='https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Light_bulb_%28yellow%29_icon.svg/1200px-Light_bulb_%28yellow%29_icon.svg.png',

                        ),
                    ]),
        html.Div(children=[
                        html.Img(id='my-lightBulbOff2',src='https://cdn-icons-png.flaticon.com/512/18/18310.png',),
                    ]),


            daq.Indicator(
                id='led-indicator',
                value=True,
                color="#00cc96"
            )
        ]
    ),



        ]
    ),




    html.Div(id='hidden-div', style={'display': 'none'}),

])





@app.callback(Output('light-intensity-indicator', 'value'),
              Input('light-intensity-interval', 'n_intervals'))
def update_light_intensity(value):
    light_intensity = readLight()
    control_LED_and_send_email(light_intensity)
    return light_intensity



@app.callback(Output('my-username', 'children'),
              Output('my-pic', 'src'),
              Output('my-temp-desire', 'value'),
              Output('my-light-desire', 'value'),
              Output('my-humid-desire', 'value'),
              Output('my-rfid', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_output(n):
    userNumber, username, desirePic, desireTemp, desireHumidity, desireLight = readUser()
    return username, desirePic, desireTemp, desireLight, desireHumidity, userNumber

@app.callback(
    Output('boolean-switch-result', 'children'),
    Output('led-indicator', 'value'),
    Output('my-lightBulbOn2', 'style'),
    Output('my-lightBulbOff2', 'style'),
    Input('our-boolean-switch', 'on')
)
def update_output(value):
    turnOnLED(True) if value else turnOnLED(False)
    on_style = {'width': '100px', 'height': '100px', 'display': 'inline-block'} if value else {'display': 'none'}
    off_style = {'width': '100px', 'height': '100px', 'display': 'inline-block'} if not value else {'display': 'none'}
    return ('LED is on', 'LED is off') [not value], value, on_style, off_style
    
def turnOnLED(active):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(13,GPIO.OUT)

    if active == True:
        GPIO.output(13, GPIO.HIGH)
    if active == False:
        GPIO.output(13, GPIO.LOW)


@app.callback(
    Output('humidity-indicator', 'value'),
    Input('tempAndHumid-intensity-interval', 'n_intervals')
)
def update_humidity(value):
    dht = DHT.DHT(DHTPin)  # create a DHT class object
    for i in range(0, 15):
        # read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
        chk = dht.readDHT11()
        # read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
        if (chk is dht.DHTLIB_OK):
            print("Humidity : %.2f, \n" % (dht.humidity))
            break
        time.sleep(0.1)
    return dht.humidity


@app.callback(
    Output('temp-indicator', 'value'),
    Input('interval-component', 'n_intervals')
)
def update_output(value):
    global email_sent
    dht = DHT.DHT(DHTPin)  # create a DHT class object
    for i in range(0, 15):
        chk = dht.readDHT11()
        if chk is dht.DHTLIB_OK:
            print("Temperature : %.2f, \n" % (dht.temperature))
            break
        time.sleep(0.1)
    if (dht.temperature > 18) and not email_sent:
        send_email()
        email_sent = True
        print("Email sent!")
    elif dht.temperature <= 18:
        email_sent = False
    return dht.temperature




@app.callback(
    Output('email-notification-text', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_email_notification(value):
    global email_sent2
    if email_sent2:
        return "Email was sent."
    else:
        return ""



@app.callback(
    Output('my-lightBulbOn', 'style'),
    Output('my-lightBulbOff', 'style'),
    Input('interval-component', 'n_intervals')
)

def update_lightbulb_images(value):
    led_on = GPIO.input(LEDPin)
    if led_on:
        return {'display': 'block', 'height': '100px', 'width': '100px', 'margin-top': '-60px', 'margin-left': '70px'}, {'display': 'none', 'height': '100px', 'width': '100px', 'margin-top': '-60px', 'margin-left': '70px'}
    else:
        return {'display': 'none', 'height': '100px', 'width': '100px', 'margin-top': '-60px', 'margin-left': '70px'}, {'display': 'block', 'height': '100px', 'width': '100px', 'margin-top': '-60px', 'margin-left': '70px'}





@app.callback(
    Output('FanOn', 'style'),
    Output('FanOff', 'style'),
    Output('fan-indicator', 'value'),
    Input('interval-component', 'n_intervals')
)
def update_fan(value):
    global email_sent, email_received, last_email_received_time, fan_should_be_on
    fan_on = check_email_reply()

    if fan_on:
        fan_should_be_on = True
        last_email_received_time = time.time()
    elif time.time() - last_email_received_time > 10:
        email_received = False
        fan_should_be_on = False

    if fan_should_be_on:
       
        return {'display': 'block', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, {'display': 'none', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, True
    else:
        return {'display': 'none', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, {'display': 'block', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, False


def send_email():
    smtp_server = "smtp-mail.outlook.com"
    port = 587  # For starttls
    sender_email = "iot_maxter77@outlook.com"
    receiver_email = "iot_maxter77@outlook.com"
    password = "Itachi123&"

    subject = "Subject: Turn on FAN"
    body = "The current temperature is over 24 Would you like to turn on the fan?"

    # Create the MIME object
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    # Attach the body to the email
    msg.attach(MIMEText(body, "plain"))

    # Send the email
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls()
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())


def sendLightEmail2():

    smtp_server = "smtp-mail.outlook.com"
    port = 587  # For starttls
    sender_email = "iot_maxter77@outlook.com"
    receiver_email = "iot_maxter77@outlook.com"
    password = "Itachi123&"
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    TEXT = "Light is now ON \n\nAt: " + current_time + " time"

    subject = "Subject: Light is on"
    body = TEXT

    # Create the MIME object
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    # Attach the body to the email
    msg.attach(MIMEText(body, "plain"))

    # Send the email
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls()
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())


if __name__ == '__main__':
    app.run_server(debug=True)
