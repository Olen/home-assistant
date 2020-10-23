"""Test the OpenPlantBook config flow."""
from homeassistant import config_entries, setup
from homeassistant.components.openplantbook.const import DOMAIN

from tests.async_mock import patch


async def test_form(hass):
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.openplantbook.async_setup", return_value=True
    ) as mock_setup, patch(
        "homeassistant.components.openplantbook.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "client_id": "test-client-id",
                "secret": "test-secret",
            },
        )

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Openplantbook API"
    assert result2["data"] == {
        "client_id": "test-client-id",
        "secret": "test-secret",
    }
    await hass.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
