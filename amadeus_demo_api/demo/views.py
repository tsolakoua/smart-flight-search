import os
from datetime import datetime, timedelta
from amadeus import Client, ResponseError
from django.shortcuts import render


def demo(request):
    origin = request.POST.get('Origin')
    destination = request.POST.get('Destination')
    departureDate = request.POST.get('Departuredate')
    returnDate = request.POST.get('Returndate')
    adults = request.POST.get('Adults')

    kwargs = {'origin': request.POST.get('Origin'), 'destination': request.POST.get('Destination'),
              'departureDate': request.POST.get('Departuredate')}
    if adults:
        kwargs['adults'] = adults
    if returnDate:
        kwargs['returnDate'] = returnDate

    amadeus = Client(
        client_id= os.environ.get('API_KEY'),
        client_secret=os.environ.get('API_SECRET'),
    )

    if origin and destination and departureDate:
        try:
            low_fare_flights = amadeus.shopping.flight_offers.get(**kwargs)
            prediction_flights = amadeus.shopping.flight_offers.prediction.post(low_fare_flights.result)
        except ResponseError as error:
            print(error)
        low_fare_flights_returned = []
        for flight in low_fare_flights.data:
            offer = construct_flights(flight)
            low_fare_flights_returned.append(offer)
        prediction_flights_returned = []
        for flight in prediction_flights.data:
            offer = construct_flights(flight)
            prediction_flights_returned.append(offer)

        return render(request, 'demo/results.html', {'response': low_fare_flights_returned,
                                                     'prediction': prediction_flights_returned,
                                                     'origin': origin,
                                                     'destination': destination,
                                                     'departureDate': departureDate,
                                                     'returnDate': returnDate
                                                     })
    return render(request, 'demo/demo_form.html', {})


def construct_flights(flight):
    offer = {}
    index = 0
    offer['price'] = flight['offerItems'][0]['price']['total']
    offer['id'] = flight['id']
    for f in flight['offerItems'][0]['services']:
        if len(flight['offerItems'][0]['services'][index]['segments']) == 2:  # one stop flight
            offer[str(index)+'firstFlightDepartureAirport'] = \
            flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['departure']['iataCode']
            offer[str(index)+'firstFlightAirlineLogo'] = \
            get_airline_logo(flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['carrierCode'])
            offer[str(index)+'firstFlightAirline'] = \
            flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['carrierCode']
            offer[str(index) + 'firstFlightDepartureDate'] = \
            get_hour(flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['departure']['at'])
            offer[str(index)+'firstFlightArrivalAirport'] = \
            flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['arrival']['iataCode']
            offer[str(index)+'firstFlightArrivalDate'] = \
            get_hour(flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['arrival']['at'])
            offer[str(index)+'firstFlightArrivalDuration'] = \
            get_duration(flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['duration'])
            offer[str(index)+'secondFlightDepartureAirport'] = \
            flight['offerItems'][0]['services'][index]['segments'][1]['flightSegment']['departure']['iataCode']
            offer[str(index) + 'secondFlightDepartureDate'] = \
            get_hour(flight['offerItems'][0]['services'][index]['segments'][1]['flightSegment']['departure']['at'])
            offer[str(index)+'secondFlightAirlineLogo'] = \
            get_airline_logo(flight['offerItems'][0]['services'][index]['segments'][1]['flightSegment']['carrierCode'])
            offer[str(index)+'secondFlightAirline'] = \
            flight['offerItems'][0]['services'][index]['segments'][1]['flightSegment']['carrierCode']
            get_hour(flight['offerItems'][0]['services'][index]['segments'][1]['flightSegment']['departure']['at'])
            offer[str(index)+'secondFlightArrivalAirport'] = \
            flight['offerItems'][0]['services'][index]['segments'][1]['flightSegment']['arrival']['iataCode']
            offer[str(index)+'secondFlightArrivalDate'] = \
            get_hour(flight['offerItems'][0]['services'][index]['segments'][1]['flightSegment']['arrival']['at'])
            offer[str(index)+'secondFlightArrivalDuration'] = \
            get_duration(flight['offerItems'][0]['services'][index]['segments'][1]['flightSegment']['duration'])
            offer[str(index)+'stop_time'] = get_stoptime(flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['arrival']['at'],
                                              flight['offerItems'][0]['services'][index]['segments'][1]['flightSegment']['departure']['at'])
            offer[str(index) + 'FlightTotalDuration'] = get_total_duration_connecting_flights(offer[str(index) + 'stop_time'], offer[
                str(index) + 'firstFlightArrivalDuration'], offer[str(index) + 'secondFlightArrivalDuration'])


        elif len(flight['offerItems'][0]['services'][index]['segments']) == 1:  # direct flight
            offer[str(index)+'price'] = flight['offerItems'][0]['price']['total']
            offer[str(index)+'firstFlightDepartureAirport'] = \
            flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['departure']['iataCode']
            offer[str(index)+'firstFlightAirlineLogo'] = \
            get_airline_logo(flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['carrierCode'])
            offer[str(index)+'firstFlightAirline'] = \
            flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['carrierCode']
            offer[str(index)+'firstFlightDepartureDate'] = \
            get_hour(flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['departure']['at'])
            offer[str(index)+'firstFlightArrivalAirport'] = \
            flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['arrival']['iataCode']
            offer[str(index)+'firstFlightArrivalDate'] = \
            get_hour(flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['arrival']['at'])
            offer[str(index)+'firstFlightArrivalDuration'] = \
            get_duration(flight['offerItems'][0]['services'][index]['segments'][0]['flightSegment']['duration'])
            offer[str(index)+'FlightTotalDuration'] = get_total_duration_direct_flight(offer[str(index)+'firstFlightArrivalDuration'])
        index += 1

    return offer


def get_hour(date_time):
    return datetime.strptime(date_time[0:19], "%Y-%m-%dT%H:%M:%S").strftime("%H:%M")


def get_total_duration_direct_flight(flight_duration):
    hr = flight_duration[0:2]
    min = flight_duration[3:]
    if int(hr) == 0:
        return "%02dm" % (int(min))
    elif int(min) == 0:
        return "%dh" % (int(hr))
    return "%dh %02dm" % (int(hr), int(min))


def get_total_duration_connecting_flights(stop_time, first_flight_duration, second_flight_duration):
    timeList = [stop_time+':00', first_flight_duration+':00', second_flight_duration+':00']
    totalSecs = 0
    for tm in timeList:
        timeParts = [int(s) for s in tm.split(':')]
        totalSecs += (timeParts[0] * 60 + timeParts[1]) * 60 + timeParts[2]
    totalSecs, sec = divmod(totalSecs, 60)
    hr, min = divmod(totalSecs, 60)
    if hr == 0:
        return "%02dm" % min
    elif min == 0:
        return "%dh" % hr
    return "%dh %02dm" % (hr, min)


def get_duration(duration):
    res = datetime.strptime(duration, "%wDT%HH%MM")
    return res.strftime("%H:%M")


def get_stoptime(arrival_stop_time, departure_stop_time):
    arrival = datetime.strptime(arrival_stop_time[0:19], "%Y-%m-%dT%H:%M:%S")
    departure = datetime.strptime(departure_stop_time[0:19], "%Y-%m-%dT%H:%M:%S")
    stoptime = str(timedelta(seconds=(departure-arrival).seconds))
    if stoptime[1] == ':':
        stoptime = '0' + stoptime
    return stoptime[0:5]


def get_airline_logo(carrier_code):
    return "https://s1.apideeplink.com/images/airlines/"+carrier_code+".png"