import os

__author__ = 'Timur'

import gflags
import httplib2

from apiclient import discovery
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run


def main():
    client_secret_filename = 'client_secret.txt'
    calendar_oauth_filename = 'calendar.dat'

    print("Please login with your google credentials...")
    google_service = connect_to_google_cal_api_service(client_secret_filename, calendar_oauth_filename)
    while True:
        print("\n\nOptions:")
        print("1 - List all calendars")
        print("2 - Clear your primary calendar")
        print("3 - Count duplicate events in two calendars")
        print("4 - Remove duplicate events from a particular calendar")
        print("5 - Quit")
        user_input = raw_input('What would you like to do? ')
        if int(user_input) == 1:
            list_all_calendars(google_service)
        elif int(user_input) == 2:
            clear_primary_calendar(google_service)
        elif int(user_input) == 3:
            count_num_duplicate_events_in_two_cals(google_service)
        elif int(user_input) == 4:
            remove_all_duplicates_from_cal_one(google_service)
        elif int(user_input) == 5:
            logout(calendar_oauth_filename)
            print("Good Bye!")
            break
        else:
            print('Sorry I could not recognize your input. Please try again.')


def logout(filename_to_remove):
    os.remove(filename_to_remove)


def clear_primary_calendar(google_service):
    print('Are you sure you want to delete all events from your primary calendar (this cannot be undone)?')
    user_input = raw_input('(Y/N)')
    if user_input.lower() == 'y':
        print 'Attempting to clear events...'
        try:
            google_service.calendars().clear(calendarId='primary').execute()
        except:
            calendar_id = raw_input('Auto-clear failed. Please enter the calendar id: ')
            all_events = get_all_events_from_calendar(google_service, calendar_id)
            for event in all_events:
                try:
                    print "Deleting event '{0}'".format(event[unicode('summary')])
                except:
                    True
                try:
                    google_service.events().delete(calendarId=calendar_id, eventId=event[unicode('id')]).execute()
                except:
                    print "Could not delete event with the id: '{0}'".format(event[unicode('id')])
        print 'All done.'


def list_all_calendars(google_service):
    page_token = None
    while True:
        calendar_list = google_service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            print "Name: {0} ID: {1}".format(calendar_list_entry['summary'], calendar_list_entry['id'])
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break


def connect_to_google_cal_api_service(client_secret_filename, calendar_oauth_filename):
    oauth_settings = get_oauth_settings_from_file(client_secret_filename)

    FLAGS = gflags.FLAGS

    # Set up a Flow object to be used if we need to authenticate. This
    # sample uses OAuth 2.0, and we set up the OAuth2WebServerFlow with
    # the information it needs to authenticate. Note that it is called
    # the Web Server Flow, but it can also handle the flow for native
    # applications
    # The client_id and client_secret can be found in Google Developers Console
    FLOW = OAuth2WebServerFlow(
        client_id=oauth_settings[0],
        client_secret=oauth_settings[1],
        scope='https://www.googleapis.com/auth/calendar',
        user_agent='SaveMyCal/0.1')

    # To disable the local server feature, uncomment the following line:
    # FLAGS.auth_local_webserver = False

    # If the Credentials don't exist or are invalid, run through the native client
    # flow. The Storage object will ensure that if successful the good
    # Credentials will get written back to a file.
    storage = Storage(calendar_oauth_filename)
    credentials = storage.get()
    if credentials is None or credentials.invalid == True:
        credentials = run(FLOW, storage)

    # Create an httplib2.Http object to handle our HTTP requests and authorize it
    # with our good Credentials.
    http = httplib2.Http()
    http = credentials.authorize(http)

    # Build a service object for interacting with the API. Visit
    # the Google Developers Console
    # to get a developerKey for your own application.
    service = discovery.build(serviceName='calendar', version='v3', http=http, developerKey=oauth_settings[2])
    return service


def get_oauth_settings_from_file(file_name):
    with open(file_name, "r") as file:
        read_settings = file.readlines()
        settings_to_return = []
        for line in read_settings:
            settings_to_return.append(line.replace("\n", ""))
        return settings_to_return


def count_num_duplicate_events_in_two_cals(service):
    calendar_one = raw_input('Enter the first calendar id: ')
    calendar_two = raw_input('Enter the second calendar id: ')

    all_cal_one_events = get_all_events_from_calendar(service, calendar_one)
    print "# of cal 1 events: {0}".format(len(all_cal_one_events))

    all_cal_two_events = get_all_events_from_calendar(service, calendar_two)
    print "# of cal 2 events: {0}".format(len(all_cal_two_events))

    matching_event_ids = get_duplicates_in_two_event_sets(all_cal_one_events, all_cal_two_events)

    print "Total number of duplicate events: {0}".format(len(matching_event_ids))


def get_duplicates_in_two_event_sets(event_set_one, event_set_two):
    matching_event_ids = []
    for cal_two_event in event_set_two:
        for cal_one_event in event_set_one:
            try:
                cal_two_event_title = cal_two_event[unicode("summary")]
                try:
                    cal_one_event_title = cal_one_event[unicode("summary")]
                    try:
                        cal_two_event_start = cal_two_event[unicode("start")][unicode("dateTime")]
                        try:
                            cal_one_event_start = cal_one_event[unicode("start")][unicode("dateTime")]
                            if cal_two_event_title == cal_one_event_title and cal_two_event_start == cal_one_event_start:
                                print "~~~~~ FOUND A MATCH ~~~~: {0}".format(cal_one_event["id"])
                                matching_event_ids.append(cal_one_event["id"])
                        except:
                            cal_two_event_start = cal_two_event[unicode("start")][unicode("date")]
                            try:
                                cal_one_event_start = cal_one_event[unicode("start")][unicode("date")]
                                print cal_two_event
                                if cal_two_event_title == cal_one_event_title and cal_two_event_start == cal_one_event_start:
                                    print "~~~~~ FOUND A DATE MATCH ~~~~: {0}".format(cal_one_event["id"])
                                    matching_event_ids.append(cal_one_event["id"])
                            except:
                                True
                            #print "Could not get cal 1 event start date"
                    except:
                        #print "Could not get cal 2 event start date."
                        cal_two_event_start = cal_two_event[unicode("start")][unicode("date")]
                        try:
                            cal_one_event_start = cal_one_event[unicode("start")][unicode("date")]
                            if cal_two_event_title == cal_one_event_title and cal_two_event_start == cal_one_event_start:
                                print "~~~~~ FOUND A DATE MATCH ~~~~: {0}".format(cal_one_event["id"])
                                matching_event_ids.append(cal_one_event["id"])
                        except:
                            True
                except:
                    True
                    #print "Could not get title of cal 1 event."
            except:
                True
                #print "Could not get title of cal 2 event."
    return matching_event_ids


def get_all_events_from_calendar(service, cal_id):
    all_cal_events = []
    page_token = None
    while True:
        cal_events = service.events().list(calendarId=cal_id, pageToken=page_token).execute()
        for event in cal_events['items']:
            all_cal_events.append(event)
        page_token = cal_events.get('nextPageToken')
        if not page_token:
            break
    return all_cal_events


def remove_all_duplicates_from_cal_one(service):
    calendar_one = raw_input('Enter the first calendar id: ')
    calendar_two = raw_input('Enter the second calendar id: ')

    all_cal_one_events = get_all_events_from_calendar(service, calendar_one)
    print "# of cal 1 events: {0}".format(len(all_cal_one_events))

    all_cal_two_events = get_all_events_from_calendar(service, calendar_two)
    print "# of cal 2 events: {0}".format(len(all_cal_two_events))

    matching_event_ids = get_duplicates_in_two_event_sets(all_cal_one_events, all_cal_two_events)
    for event_id in matching_event_ids:
        print "Removing event '{0}'".format(event_id)
        service.events().delete(calendarId=calendar_one, eventId=event_id).execute()


if __name__ == "__main__":
    main()