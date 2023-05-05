from dash import Dash, html, Input, Output
import dash_daq as daq
import dash
import dash_bootstrap_components as dbc
import Freenove_DHT as DHT
import time
import paho.mqtt.client as mqtt
from dash import dcc
import bluetooth
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
#User Info when User is not loged in 
username = 'Unknown'
rfid = 'User RFID'
desirePic = 'https://media.tenor.com/w-ddWw98CpIAAAAd/asta-black-clover.gif'
desireTemperature = 15
desireHumidity = 40
desireLight = 300



last_username = None
light_in = 0
last_rfid_message = None



DHTPin = 25  # define the pin of DHT11
LEDPin = 19
MotorEnable = 27
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LEDPin, GPIO.OUT)

GPIO.setup(MotorEnable, GPIO.OUT)


email_sent = False
email_sent2 = False
scanned = False
email_received = False
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
mqtt_client_instance.connect("192.168.72.197")
mqtt_client_instance.subscribe("lightIntensity")
mqtt_client_instance.subscribe("IoTLab/rfid")
mqtt_client_instance.loop_start()


def readUser():
    global last_rfid_message
    global userNumber
    global sentRFID
    global last_username
    global desireTemperature
    global desireHumidity
    global desireLight
    userNumber = str(last_rfid_message)
    print(userNumber)
    
    #store the info taken by the card into the database

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
    desireLight = 300
    sentRFID = False

    return userNumber, username, desirePic, desireTemperature, desireHumidity, desireLight
    dbconnect.close()


def readLight():
    global light_in
    return light_in



def get_nearby_bluetooth_devices():
    global bluetooth, scanned
    print("Scanning for bluetooth devices:")
    devices = bluetooth.discover_devices(lookup_names = True, lookup_class = True)
    number_of_devices = len(devices)
    print(number_of_devices,"devices found")
    scanned = True

    return number_of_devices
    

def control_LED_and_send_email(light_intensity):
    global email_sent2
    print("light_intensity : ") 
    print(light_intensity) 
    print("desire : ") 
    print(desireLight) 

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
    sender_email = "iot_maxter2024@outlook.com"
    receiver_email = "iot_maxter2024@outlook.com"
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
    email_address = "iot_maxter2024@outlook.com"
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
            daq.LEDDisplay(
                id='my-light-desire',
                label='Desired Light',
                value=desireLight,
                
            ),
            html.Hr(),
            daq.LEDDisplay(
                id='my-temp-desire',
                label='Desired Temperature',
                value=desireTemperature,
           ),
            html.Hr(),
            daq.LEDDisplay(
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
            interval=3000,
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
                value=20,
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
                value=20,
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
            # daq.PowerButton(id='power-button', on=False),
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




        ]
    ),


# html.Div(
#     id="bluetooth-area",
#     children=[
#         html.H2('Nearby Bluetooth Devices'),
#         html.Div(id='bluetooth-devices-count'),
#     ]
# ),

# dcc.Interval(
#     id='bluetooth-update-interval',
#     interval=10000,  # in milliseconds
#     n_intervals=0
# ),

    html.Div(id='hidden-div', style={'display': 'none'}),

])









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

@app.callback(Output('light-intensity-indicator', 'value'),
              Input('light-intensity-interval', 'n_intervals'))
def update_light_intensity(value):
    light_intensity = readLight()
    control_LED_and_send_email(light_intensity)
    return light_intensity

@app.callback(
    Output('humidity-indicator', 'value'),
    Output('temp-indicator', 'value'),
    Input('tempAndHumid-intensity-interval', 'n_intervals')
)
def update_humidity(value):
    global email_sent
    dht = DHT.DHT(DHTPin)  
    for i in range(0, 15):
        chk = dht.readDHT11()
        if (chk is dht.DHTLIB_OK):
            print("Humidity : %.2f, \t Temperature : %.2f \n"%(dht.humidity,dht.temperature))
            break
    if (dht.temperature > desireTemperature) and not email_sent:
        send_email()
        email_sent = True
        print("Email sent!")
    elif dht.temperature <= desireTemperature:
        email_sent = False
    return dht.humidity, dht.temperature





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
        GPIO.output(MotorEnable, GPIO.HIGH)
       
        return {'display': 'block', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, {'display': 'none', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, True
    else:
        GPIO.output(MotorEnable, GPIO.LOW)
        return {'display': 'none', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, {'display': 'block', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, False


# def toggle_fan(n_clicks, fan_indicator):
#     if n_clicks > 0:
#         if fan_indicator:
#             GPIO.output(MotorEnable, GPIO.LOW)
#             return {'display': 'none', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, {'display': 'block', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, False
#         else:
#             GPIO.output(MotorEnable, GPIO.HIGH)
#             return {'display': 'block', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, {'display': 'none', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, True
#     else:
#         return dash.no_update, dash.no_update, dash.no_update

# @app.callback(
#     Output('bluetooth-devices-count', 'children'),
#     Input('bluetooth-update-interval', 'n_intervals')
# )
# def update_bluetooth_devices_count(value):
#     nearby_devices = get_nearby_bluetooth_devices()
#     return nearby_devices
    
def send_email():
    smtp_server = "smtp-mail.outlook.com"
    port = 587  # For starttls
    sender_email = "iot_maxter2024@outlook.com"
    receiver_email = "iot_maxter2024@outlook.com"
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
    sender_email = "iot_maxter2024@outlook.com"
    receiver_email = "iot_maxter2024@outlook.com"
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
