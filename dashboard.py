from dash import Dash, html, Input, Output
import dash_daq as daq
import Freenove_DHT as DHT
import time
from dash import dcc
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
import imaplib
import email
import RPi.GPIO as GPIO



DHTPin = 23  # define the pin of DHT11


email_sent = False
email_received = False
GPIO.setwarnings(False)

app = Dash(__name__, external_stylesheets=['./assets/dashboard.css'])





def check_email_reply():
    global email_received
    # Connect to the IMAP server
    imap_url = "imap-mail.outlook.com"
    email_address = "iot-project-2023@outlook.com"
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
                body = part.get_payload(decode=True).decode()
                if "YES" in body.upper() and not email_received:
                    email_received = True
                    fan_on = True
    imap.close()
    return fan_on


app.layout = html.Div([
    html.Div(
        id="app-Header",
        children=[
            html.Div('IOT Dashboard by Eris, Uraib And George', className="app-header--title")
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
                html.Img(id='FanOn', src='https://www.nicepng.com/png/detail/29-294805_png-file-fan-icon-transparent.png', ),
                
            ]),
            html.Div(children=[
                html.Img(id='FanOff', src='https://cdn-icons-png.flaticon.com/512/925/925993.png', ),
            ]),
            daq.Indicator(
                id='fan-indicator',
                value=True,
                color="#00cc96"
            )
        ]
    ),
    html.Div(id='hidden-div', style={'display': 'none'}),








])

@app.callback(
    Output('humidity-indicator', 'value'),
    Input('interval-component', 'n_intervals')
)
def update_humidity(value):
    dht = DHT.DHT(DHTPin)   #create a DHT class object
    for i in range(0,15):            
        chk = dht.readDHT11()     #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
        if (chk is dht.DHTLIB_OK):      #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
            print("Humidity : %.2f, \n"%(dht.humidity))
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
            print("Temperature : %.2f, \n"%(dht.temperature))
            break
        time.sleep(0.1)
    if (dht.temperature > 10) and not email_sent:
        send_email()
        email_sent = True
        print("Email sent!")
    elif dht.temperature <= 24:
        email_sent = False   
    return dht.temperature

@app.callback(
    Output('FanOn', 'style'),
    Output('FanOff', 'style'),
    Output('fan-indicator', 'value'),
    Input('interval-component', 'n_intervals')
)
def update_fan(value):
    global email_sent, email_received
    fan_on = check_email_reply()
    if fan_on:
        return {'display': 'block'}, {'display': 'none'}, True
    else:
        return {'display': 'none'}, {'display': 'block'}, False



def send_email():
    smtp_server = "smtp-mail.outlook.com"
    port = 587  # For starttls
    sender_email = "iot-project-2023@outlook.com"
    receiver_email = "bandar123"
    password = "iotproject123"

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
