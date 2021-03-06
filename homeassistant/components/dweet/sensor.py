"""Support for showing values from Dweet.io."""
import json
import logging
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME, CONF_VALUE_TEMPLATE, CONF_UNIT_OF_MEASUREMENT, CONF_DEVICE)
from homeassistant.helpers.entity import Entity

REQUIREMENTS = ['dweepy==0.3.0']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Dweet.io Sensor'

SCAN_INTERVAL = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICE): cv.string,
    vol.Required(CONF_VALUE_TEMPLATE): cv.template,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Dweet sensor."""
    import dweepy

    name = config.get(CONF_NAME)
    device = config.get(CONF_DEVICE)
    value_template = config.get(CONF_VALUE_TEMPLATE)
    unit = config.get(CONF_UNIT_OF_MEASUREMENT)
    if value_template is not None:
        value_template.hass = hass

    try:
        content = json.dumps(dweepy.get_latest_dweet_for(device)[0]['content'])
    except dweepy.DweepyError:
        _LOGGER.error("Device/thing %s could not be found", device)
        return

    if value_template.render_with_possible_json_value(content) == '':
        _LOGGER.error("%s was not found", value_template)
        return

    dweet = DweetData(device)

    add_entities([DweetSensor(hass, dweet, name, value_template, unit)], True)


class DweetSensor(Entity):
    """Representation of a Dweet sensor."""

    def __init__(self, hass, dweet, name, value_template, unit_of_measurement):
        """Initialize the sensor."""
        self.hass = hass
        self.dweet = dweet
        self._name = name
        self._value_template = value_template
        self._state = None
        self._unit_of_measurement = unit_of_measurement

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def state(self):
        """Return the state."""
        return self._state

    def update(self):
        """Get the latest data from REST API."""
        self.dweet.update()

        if self.dweet.data is None:
            self._state = None
        else:
            values = json.dumps(self.dweet.data[0]['content'])
            self._state = self._value_template.render_with_possible_json_value(
                values, None)


class DweetData:
    """The class for handling the data retrieval."""

    def __init__(self, device):
        """Initialize the sensor."""
        self._device = device
        self.data = None

    def update(self):
        """Get the latest data from Dweet.io."""
        import dweepy

        try:
            self.data = dweepy.get_latest_dweet_for(self._device)
        except dweepy.DweepyError:
            _LOGGER.warning("Device %s doesn't contain any data", self._device)
            self.data = None
