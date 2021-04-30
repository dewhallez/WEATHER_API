from flask import Flask, render_template, request
import requests
import configparser

# create function to get API Key from config.ini file
def get_api_key():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['openweathermap']['api']


app = Flask(__name__)

# Route to home page
@app.route('/')
def weather_dashboard():
    return render_template('home.html')

# Route to results
@app.route('/results', methods=['POST'])
def render_results():
    zip_code = request.form['zipCode']

    api_key = get_api_key()
    data = get_weather_results(zip_code, api_key)
    temp = "{0:.1f}".format(data['main']["temp"])
    feels_like = "{0:.1f}".format(data["main"]["feels_like"])
    location = data["name"]
    description = data['weather'][0]['description']
    

    return render_template('results.html', location=location, temp=temp, feels_like=feels_like, description=description)


# Get api key from "config.ini" file
def get_api_key():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['openweathermap']['api']


# Get weather for a specified zip code
def get_weather_results(zip_code, api_key):
    api_url = "https://api.openweathermap.org/data/2.5/weather?zip={}&units=imperial&appid={}".format(zip_code, api_key)
    r = requests.get(api_url)
    return r.json()

# print out weather for a desired zip code
#print(get_weather_results('30122', get_api_key()))


if __name__ == '__main__':
    app.run(debug=True)
