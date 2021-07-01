from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import AllSlotsReset, SlotSet, UserUtteranceReverted
from rasa_sdk import Tracker, FormValidationAction

import datetime
import vaccine_db.data as db

class ActionStats(Action):
    
    def name(self) -> Text:
        return "action_stats"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        region = tracker.get_slot('region')
        is_total = region == "ITA"

        data = db.get_stats()

        if is_total:
            ds = 0
            dc = 0
            for e in data:
                ds += e['dosi_somministrate']
                dc += e['dosi_consegnate']
            ps = "{:.1f}".format(100.0 * ds / dc)
            dispatcher.utter_message(text="Italy has a total of {} vaccination doses administered, with an administration percentage of {} points.\nAre you interested in a particular region?".format(ds, ps))
        else:
            if region in db.get_regions():
                e = db.get_region(region)
                ds = e['dosi_somministrate']
                dc = e['dosi_consegnate']
                name = e['nome_area']
                ps = "{:.1f}".format(100.0 * ds / dc)
                dispatcher.utter_message(text="Region {} has a total of {} vaccination doses administered, with an administration percentage of {} points.\nAre you interested in another region?".format(name, ds, ps))
            else:
                dispatcher.utter_message(text="No region with name {} was found.\nAre you interested in another region?".format(region))
        
        return [AllSlotsReset()]

class ValidateStatsForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_stats_form"

    def validate_region(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        if slot_value in db.get_regions():

            return {"region": slot_value}
        else:

            dispatcher.utter_message(text="No region with name {} was found.".format(slot_value))
            return {"region": None}

class ActionBooking(Action):

    def name(self) -> Text:
        return "action_booking"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        if tracker.get_slot('time') != True:
            dispatcher.utter_message(text="Searching for vaccination for date {}...".format((datetime.datetime.strptime(tracker.get_slot('time'), '%Y-%m-%dT%H:%M:%S.%f%z')).strftime("%d %B")))
            search_id = db.get_date_vaccine(tracker.get_slot('region'), tracker.get_slot('time'))
        else:
            dispatcher.utter_message(text="Searching for the first available vaccination dates...")
            search_id = db.get_first_vaccine(tracker.get_slot('region'))
        
        return [SlotSet('search_id', search_id), SlotSet('last_ok', None)]

class ValidateBookingForm(FormValidationAction):
    
    def name(self) -> Text:
        return "validate_booking_form"

    def validate_region(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        if slot_value in db.get_regions() and slot_value != 'ITA':
            dispatcher.utter_message(text="Search region is {}.".format(db.get_region_name(slot_value)))
            return {"region": slot_value}
        else:
            dispatcher.utter_message(text="No region with name {} was found.".format(slot_value))
            return {"region": None}
    
    def validate_time(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

            if slot_value == True:
                dispatcher.utter_message(text="No interest date was set.")
            else:
                dispatcher.utter_message(text="Search will be done for date {}.".format((datetime.datetime.strptime(slot_value, '%Y-%m-%dT%H:%M:%S.%f%z')).strftime("%d %B")))
            return {"time": slot_value}

    def validate_id_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        user = db.get_user(slot_value)
        if user != None:

            vaccine = db.get_user_vaccination(slot_value)
            if vaccine != None:
                dispatcher.utter_message(text="User with name {} was found, but he has already a reservation for {} on {}.".format(user['first_name'] + " " + user['last_name'], vaccine['place'], vaccine['time']))
                return {"id_number": None, "already_registered": True, "requested_slot": None}
            else:
                dispatcher.utter_message(text="User with name {} was found.".format(user['first_name'] + " " + user['last_name']))
                return {"id_number": slot_value, "already_registered": False}
        else:
            dispatcher.utter_message(text="No user with id {} was found.".format(slot_value))
            return {"id_number": None}

class ActionSetPrev(Action):

    def name(self) -> Text:
        return "action_set_prev"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        slot = tracker.get_slot('requested_slot')

        if slot == 'id_number':
            prev = None
        elif slot == 'region':
            prev = 'id_number'
            sn = 'id number'
        elif slot == 'time':
            prev = 'region'
            sn = 'interest region'
        else:
            prev = 'time'
            sn = 'date'

        if prev != None:
            dispatcher.utter_message(text="Would you like to change {}?".format(sn))

        return [SlotSet("prev", prev)]

class ActionChangeLast(Action):

    def name(self) -> Text:
        return "action_change_last"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        return [SlotSet("requested_slot", tracker.get_slot('prev')), SlotSet(tracker.get_slot('prev'), None)]

class ActionSelecting(Action):

    def name(self) -> Text:
        return "action_selecting"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        index = int(tracker.get_slot('choice')) - 1
        search_id = tracker.get_slot('search_id')
        vaccines = db.searches[search_id]
        vaccine = vaccines[index]
        
        dispatcher.utter_message(text="Selected option in structure {} on {} at {}.\nWould you like to book for this?".format(vaccine['place'], vaccine['time'], vaccine['details']))

        return []

class ValidateSelectingForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_selecting_form"

    def validate_choice(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        search_id = tracker.get_slot('search_id')
        vaccines = db.searches[search_id]
        
        if slot_value < 1 or slot_value > len(vaccines):
            return {"choice": slot_value}

        # if return from already made choice
        if tracker.latest_message['intent']['name'] == 'deny':
            return {"choice": None}
        else:
            return {"choice": slot_value}

class ActionList(Action):

    def name(self) -> Text:
        return "action_list"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        search_id = tracker.get_slot('search_id')
        vaccines = db.searches[search_id]
        
        if len(vaccines) == 0:
            dispatcher.utter_message(text="No options found for date {}.\nDo you want to search for other dates?".format((datetime.datetime.strptime(tracker.get_slot('time'), '%Y-%m-%dT%H:%M:%S.%f%z')).strftime("%d %B")))
            return [SlotSet("empty_list", True), SlotSet("time", None)]
        else:
            dispatcher.utter_message(text="Found {} matches.\n".format(len(vaccines)))
            for i in range(len(vaccines)):
                dispatcher.utter_message(text="Option {}: {} on {}.\n".format(i+1, vaccines[i]['place'], vaccines[i]['time']))
            dispatcher.utter_message(text="Select one option.")
            return [SlotSet("empty_list", False)]


class ActionEmail(Action):

    def name(self) -> Text:
        return "action_email"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        index = int(tracker.get_slot('choice')) - 1
        search_id = tracker.get_slot('search_id')
        vaccines = db.searches[search_id]
        vaccine = vaccines[index]
        email = tracker.get_slot("email")
        user_id = tracker.get_slot("id_number")
        db.save_booking(user_id, vaccine)
        dispatcher.utter_message(text="Booking confirmed, email with details sent to {}.".format(email))
        
        return [AllSlotsReset()]

class ValidateEmailForm(FormValidationAction):
    
    def name(self) -> Text:
        return "validate_email_form"
    
    def validate_last_ok(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        if slot_value:
            return {"last_ok": True}
        else:
            return {"last_ok": None, "email": None, "requested_slot": "email"}

class ActionClear(Action):

    def name(self) -> Text:
        return "action_clear"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [AllSlotsReset()]

class ActionBookingDetails(Action):

    def name(self) -> Text:
        return "action_booking_details"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_id = tracker.get_slot("id_number")
        user = db.get_user(user_id)
        vaccine = db.get_user_vaccination(user_id)

        if vaccine:
            dispatcher.utter_message(text="User {} has a reservation in structure {} on {} at {}.".format(user['first_name'] + " " + user['last_name'], vaccine['place'], vaccine['time'], vaccine['details']))
            return [SlotSet("empty_booking", False)]
        else:
            dispatcher.utter_message(text="User {} has no reservation.".format(user['first_name'] + " " + user['last_name']))
            return [SlotSet("empty_booking", True)]            
                
class ValidateDetailsForm(FormValidationAction):
    
    def name(self) -> Text:
        return "validate_details_form"
    
    def validate_id_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        user = db.get_user(slot_value)
        if user != None:
            return {"id_number": slot_value}
        else:
            dispatcher.utter_message(text="No user with id {} was found.".format(slot_value))
            return {"id_number": None}

class ActionBookingDelete(Action):

    def name(self) -> Text:
        return "action_booking_delete"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_id = tracker.get_slot("id_number")
        success = db.remove_user_vaccination(user_id)

        if success:
            dispatcher.utter_message(text="Booking was canceled with success.")
        else:
            dispatcher.utter_message(text="No bookings were found for the user.")

        return [AllSlotsReset()]

class ValidateDeleteForm(FormValidationAction):
    
    def name(self) -> Text:
        return "validate_delete_form"
    
    def validate_id_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        user = db.get_user(slot_value)
        if user != None:
            return {"id_number": slot_value}
        else:
            dispatcher.utter_message(text="No user with id {} was found.".format(slot_value))
            return {"id_number": None}

class ActionRepeat(Action):
    def name(self) -> Text:
        return "action_repeat"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        for i in range(1, 10):
            if tracker.events[-i]['event'] == 'bot' and tracker.events[-i]['text'] != None:
                dispatcher.utter_message(text=tracker.events[-i]['text'])
                break
        return [UserUtteranceReverted()]