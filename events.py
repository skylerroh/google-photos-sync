from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import date, timedelta
import datetime
import json
from typing import List
import pprint

@dataclass_json
@dataclass
class Event:
    name: str
    start_date: date
    end_date: date

    def __post_init__(self):
        if (isinstance(self.start_date, str)):
            self.start_date = datetime.datetime.strptime(self.start_date, "%Y-%m-%d")
        if (isinstance(self.end_date, str)):
            self.end_date = datetime.datetime.strptime(self.end_date, "%Y-%m-%d")


    def all_dates(self):
        return [self.start_date + timedelta(days=i) for i in range(0, (self.end_date - self.start_date).days + 1)]

class EventList:
    def __init__(self, events: List[Event]):
        self.sorted_events = sorted(events, key=lambda x: (x.start_date, x.end_date))
        self.event_index = {}
        for event in self.sorted_events:
            self.event_index.update({date.strftime("%Y-%m-%d"): event for date in event.all_dates()})

    def find_event(self, date: datetime):
        return self.event_index.get(date.strftime("%Y-%m-%d"))

    def __repr__(self):
        return "\n".join([i.__repr__() for i in self.sorted_events])

class EventLoader:
    @staticmethod
    def load_events(path):
        with open(path, 'r') as f:
            data = json.load(f)
        return {album_and_events["album_name"]: EventList([Event.from_dict(event) for event in album_and_events["events"]])
                for album_and_events
                in data}