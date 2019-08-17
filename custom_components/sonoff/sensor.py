<<<<<<< Updated upstream
import logging, time, hmac, hashlib, random, base64, json, socket

from datetime import timedelta
from homeassistant.util import Throttle
from homeassistant.components.sensor import DOMAIN
# from homeassistant.components.sonoff import (DOMAIN as SONOFF_DOMAIN, SonoffDevice)
from custom_components.sonoff import (DOMAIN as SONOFF_DOMAIN, SonoffDevice)
from homeassistant.const import TEMP_CELSIUS

SCAN_INTERVAL = timedelta(seconds=10)

_LOGGER = logging.getLogger(__name__)

SONOFF_SENSORS_MAP = {
    'power'                 : { 'eid' : 'power',       'uom' : 'W',            'icon' : 'mdi:flash-outline' },
    'current'               : { 'eid' : 'current',     'uom' : 'A',            'icon' : 'mdi:current-ac' },
    'voltage'               : { 'eid' : 'voltage',     'uom' : 'V',            'icon' : 'mdi:power-plug' },
    'currentHumidity'       : { 'eid' : 'humidity',    'uom' : '%',            'icon' : 'mdi:water-percent' },
    'currentTemperature'    : { 'eid' : 'temperature', 'uom' : TEMP_CELSIUS,   'icon' : 'mdi:thermometer' },
    'water'                 : { 'eid' : 'water',       'uom' : 'W',            'icon' : 'mdi:water-percent' },
    'state'                 : { 'eid' : 'state',       'uom' : 'W',            'icon' : 'mdi:help' },
    'lightswitch'           : { 'eid' : 'lightswitch', 'uom' : 'W',            'icon' : 'mdi:lightbulb' },
    'lightBcolor'           : { 'eid' : 'lightBcolor', 'uom' : 'X',            'icon' : 'mdi:palette' },
    'lightGcolor'           : { 'eid' : 'lightGcolor', 'uom' : 'X',            'icon' : 'mdi:palette' },
    'lightRcolor'           : { 'eid' : 'lightRcolor', 'uom' : 'X',            'icon' : 'mdi:palette' },
    'lightbright'           : { 'eid' : 'lightbright', 'uom' : '%',            'icon' : 'mdi:lightbulb-on' },
    'lightmode'             : { 'eid' : 'lightmode',   'uom' : 'W',            'icon' : 'mdi:theme-light-dark' },
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Add the Sonoff Sensor entities"""
 
    entities = []
    for device in hass.data[SONOFF_DOMAIN].get_devices(force_update = True):
        # as far as i know only 1-switch devices seem to have sensor-like capabilities
        
        if 'params' not in device.keys(): continue # this should never happen... but just in case

        for sensor in SONOFF_SENSORS_MAP.keys():
            if device['params'].get(sensor) and device['params'].get(sensor) != "unavailable":
                entity = SonoffSensor(hass, device, sensor)
                entities.append(entity) 
    
    if len(entities):
        async_add_entities(entities, update_before_add=False)

class SonoffSensor(SonoffDevice):
    """Representation of a Sonoff sensor."""

    def __init__(self, hass, device, sensor = None):
        """Initialize the device."""
        SonoffDevice.__init__(self, hass, device)
        self._sensor        = sensor
        self._name          = '{} {}'.format(device['name'], SONOFF_SENSORS_MAP[self._sensor]['eid'])
        self._attributes    = {}
  
    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return SONOFF_SENSORS_MAP[self._sensor]['uom']

    @property
    def state(self):
       """Return the state of the sensor."""
       return self.get_device()['params'].get(self._sensor)

    # entity id is required if the name use other characters not in ascii
    @property
    def entity_id(self):
        """Return the unique id of the switch."""
        entity_id = "{}.{}_{}_{}".format(DOMAIN, SONOFF_DOMAIN, self._deviceid, SONOFF_SENSORS_MAP[self._sensor]['eid'])
        return entity_id

    @property
    def icon(self):
        """Return the icon."""
        return SONOFF_SENSORS_MAP[self._sensor]['icon']
=======
"""
Sensor for checking the status of Hue sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.hue/
"""
import asyncio
import async_timeout
import logging
import threading
from datetime import timedelta

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval

DEPENDENCIES = ["hue"]

__version__ = "1.5"

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=0.1)
TYPE_GEOFENCE = "Geofence"
ICONS = {"SML": "mdi:run", "RWL": "mdi:remote", "ZGP": "mdi:remote", "FOH": "mdi:light-switch"}
DEVICE_CLASSES = {"SML": "motion"}
ATTRS = {
    "SML": [
        "light_level",
        "battery",
        "last_updated",
        "lx",
        "dark",
        "daylight",
        "temperature",
        "on",
        "reachable",
        "sensitivity",
        "threshold",
    ],
    "RWL": ["last_updated", "battery", "on", "reachable"],
    "ZGP": ["last_updated"],
    "FOH": ["last_updated"]
}


def parse_hue_api_response(sensors):
    """Take in the Hue API json response."""
    data_dict = {}  # The list of sensors, referenced by their hue_id.

    # Loop over all keys (1,2 etc) to identify sensors and get data.
    for sensor in sensors:
        modelid = sensor["modelid"][0:3]
        if modelid in ["RWL", "SML", "ZGP"]:
            _key = modelid + "_" + sensor["uniqueid"][:-5]
            if modelid == "RWL":
                data_dict[_key] = parse_rwl(sensor)
            elif modelid == "ZGP":
                data_dict[_key] = parse_zgp(sensor)

        elif modelid == 'FOH': ############# New Model ID
            _key = modelid + '_' + sensor['uniqueid'][-5:] ###needed for uniqueness
            data_dict[_key] = parse_foh(sensor)

    return data_dict


def parse_zgp(response):
    """Parse the json response for a ZGPSWITCH Hue Tap."""
    TAP_BUTTONS = {34: "1_click", 16: "2_click", 17: "3_click", 18: "4_click"}
    press = response["state"]["buttonevent"]
    if press is None or press not in TAP_BUTTONS:
        button = "No data"
    else:
        button = TAP_BUTTONS[press]

    data = {
        "model": "ZGP",
        "name": response["name"],
        "state": button,
        "last_updated": response["state"]["lastupdated"].split("T"),
    }
    return data


def parse_rwl(response):
    """Parse the json response for a RWL Hue remote."""

    """
        I know it should be _released not _up
        but _hold_up is too good to miss isn't it
    """
    responsecodes = {"0": "_click", "1": "_hold", "2": "_click_up", "3": "_hold_up"}

    button = None
    if response["state"]["buttonevent"]:
        press = str(response["state"]["buttonevent"])
        button = str(press)[0] + responsecodes[press[-1]]

    data = {
        "model": "RWL",
        "name": response["name"],
        "state": button,
        "battery": response["config"]["battery"],
        "on": response["config"]["on"],
        "reachable": response["config"]["reachable"],
        "last_updated": response["state"]["lastupdated"].split("T"),
    }
    return data


def parse_foh(response):
    """Parse the JSON response for a FOHSWITCH (type still = ZGPSwitch)"""
    FOH_BUTTONS = {
        16: 'left_upper_press',
        20: 'left_upper_release',
        17: 'left_lower_press',
        21: 'left_lower_release',
        18: 'right_lower_press',
        22: 'right_lower_release',
        19: 'right_upper_press',
        23: 'right_upper_release',
        100: 'double_upper_press',
        101: 'double_upper_release',
        98: 'double_lower_press',
        99: 'double_lower_release'
    }
    
    press = response['state']['buttonevent']
    if press is None or press not in FOH_BUTTONS:
        button = 'No data'
    else:
        button =FOH_BUTTONS[press]

    data = {'model':'FOH',
            'name': response['name'],
            'state': button,
            'last_updated': response['state']['lastupdated'].split('T')}
    return data


def get_bridges(hass):
    from homeassistant.components import hue
    from homeassistant.components.hue.bridge import HueBridge

    return [
        entry
        for entry in hass.data[hue.DOMAIN].values()
        if isinstance(entry, HueBridge) and entry.api
    ]


async def update_api(api):
    import aiohue

    try:
        with async_timeout.timeout(10):
            await api.update()
    except (asyncio.TimeoutError, aiohue.AiohueException) as err:
        _LOGGER.debug("Failed to fetch sensors: %s", err)
        return False
    return True


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Initialise Hue Bridge connection."""
    data = HueSensorData(hass, async_add_entities)
    await data.async_update_info()
    async_track_time_interval(hass, data.async_update_info, SCAN_INTERVAL)


class HueSensorData(object):
    """Get the latest sensor data."""

    def __init__(self, hass, async_add_entities):
        """Initialize the data object."""
        self.hass = hass
        self.lock = threading.Lock()
        self.data = {}
        self.sensors = {}
        self.async_add_entities = async_add_entities

    async def update_bridge(self, bridge):
        available = await update_api(bridge.api.sensors)
        if not available:
            return

        data = parse_hue_api_response(
            sensor.raw
            for sensor in bridge.api.sensors.values()
            if sensor.type != TYPE_GEOFENCE
        )

        new_sensors = data.keys() - self.data.keys()
        updated_sensors = []
        for key, new in data.items():
            new['changed'] = True
            old = self.data.get(key)
            if not old or old == new:
                continue
            updated_sensors.append(key)
            if (
                old["last_updated"] == new["last_updated"]
                and old["state"] == new["state"]
            ):
                new['changed'] = False
        self.data.update(data)

        new_entities = {
            entity_id: HueSensor(entity_id, self) for entity_id in new_sensors
        }
        if new_entities:
            _LOGGER.debug("Created %s", ", ".join(new_entities.keys()))
            self.sensors.update(new_entities)
            self.async_add_entities(new_entities.values(), True)
        for entity_id in updated_sensors:
            self.sensors[entity_id].async_schedule_update_ha_state()

    async def async_update_info(self, now=None):
        """Get the bridge info."""
        locked = self.lock.acquire(False)
        if not locked:
            return
        try:
            bridges = get_bridges(self.hass)
            if not bridges:
                if now:
                    # periodic task
                    await asyncio.sleep(5)
                return
            await asyncio.wait(
                [self.update_bridge(bridge) for bridge in bridges], loop=self.hass.loop
            )
        finally:
            self.lock.release()


class HueSensor(Entity):
    """Class to hold Hue Sensor basic info."""

    ICON = "mdi:run-fast"

    def __init__(self, hue_id, data):
        """Initialize the sensor object."""
        self._hue_id = hue_id
        self._data = data.data  # data is in .data

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the sensor."""
        data = self._data.get(self._hue_id)
        if data:
            return data["name"]

    @property
    def state(self):
        """Return the state of the sensor."""
        data = self._data.get(self._hue_id)
        if data and data["changed"]:
            return data["state"]

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        data = self._data.get(self._hue_id)
        if data:
            icon = ICONS.get(data["model"])
            if icon:
                return icon
        return self.ICON

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        data = self._data.get(self._hue_id)
        if data:
            device_class = DEVICE_CLASSES.get(data["model"])
            if device_class:
                return device_class

    @property
    def device_state_attributes(self):
        """Attributes."""
        data = self._data.get(self._hue_id)
        if data:
            return {key: data.get(key) for key in ATTRS.get(data["model"], [])}
>>>>>>> Stashed changes
