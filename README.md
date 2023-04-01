# IoT Dashboard 🌡️💨🌐

An IoT dashboard project to monitor temperature and humidity and control a fan remotely through email. Built with Python, Dash, and a Raspberry Pi.

## Description 📝

This IoT dashboard project allows you to monitor temperature and humidity in real-time using a Raspberry Pi, DHT11 sensor, and a fan. It displays temperature, humidity, and fan status on a dashboard with interactive visualizations. The dashboard will send an email to the user when the temperature exceeds a specified threshold, and the user can reply to the email to turn on the fan.

## Features ⭐

- Real-time temperature and humidity monitoring 🌡️💧
- Email notifications when the temperature exceeds a specified threshold 📧
- Remote fan control through email replies 📨
- Interactive dashboard with visualizations for temperature, humidity, and fan status 📊

## Dependencies 📦

- Python 3 🐍
- Dash 🖥️
- DHT11 sensor 🌡️
- Raspberry Pi 🍓
- Fan (compatible with Raspberry Pi) 💨

## Installation 🔧

1. Clone this repository to your local machine.
2. Install the required Python packages.
3. Connect the DHT11 sensor and the fan to your Raspberry Pi according to the manufacturer's instructions.

## Usage 🚀

1. Run the main script:
2. Access the IoT dashboard on your browser at `http://localhost:8050/`.
3. When the temperature exceeds the specified threshold, you will receive an email asking if you would like to turn on the fan. 🌡️🔥
4. Reply to the email with "YES" to turn on the fan. The fan will turn off automatically after 10 seconds. 💨⏲️

## Note 📌

Please update the email credentials (email address and password) in the `check_email_reply()` function with your own email account.

## License 📄

This project is open source and available under the [MIT License](LICENSE).




