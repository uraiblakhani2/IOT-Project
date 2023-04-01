from dash import Dash, html, Input, Output
import dash_daq as daq
import Freenove_DHT as DHT
import time
import paho.mqtt.client as mqtt
from dash import dcc
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
import imaplib
import threading
import email
import time

import RPi.GPIO as GPIO
from time import sleep


DHTPin = 23  # define the pin of DHT11


email_sent = False
email_received = False
GPIO.setwarnings(False)
last_email_received_time = 0
fan_should_be_on = False


app = Dash(__name__, external_stylesheets=['./assets/dashboard.css'])


mqtt_client = mqtt.Client("dashboard")
mqtt_server = "192.168.2.67"
# Set your MQTT username and password here
mqtt_client.username_pw_set("username", "password")
mqtt_client.connect(mqtt_server, 1883)

light_intensity = 0


def on_message(client, userdata, message):
    global light_intensity
    light_intensity = int(message.payload.decode("utf-8"))


mqtt_client.on_message = on_message
mqtt_client.subscribe("lightIntensity")
def mqtt_loop():
    while True:
        mqtt_client.loop()

mqtt_thread = threading.Thread(target=mqtt_loop)
mqtt_thread.daemon = True
mqtt_thread.start()


def check_email_reply():
    global email_received
    # Connect to the IMAP server
    imap_url = "imap-mail.outlook.com"
    email_address = "uraibiotproject@outlook.com"
    password = "bandar123"
    imap = imaplib.IMAP4_SSL(imap_url)
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


app.layout = html.Div([
    html.Div(
        id="app-Header",
        children=[
            html.Div('IOT Dashboard by Eris, Uraib And George',
                     className="app-header--title")
        ]
    ),

    html.Div(
        dcc.Interval(
            id='interval-component',
            interval=10000,
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
                value=0,
                max=1023,
                min=0,
                showCurrentValue=True,
                units="",
                style={
                    'margin-bottom': '5%'
                }
            ),
        ]
    ),

    html.Div(id='hidden-div', style={'display': 'none'}),








])


@app.callback(
    Output('light-intensity-indicator', 'value'),
    Input('interval-component', 'n_intervals')
)
def update_light_intensity(value):
    return light_intensity


@app.callback(
    Output('humidity-indicator', 'value'),
    Input('interval-component', 'n_intervals')
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
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setwarnings(False)
        # Motor1 = 27
        # GPIO.setup(Motor1, GPIO.OUT)
        # GPIO.output(Motor1, GPIO.HIGH)

        return {'display': 'block', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, {'display': 'none', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, True
    else:
        return {'display': 'none', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, {'display': 'block', 'height': '200px', 'width': '200px', 'margin-left': '40px'}, False


def send_email():
    smtp_server = "smtp-mail.outlook.com"
    port = 587  # For starttls
    sender_email = "uraibiotproject@outlook.com"
    receiver_email = "uraibiotproject@outlook.com"
    password = "bandar123"

    subject = "Subject: Turn on FAN"
    body = "The current temperature is over 24 Would you like to turn on the fan?”"

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
