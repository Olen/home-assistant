"""Describe group states."""
from __future__ import annotations

import voluptuous as vol

from config.custom_components.plant import PlantDevice
from homeassistant.components.group import GroupEntity, GroupIntegrationRegistry
from homeassistant.components.sensor import DEVICE_CLASSES_SCHEMA
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_CLASS,
    CONF_ENTITIES,
    CONF_NAME,
    CONF_UNIQUE_ID,
    STATE_OK,
    STATE_PROBLEM,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA_BASE
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN

DEFAULT_NAME = "Plant Group"

CONF_ALL = "all"
REG_KEY = f"{DOMAIN}_registry"

PLATFORM_SCHEMA = PLATFORM_SCHEMA_BASE.extend(
    {
        vol.Required(CONF_ENTITIES): cv.entities_domain(DOMAIN),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_ALL): cv.boolean,
    }
)


@callback
def async_describe_on_off_states(
    hass: HomeAssistant, registry: GroupIntegrationRegistry
) -> None:
    """Describe group on off states."""
    registry.on_off_states({STATE_PROBLEM}, STATE_OK)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Plant Group platform."""
    async_add_entities(
        [
            PlantGroup(
                config.get(CONF_UNIQUE_ID),
                config[CONF_NAME],
                config.get(CONF_DEVICE_CLASS),
                config[CONF_ENTITIES],
                config.get(CONF_ALL),
            )
        ]
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Binary Sensor Group config entry."""
    registry = er.async_get(hass)
    entities = er.async_validate_entity_ids(
        registry, config_entry.options[CONF_ENTITIES]
    )
    mode = config_entry.options[CONF_ALL]

    async_add_entities(
        [PlantGroup(config_entry.entry_id, config_entry.title, None, entities, mode)]
    )


class PlantGroup(GroupEntity):
    """Representation of a BinarySensorGroup."""

    _attr_available: bool = False

    def __init__(
        self,
        unique_id: str | None,
        name: str,
        device_class: str | None,
        entity_ids: list[str],
        mode: str | None,
    ) -> None:
        """Initialize a BinarySensorGroup entity."""
        super().__init__()
        self._entity_ids = entity_ids
        self._attr_name = name
        self._attr_extra_state_attributes = {ATTR_ENTITY_ID: entity_ids}
        self._attr_unique_id = unique_id
        self._device_class = device_class
        self.mode = any
        if mode:
            self.mode = all

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""

        @callback
        def async_state_changed_listener(event: Event) -> None:
            """Handle child updates."""
            self.async_set_context(event.context)
            self.async_defer_or_update_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._entity_ids, async_state_changed_listener
            )
        )

        await super().async_added_to_hass()

    @callback
    def async_update_group_state(self) -> None:
        """Query all members and determine the binary sensor group state."""
        states = [
            state.state
            for entity_id in self._entity_ids
            if (state := self.hass.states.get(entity_id)) is not None
        ]

        # Set group as unavailable if all members are unavailable or missing
        self._attr_available = any(state != STATE_UNAVAILABLE for state in states)

        valid_state = self.mode(
            state not in (STATE_UNKNOWN, STATE_UNAVAILABLE) for state in states
        )
        if not valid_state:
            # Set as unknown if any / all member is not unknown or unavailable
            self._attr_is_on = None
        else:
            # Set as ON if any / all member is OK
            self._attr_is_on = self.mode(state == STATE_OK for state in states)

    @property
    def device_class(self) -> str | None:
        """Return the sensor class of the binary sensor."""
        return self._device_class
