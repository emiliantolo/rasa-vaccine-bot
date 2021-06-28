import requests
import json
import random
import datetime
import uuid

regions = ['ABR', 'BAS', 'CAL', 'CAM', 'EMR', 'FVG', 'LAZ', 'LIG', 'LOM', 'MAR', 'MOL', 'PAB', 'PAT', 'PIE', 'PUG', 'SAR', 'SIC', 'TOS', 'UMB', 'VDA', 'VEN', 'ITA']

region_names = [
"Abruzzo",
"Basilicata",
"Calabria",
"Campania",
"Emilia Romagna",
"Friuli Venezia Giulia",
"Lazio",
"Liguria",
"Lombardia",
"Marche",
"Molise",
"P.A. Bolzano",
"P.A. Trento",
"Piemonte",
"Puglia",
"Sardegna",
"Sicilia",
"Toscana",
"Umbria",
"Valle d'Aosta",
"Veneto"
]

searches = dict()

def random_date(start, end):
    delta = end - start
    minutes_delta = (delta.days * 24 * 60)
    random_minute = random.randrange(minutes_delta)
    return (start + datetime.timedelta(minutes=random_minute)).strftime("%d %B at %H %M")

def get_regions():
    return regions

def get_region_name(region):
    index = regions.index(region) 
    return region_names[index]

def get_region(region):
    data = requests.get('https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/vaccini-summary-latest.json')
    data = data.json()['data']
    return [e for e in data if e['area'] == region][0]

def get_stats():
    data = requests.get('https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/vaccini-summary-latest.json')
    data = data.json()['data']
    return data

def get_user(id):
    user = None
    f = open('vaccine_db/users.json')
    data = json.load(f)
    for u in data:
        if u['id'] == id:
            user = u
    f.close()
    return user

def get_user_vaccination(user_id):
    vaccination = None
    with open('vaccine_db/bookings.json') as f:
        data = json.load(f)
        f.close()
    for v in data:
        if v['user_id'] == user_id:
            vaccination = v['vaccination']
    return vaccination

def get_first_vaccine(region):
    data = requests.get('https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/punti-somministrazione-tipologia.json')
    data = data.json()['data']
    places = [e['denominazione_struttura'] for e in data if e['area'] == region]
    n = 5
    s_places = [places[i] for i in random.sample(range(0, len(places)), n)]
    start = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time()) + datetime.timedelta(days=1)
    end = start + datetime.timedelta(days=30)
    s_dates = [random_date(start, end) for i in range(n)]
    s_dates.sort()
    vaccines = [{'id': str(uuid.uuid4()), 'place': s_places[i], 'time': s_dates[i], 'details': 'floor {}'.format(random.randint(0,5))} for i in range (n)]
    search_id = str(uuid.uuid4())
    searches[search_id] = vaccines
    return search_id

def get_date_vaccine(region, date):
    data = requests.get('https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/punti-somministrazione-tipologia.json')
    data = data.json()['data']
    places = [e['denominazione_struttura'] for e in data if e['area'] == region]
    n = random.randint(0, 3)
    s_places = [places[i] for i in random.sample(range(0, len(places)), n)]
    date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f%z')
    start = date
    end = start + datetime.timedelta(hours=24)
    s_dates = [random_date(start, end) for i in range(n)]
    s_dates.sort()
    vaccines = [{'id': str(uuid.uuid4()), 'place': s_places[i], 'time': s_dates[i], 'details': 'floor {}'.format(random.randint(0,5))} for i in range (n)]
    search_id = str(uuid.uuid4())
    searches[search_id] = vaccines
    return search_id

def save_booking(user_id, vaccine):
    with open('vaccine_db/bookings.json') as f:
        data = json.load(f)
        f.close()
    booking = {'user_id': user_id, 'vaccination': vaccine}
    data.append(booking)
    with open('vaccine_db/bookings.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.close()

def remove_user_vaccination(user_id):
    with open('vaccine_db/bookings.json') as f:
        data = json.load(f)
        f.close()
    index = -1
    for i in range(len(data)):
        if data[i]['user_id'] == user_id:
            index = i
    if index != -1:
        data.pop(index)
        with open('vaccine_db/bookings.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.close()
        return True
    else:
        return False
        