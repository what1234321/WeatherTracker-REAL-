
from flask import Flask, render_template, request, jsonify
import json
import requests
from datetime import datetime

app = Flask(__name__)
API_KEY = '9777155c8a3cc183254aee7ad5ebbafe'

HISTORY_FILE = 'history.json'
WEATHER_HISTORY_FILE = 'weather_history.json'

def save_search_history(city):
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []
    history_entry = {
        'city': city,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    history.append(history_entry)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)

@app.route('/history')
def view_history():
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []
    return render_template('history.html', history=history)

def save_weather_history(city, weather):
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        with open(WEATHER_HISTORY_FILE, 'r') as f:
            all_history = json.load(f)
    except FileNotFoundError:
        all_history = {}
    city_history = all_history.get(city, [])
    for entry in city_history:
        if entry['date'] == today:
            entry['temperature'] = weather['temperature']
            entry['humidity'] = weather['humidity']
            break
    else:
        city_history.append({
            'date': today,
            'temperature': weather['temperature'],
            'humidity': weather['humidity']
        })
    city_history = city_history[-3:]
    all_history[city] = city_history
    with open(WEATHER_HISTORY_FILE, 'w') as f:
        json.dump(all_history, f, indent=4)

def get_recent_weather_data(city):
    try:
        with open(WEATHER_HISTORY_FILE, 'r') as f:
            all_history = json.load(f)
            return all_history.get(city, [])
    except FileNotFoundError:
        return []

def get_weather(city):
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=kr'
    response = requests.get(url)
    data = response.json()
    if data.get('cod') != 200:
        return {'city': city, 'error': '날씨 정보를 불러올 수 없습니다.'}
    return {
        'city': city,
        'temperature': data['main']['temp'],
        'humidity': data['main']['humidity'],
        'description': data['weather'][0]['description'],
        'rain': data.get('rain', {}).get('1h', 0),
        'error': None
    }

@app.route('/')
def home():
    city = request.args.get('city', 'Seoul')
    weather = get_weather(city)
    if not weather.get('error'):
        save_search_history(city)
        save_weather_history(city, weather)
    history_data = get_recent_weather_data(city)
    if len(history_data) >= 2:
        yesterday = history_data[-2]
        weather['delta_temp'] = weather['temperature'] - yesterday['temperature']
        weather['delta_humidity'] = weather['humidity'] - yesterday['humidity']
    else:
        weather['delta_temp'] = None
        weather['delta_humidity'] = None
    chart_data = {
        'dates': [d['date'] for d in history_data],
        'temps': [d['temperature'] for d in history_data],
        'humidities': [d['humidity'] for d in history_data]
    }
    return render_template('index.html', weather=weather, chart_data=chart_data)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
