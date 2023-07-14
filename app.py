from flask import Flask, request
from pymongo import MongoClient
import certifi
from datetime import datetime
from collections import OrderedDict, Counter
import json

server = MongoClient("mongodb+srv://userReadOnly:7ZT817O8ejDfhnBM@minichallenge.q4nve1r.mongodb.net/"
                     , tlsCAFile=certifi.where())
db = server.minichallenge
flights = db.flights
hotels = db.hotels

app = Flask(__name__)


def validate(date_text):
    datetime.fromisoformat(date_text)


@app.route('/flight', methods=['GET'])
def get_flights():
    departureDate = request.args.get('departureDate')
    returnDate = request.args.get('returnDate')
    destination = request.args.get('destination')
    if not departureDate or not returnDate or not destination:
        return json.dumps('Missing parameters'), 400
    try:
        validate(departureDate)
        validate(returnDate)
    except:
        return json.dumps('Bad date parameters'), 400
    departureDateIso = departureDate + "T00:00:00.000+00:00"
    returnDateIso = returnDate + "T00:00:00.000+00:00"
    dDate = datetime.fromisoformat(departureDateIso)
    rDate = datetime.fromisoformat(returnDateIso)

    departing_flights = flights.find({
        'destcity': destination,
        'date': dDate,
        'srccity': 'Singapore'
    })

    returning_flights = flights.find({
        'srccity': destination,
        'date': rDate,
        'destcity': 'Singapore'
    })
    curr_cheapest_price = float('inf')
    curr_cheapest_flights = None
    for departing_flight in departing_flights:
        for returning_flight in returning_flights:
            if departing_flight['airline'] == returning_flight['airline']:
                incoming_price = returning_flight['price']
                outgoing_price = departing_flight['price']
                total_price = incoming_price + outgoing_price
                if total_price < curr_cheapest_price:
                    curr_cheapest_price = total_price
                    curr_cheapest_flights = (departing_flight, returning_flight)
    if curr_cheapest_flights:
        response = OrderedDict([
            ('City', destination),
            ('Departure Date', curr_cheapest_flights[0]['date'].strftime("%Y-%m-%d")),
            ('Departure Airline', curr_cheapest_flights[0]['airlinename']),
            ('Departure Price', curr_cheapest_flights[0]['price']),
            ('Return Date', curr_cheapest_flights[1]['date'].strftime("%Y-%m-%d")),
            ('Return Airline', curr_cheapest_flights[1]['airlinename']),
            ('Return Price', curr_cheapest_flights[1]['price'])
        ])
        return json.dumps([response]), 200
    else:
        return json.dumps([]), 200


@app.route('/hotel', methods=['GET'])
def get_hotel():
    check_in_date = request.args.get('checkInDate')
    check_out_date = request.args.get('checkOutDate')
    destination = request.args.get('destination')
    if not check_in_date or not check_out_date or not destination:
        return json.dumps('Missing parameters'), 400
    try:
        validate(check_in_date)
        validate(check_out_date)
    except:
        return json.dumps('Bad date parameters'), 400
    check_in_date_iso = check_in_date + "T00:00:00.000+00:00"
    check_out_date_iso = check_out_date + "T00:00:00.000+00:00"
    in_date = datetime.fromisoformat(check_in_date_iso)
    out_date = datetime.fromisoformat(check_out_date_iso)
    num_days = (out_date - in_date).days + 1
    hotel_list_sorted = hotels.find({
        "date": {
            "$gte": in_date,
            "$lte": out_date
        },
        'city': destination
    }).sort([('hotelName', 1), ("date", 1), ("price", 1)])

    hotel_day_counts = Counter()
    unique_combis = set()
    cheapest_hotel_list = []
    for hotel in hotel_list_sorted:
        combi = (hotel['hotelName'], hotel['date'])
        if combi not in unique_combis:
            unique_combis.add(combi)
            cheapest_hotel_list.append(hotel)
    for hotel in cheapest_hotel_list:
        hotel_day_counts[hotel['hotelName']] += 1
    final_list = [hotel for hotel in cheapest_hotel_list if hotel_day_counts[hotel['hotelName']] >= num_days]
    print(hotel_day_counts)
    curr_hotel_name = ""
    curr_price = 0
    cheapest_hotel_name = []
    cheapest_price = float('inf')
    for hotel in final_list:
        name = hotel['hotelName']
        price = hotel['price']
        if curr_hotel_name == "":
            curr_hotel_name = name
            curr_price = price
        elif curr_hotel_name == name:
            curr_price += price
        elif curr_hotel_name != name:
            if curr_price == cheapest_price:
                cheapest_hotel_name.append(curr_hotel_name)
            elif curr_price < cheapest_price:
                cheapest_hotel_name = [curr_hotel_name]
                cheapest_price = curr_price
            curr_hotel_name = name
            curr_price = price
    response = []
    if len(cheapest_hotel_name) != 0:
        for hotel in cheapest_hotel_name:
            response.append(OrderedDict([
                ('City', destination),
                ("Check In Date", in_date.strftime("%Y-%m-%d")),
                ('Check Out Date', out_date.strftime("%Y-%m-%d")),
                ('Hotel', hotel),
                ('Price', cheapest_price)
            ]))
    return json.dumps(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
