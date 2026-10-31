"""Locust load test for the guest paths (see README.md). Local development only."""
import json
import os
import random
from datetime import date, timedelta
from pathlib import Path

from locust import HttpUser, between, task

API = '/api/v1'
# People look for the same few places and the same coming days, and open the hotels at the top of the list
CITIES = ['Tashkent'] * 5 + ['Samarkand'] * 3 + ['Bukhara'] * 2 + ['Khiva', 'Fergana', 'Namangan', 'Almaty', 'Istanbul']
SESSIONS = json.loads(Path(__file__).with_name('sessions.json').read_text()) \
    if Path(__file__).with_name('sessions.json').exists() else []
BUSINESS_REFUSALS = (400, 409, 429)
# Against a production-like server (DEBUG off, https only) set this to one of its CSRF_TRUSTED_ORIGINS: the test then
# speaks as a visitor that came over https through the proxy. Leave it unset against the development server.
HTTPS_ORIGIN = os.getenv('LOADTEST_ORIGIN', '')
# Seconds a visitor reads a page before the next click. 1-3 is a stress test; 40-80 is people reading (3000 visitors).
WAIT_MIN = float(os.getenv('LOADTEST_WAIT_MIN', '1'))
WAIT_MAX = float(os.getenv('LOADTEST_WAIT_MAX', '3'))


def stay():
    start = date.today() + timedelta(days=random.randint(3, 17))
    return start.isoformat(), (start + timedelta(days=random.randint(1, 3))).isoformat()


class Guest(HttpUser):
    """Browses: search, hotel page, availability, quote."""
    weight = 8
    wait_time = between(WAIT_MIN, WAIT_MAX)

    def on_start(self):
        self.hotel = None
        # Behind nginx every visitor has an own address; the API throttles per address (NUM_PROXIES=1)
        self.client.headers['X-Forwarded-For'] = '.'.join(str(random.randint(1, 254)) for _ in range(4))
        if HTTPS_ORIGIN:
            self.client.headers['X-Forwarded-Proto'] = 'https'

    def search(self):
        check_in, check_out = stay()
        with self.client.get(f'{API}/properties/search/', name='search', catch_response=True, params={
                'location': random.choice(CITIES), 'check_in': check_in, 'check_out': check_out,
                'page': random.choices([1, 2, 3], weights=[6, 3, 1])[0]}) as response:
            if response.status_code != 200:
                return response.failure(f'status {response.status_code}')
            results = response.json().get('results', [])
            if results:
                self.hotel = random.choices(results, weights=[1 / (rank + 1) for rank in range(len(results))])[0]['id']

    @task(5)
    def search_then_open_hotel(self):
        self.search()
        if not self.hotel:
            return
        detail = self.client.get(f'{API}/properties/{self.hotel}/', name='hotel page')
        self.client.get(f'{API}/properties/{self.hotel}/availability/', name='availability',
                        params={'check_in': date.today().isoformat()})
        if detail.status_code != 200 or not detail.json().get('room_types'):
            return
        room = random.choice(detail.json()['room_types'])
        plans = room.get('rate_plans') or []
        if plans:
            check_in, check_out = stay()
            # "No rooms left" (400) is the right answer once the booking users have filled the best hotels
            with self.client.get(f'{API}/properties/{self.hotel}/quote/', name='quote', catch_response=True, params={
                    'room_type_id': room['id'], 'rate_plan_id': plans[0]['id'],
                    'check_in': check_in, 'check_out': check_out}) as quote:
                if quote.status_code in (200, 400):
                    quote.success()
                else:
                    quote.failure(f'status {quote.status_code}')

    @task(2)
    def filter_options(self):
        self.client.get(f'{API}/properties/filter-options/', name='filter options')

    @task(1)
    def suggestions(self):
        self.client.get(f'{API}/properties/search/suggestions/', name='suggestions',
                        params={'q': random.choice(['Silk', 'Grand', 'Hauz', 'Tash'])})

    @task(1)
    def geography(self):
        self.client.get(f'{API}/geography/countries/', name='geography countries')


class Booker(Guest):
    """Browses like a guest, then books (pending booking, no payment)."""
    weight = 2
    session_index = 0

    def on_start(self):
        super().on_start()
        if not SESSIONS:
            raise SystemExit('Run make_sessions.py first')
        self.next_identity()

    def next_identity(self):
        Booker.session_index += 1
        self.client.cookies.set('sessionid', SESSIONS[Booker.session_index % len(SESSIONS)])
        self.client.get(f'{API}/auth/csrf/', name='csrf')
        self.csrf = self.client.cookies.get('csrftoken')
        if HTTPS_ORIGIN:
            # The cookie is Secure and this test talks plain http to the server: send it back as an ordinary cookie
            self.client.cookies.set('csrftoken', self.csrf or '')

    def write_headers(self):
        headers = {'X-CSRFToken': self.csrf or ''}
        if HTTPS_ORIGIN:
            headers.update({'Origin': HTTPS_ORIGIN, 'Referer': f'{HTTPS_ORIGIN}/'})
        return headers

    @task(3)
    def book(self):
        self.search()
        if not self.hotel:
            return
        detail = self.client.get(f'{API}/properties/{self.hotel}/', name='hotel page')
        rooms = detail.json().get('room_types') if detail.status_code == 200 else None
        if not rooms or not rooms[0].get('rate_plans'):
            return
        check_in, check_out = stay()
        body = {'property_id': self.hotel, 'room_type_id': rooms[0]['id'],
                'rate_plan_id': rooms[0]['rate_plans'][0]['id'], 'check_in': check_in, 'check_out': check_out,
                'guest_count': 1, 'expected_arrival_time': '14:00'}
        with self.client.post(f'{API}/bookings/', name='create booking', json=body, catch_response=True,
                              headers=self.write_headers()) as response:
            if response.status_code in (200, 201):
                response.success()
                self.next_identity()
            elif response.status_code in BUSINESS_REFUSALS:
                response.success()
            else:
                response.failure(f'status {response.status_code}')
