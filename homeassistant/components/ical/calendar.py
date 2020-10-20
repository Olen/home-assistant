"""Support for iCal-URLs."""

import copy
import logging

from homeassistant.components.calendar import (
    ENTITY_ID_FORMAT,
    CalendarEventDevice,
    calculate_offset,
    is_offset_reached,
)
from homeassistant.const import CONF_NAME, CONF_URL
from homeassistant.helpers.entity import generate_entity_id

from . import ICalEvents
from .const import CONF_DAYS, CONF_MAX_EVENTS, DOMAIN

_LOGGER = logging.getLogger(__name__)
OFFSET = "!!"


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the iCal Calendar platform."""
    config = config_entry.data
    _LOGGER.debug("Running setup_platform for calendar")
    _LOGGER.debug(f"Conf: {config}")
    name = config.get(CONF_NAME)
    url = config.get(CONF_URL)
    days = int(config.get(CONF_DAYS))
    max_events = int(config.get(CONF_MAX_EVENTS))

    entity_id = generate_entity_id(ENTITY_ID_FORMAT, DOMAIN + " " + name, hass=hass)

    ical_events = ICalEvents(hass, url, max_events, days)

    calendar = ICalCalendarEventDevice(hass, name, entity_id, ical_events)

    async_add_entities([calendar], True)


class ICalCalendarEventDevice(CalendarEventDevice):
    """A device for getting the next Task from a WebDav Calendar."""

    def __init__(self, hass, name, entity_id, ical_events):
        """Create the iCal Calendar Event Device."""
        self.entity_id = entity_id
        self._event = None
        self._name = name
        self._offset_reached = False
        self.ical_events = ical_events

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        return {"offset_reached": self._offset_reached}

    @property
    def event(self):
        """Return the next upcoming event."""
        return self._event

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    async def async_get_events(self, hass, start_date, end_date):
        """Get all events in a specific time frame."""
        _LOGGER.debug("Running ICalCalendarEventDevice async get events")
        return await self.ical_events.async_get_events(hass, start_date, end_date)

    async def async_update(self):
        """Update event data."""
        _LOGGER.debug("Running ICalCalendarEventDevice async update")
        await self.ical_events.update()
        event = copy.deepcopy(self.ical_events.event)
        _LOGGER.debug(f"Event 1: {event}")
        if event is None:
            self._event = event
            return
        event = calculate_offset(event, OFFSET)
        _LOGGER.debug(f"Event 2: {event}")
        self._event = copy.deepcopy(event)
        self._event["start"] = {}
        self._event["end"] = {}
        self._event["start"]["dateTime"] = event["start"].isoformat()
        self._event["end"]["dateTime"] = event["end"].isoformat()
        _LOGGER.debug(f"Event 3: {self._event}")
        self._offset_reached = is_offset_reached(self._event)
