from re import I
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor
from esphome.const import (
    CONF_ID,
    DEVICE_CLASS_EMPTY,
    STATE_CLASS_MEASUREMENT,
    UNIT_EMPTY,
    UNIT_METER,
)


# DEPENDENCIES = ["i2c"]
AUTO_LOAD = ["sensor", "binary_sensor", "text_sensor"]
MULTI_CONF = True

CONF_ROODE_ID = "roode_id"

roode_ns = cg.esphome_ns.namespace("roode")
Roode = roode_ns.class_("Roode", cg.PollingComponent)

CONF_ROI_HEIGHT = "roi_height"
CONF_ROI_WIDTH = "roi_width"
CONF_ADVISED_SENSOR_ORIENTATION = "advised_sensor_orientation"
CONF_CALIBRATION = "calibration"
CONF_ROI_CALIBRATION = "roi_calibration"
CONF_INVERT_DIRECTION = "invert_direction"
CONF_MAX_THRESHOLD_PERCENTAGE = "max_threshold_percentage"
CONF_MIN_THRESHOLD_PERCENTAGE = "min_threshold_percentage"
CONF_MANUAL_THRESHOLD = "manual_threshold"
CONF_THRESHOLD_PERCENTAGE = "threshold_percentage"
CONF_RESTORE_VALUES = "restore_values"
CONF_I2C_ADDRESS = "i2c_address"
CONF_SENSOR_MODE = "sensor_mode"
CONF_MANUAL = "manual"
CONF_MANUAL_ACTIVE = "manual_active"
CONF_CALIBRATION_ACTIVE = "calibration_active"
CONF_TIMING_BUDGET = "timing_budget"
CONF_USE_SAMPLING = "use_sampling"
CONF_ROI = "roi"
CONF_ROI_ACTIVE = "roi_active"
CONF_SENSOR_OFFSET_CALIBRATION = "sensor_offset_calibration"
CONF_SENSOR_XTALK_CALIBRATION = "sensor_xtalk_calibration"
TYPES = [
    CONF_RESTORE_VALUES,
    CONF_INVERT_DIRECTION,
    CONF_ADVISED_SENSOR_ORIENTATION,
    CONF_I2C_ADDRESS,
    CONF_USE_SAMPLING,
]
CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(Roode),
        cv.Optional(CONF_INVERT_DIRECTION, default="false"): cv.boolean,
        cv.Optional(CONF_RESTORE_VALUES, default="false"): cv.boolean,
        cv.Optional(CONF_ADVISED_SENSOR_ORIENTATION, default="true"): cv.boolean,
        cv.Optional(CONF_USE_SAMPLING, default="true"): cv.boolean,
        cv.Optional(CONF_I2C_ADDRESS, default=0x29): cv.uint8_t,
        cv.Exclusive(
            CONF_CALIBRATION,
            "mode",
            f"Only one mode, {CONF_MANUAL} or {CONF_CALIBRATION} is usable",
        ): cv.Schema(
            {
                cv.Optional(CONF_CALIBRATION_ACTIVE, default="true"): cv.boolean,
                cv.Optional(CONF_MAX_THRESHOLD_PERCENTAGE, default=85): cv.int_range(
                    min=50, max=100
                ),
                cv.Optional(CONF_MIN_THRESHOLD_PERCENTAGE, default=0): cv.int_range(
                    min=0, max=100
                ),
                cv.Optional(CONF_ROI_CALIBRATION, default="false"): cv.boolean,
                cv.Optional(CONF_SENSOR_OFFSET_CALIBRATION, default=-1): cv.int_,
                cv.Optional(CONF_SENSOR_XTALK_CALIBRATION, default=-1): cv.int_,
            }
        ),
        cv.Exclusive(
            CONF_MANUAL,
            "mode",
            f"Only one mode, {CONF_MANUAL} or {CONF_CALIBRATION} is usable",
        ): cv.Schema(
            {
                cv.Optional(CONF_MANUAL_ACTIVE, default="true"): cv.boolean,
                cv.Optional(CONF_TIMING_BUDGET, default=10): cv.int_range(
                    min=10, max=1000
                ),
                cv.Inclusive(
                    CONF_SENSOR_MODE,
                    "manual_mode",
                    f"{CONF_SENSOR_MODE}, {CONF_ROI_HEIGHT}, {CONF_ROI_WIDTH} and {CONF_MANUAL_THRESHOLD} must be used together",
                ): cv.int_range(min=-1, max=3),
                cv.Inclusive(
                    CONF_MANUAL_THRESHOLD,
                    "manual_mode",
                    f"{CONF_SENSOR_MODE}, {CONF_ROI_HEIGHT}, {CONF_ROI_WIDTH} and {CONF_MANUAL_THRESHOLD} must be used together",
                ): cv.int_range(min=40, max=4000),
            }
        ),
        cv.Optional(CONF_ROI): cv.Schema(
            {
                cv.Optional(CONF_ROI_ACTIVE, default="true"): cv.boolean,
                cv.Optional(CONF_ROI_HEIGHT, default=16): cv.int_range(min=4, max=16),
                cv.Optional(CONF_ROI_WIDTH, default=6): cv.int_range(min=4, max=16),
            }
        ),
    }
).extend(cv.polling_component_schema("100ms"))


def validate_roi_settings(config):
    roi = config.get(CONF_ROI)
    manual = config.get(CONF_MANUAL)
    if CONF_CALIBRATION in config:
        roi_calibration = config.get(CONF_CALIBRATION).get(CONF_ROI_CALIBRATION)
        if roi_calibration == True and roi != None:
            raise cv.Invalid(
                "ROI calibration cannot be used with manual ROI width and height"
            )
        if roi_calibration == False and roi == None:
            raise cv.Invalid("You need to set the ROI manually or use ROI calibration")
    if manual != None and roi == None:
        raise cv.Invalid("You need to set the ROI manually if manual mode is active")


async def setup_conf(config, key, hub):
    if key in config:
        cg.add(getattr(hub, f"set_{key}")(config[key]))


def setup_manual_mode(config, hub):
    manual = config[CONF_MANUAL]
    for key in manual:
        cg.add(getattr(hub, f"set_{key}")(manual[key]))


def setup_calibration_mode(config, hub):
    calibration = config[CONF_CALIBRATION]
    for key in calibration:
        cg.add(getattr(hub, f"set_{key}")(calibration[key]))


def setup_manual_roi(config, hub):
    roi = config[CONF_ROI]
    for key in roi:
        cg.add(getattr(hub, f"set_{key}")(roi[key]))


async def to_code(config):
    hub = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(hub, config)
    cg.add_library("EEPROM", None)
    cg.add_library("Wire", None)
    cg.add_library("rneurink", "1.2.3", "VL53L1X_ULD")

    validate_roi_settings(config)

    for key in TYPES:
        await setup_conf(config, key, hub)
    if CONF_MANUAL in config:
        setup_manual_mode(config, hub)
    if CONF_CALIBRATION in config:
        setup_calibration_mode(config, hub)
