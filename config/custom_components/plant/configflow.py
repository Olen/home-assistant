"""Config flow for Custom Plant integration."""

import voluptuous as vol

from homeassistant import config_entries, data_entry_flow
from homeassistant.helpers.selector import selector

from .const import DOMAIN


@config_entries.HANDLERS.register(DOMAIN)
class PlantConfigFlow(data_entry_flow.FlowHandler):
    """Handle a config flow for Plants."""

    VERSION = 1

    def __init__(self):
        self.init_info = None

    async def async_step_init(self, user_input=None):
        """Initiate the config flow"""
        errors = {}
        if user_input is not None:
            # Validate user input
            valid = await self.validate_step_1(user_input)
            if valid:
                # Store info to use in next step
                self.init_info = user_input
                # Return the form of the next step
                return await self.async_step_limits()

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        # Specify items in the order they are to be displayed in the UI
        data_schema = {
            vol.Required("Plant name"): str,
        }
        data_schema = {
            vol.Required("Plant species"): str,
        }
        data_schema["temperature_sensor"] = selector(
            {"entity": {"device_class": "temperature"}}
        )
        data_schema["moisture_sensor"] = selector(
            {"entity": {"device_class": "humidity"}}
        )
        data_schema["conductivity_sensor"] = selector({"entity": {"domain": "sensor"}})
        data_schema["light_sensor"] = selector(
            {"entity": {"device_class": "illuminance"}}
        )

        return self.async_show_form(step_id="init", data_schema=vol.Schema(data_schema))

    async def async_step_limits(self):
        """Handle max/min values"""
        data_schema = {
            vol.Required("Max moisture"): int,
        }
        return self.async_show_form(
            step_id="limits", data_schema=vol.Schema(data_schema)
        )

    async def validate_step_1(self, user_input):
        """Validate step one"""
        return True
