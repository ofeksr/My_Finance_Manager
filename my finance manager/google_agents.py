"""
Agents for log in to Google Keep and Calendar and syncing list to add new events\tasks to them.
Note:
    Must login before doing anything else with agents.
"""

__version__ = '1.1'

import logging
import os
import pickle
import sys

import gkeepapi
import keyring
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

LOG = logging.getLogger('GoogleAgents.Logger')
handler = logging.StreamHandler(sys.stdout)
LOG.addHandler(handler)


class GoogleCalendarAgent:
    """follow instructions in https://developers.google.com/calendar/quickstart/python for first login (Step 1+2)"""
    def __init__(self):
        LOG.debug('Initialising GoogleCalendarAgent object')
        self.credentials = None
        self.service = None
        LOG.info('GoogleCalendarAgent object created successfully')

    def calendar_login(self) -> bool:
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.credentials = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in.
        if not self.credentials or not self.credentials.valid:

            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())

            else:
                SCOPES = ['https://www.googleapis.com/auth/calendar']
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.credentials = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.credentials, token)

        if self.credentials is None:
            with open('token.pickle', 'rb') as token:
                self.credentials = pickle.load(token)
                LOG.info('Google Calendar token accepted')

        self.service = build('calendar', 'v3', credentials=self.credentials)
        return True

    def add_events_calendar(self, date: str, summary: str, description: str, delete: bool = False):

        event = {
            'summary': summary,
            'description': description,
            'start': {
                'date': date,
            },
            'end': {
                'date': date,
            },
            'reminders': {
                'useDefault': True,
            },
        }

        inserted_event = self.service.events().insert(calendarId='primary', body=event).execute()
        LOG.info(f'Event created in calendar: {inserted_event.get("htmlLink")}')

        if delete:
            self.service.events().delete(calendarId='primary', eventId=inserted_event['id']).execute()

        return True


class GoogleKeepAgent:
    def __init__(self):
        LOG.debug('Initialising GoogleKeepAgent object')
        self.keep = gkeepapi.Keep()
        LOG.info('GoogleKeepAgent object created successfully')

    def keep_login(self, email_address: str, password: str, token: str = None) -> bool:
        """
        Logging in to Google Account, new login if saved token not exists or accepted.
        :return: True
        """
        LOG.debug('Trying to login to Google keep')
        username = email_address.split('@')[0]

        try:  # in case that token not accepted
            if token:
                LOG.debug('Trying to resume with saved token')
                self.keep.resume(email_address, token)

        except:
            try:
                LOG.exception('Failed to get Google Keep token')
                # generate app password if you have Two Factor enabled! otherwise, use account password.
                self.keep.login(email_address, password)

                token = self.keep.getMasterToken()
                keyring.set_password('google-keep-token', username, token)
                LOG.debug('New token saved in keyring')

            except Exception:
                LOG.exception('Failed to log in to Google Keep')
                raise

        LOG.info('Logged in to Google keep')
        return True

    def add_events_to_list(self, list_id: str, events: list, top: bool = False, bottom: bool = False) -> bool:
        """
        Adding new events to list.
        :param bottom: True means item will be inserted to bottom of list.
        :param top: True means item will be inserted to top of list.
        :param list_id: str taken from Google Keep list URL.
        :param events: list of events.
        :return: True
        """
        LOG.debug('Trying to get specific list from Google Keep')
        g_list = self.keep.get(list_id)

        for event in events:

            if top:
                g_list.add(event, False, gkeepapi.node.NewListItemPlacementValue.Top)

            elif bottom:
                g_list.add(event, False, gkeepapi.node.NewListItemPlacementValue.Bottom)

        self.keep.sync()
        LOG.info(f'{len(events)} events added to "{g_list.title}" list')
        return True
