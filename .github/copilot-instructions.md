# PVCast-Core AI Instructions

## Architecture Overview

PVCast-core is a **photovoltaic forecasting library** that predicts solar power generation using weather data and PV system models. It's designed as part of a larger Home Assistant ecosystem for solar energy management.

### Core Components
- **SystemManager**: Central orchestrator requiring `PVCAST_CONFIG` environment variable pointing to YAML config
- **Plant Models**: Wrapper around pvlib ModelChain supporting both string and micro-inverter systems
- **Weather APIs**: Factory pattern for weather data sources (HomeAssistant, ClearOutside)
- **Atmospheric Utils**: Cloud cover to irradiance conversion using pvlib algorithms

### Key Relationships
```mermaid
SystemManager → ConfigReader → Plant Models
SystemManager → WeatherAPIFactory → Weather Sources
Plant Models → pvlib.ModelChain (one per inverter in micro systems)
```

## Development Patterns

### Factory Registration Pattern
Weather APIs self-register using the factory pattern:
```python
# At module bottom:
API_FACTORY.register("clearoutside", ClearOutside, SCHEMA)
```

### Test Configuration System
- Use `@pytest.mark.parametrize` with `indirect=True` for fixture-based test configurations
- Plant fixtures determine `simple` mode by checking for `ac_power` in config
- Location fixtures use tuple unpacking: `(lat, lon, tz, altitude)`
- Example: `@pytest.mark.parametrize("micro_plant", [CONFIG_MICRO_DICT], indirect=True)`

### Error Handling Patterns
- Weather API parsing uses BeautifulSoup with specific CSS selectors
- Plant models gracefully handle pvlib ModelChain errors by setting AC power to 0
- Missing weather columns trigger warnings but don't fail execution
- All validation uses voluptuous schemas

## Critical Development Workflows

### Environment Setup
```bash
# Required environment variable
export PVCAST_CONFIG="path/to/config.yaml"

# Development commands
uv run pytest                    # Run tests
uv run ruff check --fix         # Lint and autofix
uv run ruff format              # Format code
```

### Testing Patterns
- Tests automatically reset `PVCAST_CONFIG` via `autouse` fixture
- Use `monkeypatch` for mocking pvlib internals: `monkeypatch.setattr("pvlib.modelchain.ModelChain.run_model", mock_func)`
- Weather data fixtures require DatetimeIndex with UTC timezone
- Test both error paths and happy paths for weather parsing

### Configuration Structure
```yaml
general:
  weather:
    sources: [{name: "CO", type: "clearoutside"}]
  location: {latitude: 52.35, longitude: 4.88, timezone: "Europe/Amsterdam"}

plant:
  - name: "EastWest"
    arrays: [{name: "East", tilt: 30, azimuth: 90, module: "...", inverter: "..."}]
```

## Project-Specific Conventions

### PV System Modeling
- **String plants**: One ModelChain per plant
- **Micro plants**: One ModelChain per individual inverter (calculated from `nr_inverters`)
- **Simple mode**: When `ac_power` present in config, bypasses detailed modeling
- Weather data requires irradiance conversion: `cloud_cover_to_irradiance()` before plant runs

### Module/Inverter Validation
- Uses pvlib's CEC database: `retrieve_sam("CECMod")` and `retrieve_sam("CECInverter")`
- Invalid names raise `KeyError` with message "Invalid {type} in configuration: {name}"

### Data Flow Requirements
1. Weather data → Cloud cover to irradiance conversion
2. Add precipitable water with `add_precipitable_water()`
3. Validate DatetimeIndex with UTC timezone
4. Run plant model → Results DataFrame with 'ac' column

### File Organization
- `src/pvcast/`: Main package
- `tests/const.py`: Shared test configurations (CONFIG_MICRO_DICT, etc.)
- `tests/conftest.py`: Global fixtures and MockWeatherAPI
- Weather APIs in `src/pvcast/weather/` with HTML test data in `tests/data/`

## Integration Points

### PVLib Dependencies
- Heavy reliance on pvlib for solar calculations
- Location objects: `pvlib.location.Location(lat, lon, tz, altitude)`
- ModelChain wrapping with temperature models from `TEMPERATURE_MODEL_PARAMETERS`

### External Weather Sources
- ClearOutside: HTML scraping with BeautifulSoup, regex parsing for timestamps
- HomeAssistant: REST API integration (configuration only, implementation pending)
- All sources implement abstract `WeatherAPI.retrieve_new_data() -> pd.DataFrame`

### Testing Integration
- Mock external APIs with `responses` library
- Use real HTML fixtures for parsing edge cases
- Extensive parametrized testing across multiple plant configurations and locations

## Code Style Conventions

### Comments
- Avoid excessive commenting - code should be self-explanatory
- Comments should start with lowercase letters, not capitalized
- Only add comments for complex business logic or non-obvious implementation details

Remember: Always validate plant configurations against pvlib's CEC database and ensure weather DataFrames have proper DatetimeIndex before model execution.
