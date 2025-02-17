#!/usr/bin/env python

from gi.repository import GLib 
import platform
import logging
import sys
import os
from time import sleep, time
import json
import configparser  # for config/ini file
import _thread

# import Victron Energy packages
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "ext", "velib_python"))
from vedbus import VeDbusService
from ve_utils import get_vrm_portal_id  


# get values from config.ini file
try:
    config_file = (os.path.dirname(os.path.realpath(__file__))) + "/config.ini"
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)

        #if config["MQTT"]["broker_address"] == "IP_ADDR_OR_FQDN":
        #    print('ERROR:The "config.ini" is using invalid default values like IP_ADDR_OR_FQDN. The driver restarts in 60 seconds.')
        #    sleep(60)
        #    sys.exit()
    else:
        print('ERROR:The "' + config_file + '" is not found. Did you copy or rename the "config.sample.ini" to "config.ini"? The driver restarts in 60 seconds.')
        sleep(60)
        sys.exit()

except Exception:
    exception_type, exception_object, exception_traceback = sys.exc_info()
    file = exception_traceback.tb_frame.f_code.co_filename
    line = exception_traceback.tb_lineno
    print(f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}")
    print("ERROR:The driver restarts in 60 seconds.")
    sleep(60)
    sys.exit()


# Get logging level from config.ini
# ERROR = shows errors only
# WARNING = shows ERROR and warnings
# INFO = shows WARNING and running functions
# DEBUG = shows INFO and data/values
if "DEFAULT" in config and "logging" in config["DEFAULT"]:
    if config["DEFAULT"]["logging"] == "DEBUG":
        logging.basicConfig(level=logging.DEBUG)
    elif config["DEFAULT"]["logging"] == "INFO":
        logging.basicConfig(level=logging.INFO)
    elif config["DEFAULT"]["logging"] == "ERROR":
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.WARNING)

# set variables
connected = 0
last_changed = 0
last_updated = 0

# formatting
def _a(p, v):
    return str("%.1f" % v) + "A"

def _ah(p, v):
    return str("%.1f" % v) + "Ah"

def _n(p, v):
    return str("%i" % v)

def _p(p, v):
    return str("%i" % v) + "%"

def _s(p, v):
    return str("%s" % v)

def _t(p, v):
    return str("%.1f" % v) + "°C"

def _v(p, v):
    return str("%.2f" % v) + "V"

def _v3(p, v):
    return str("%.3f" % v) + "V"

def _w(p, v):
    return str("%i" % v) + "W"


battery_dict = {
    # general data
    "/Dc/0/Power": {"value": None, "textformat": _w},
    "/Dc/0/Voltage": {"value": None, "textformat": _v},
    "/Dc/0/Current": {"value": None, "textformat": _a},
    "/Dc/0/Temperature": {"value": None, "textformat": _t},
    "/InstalledCapacity": {"value": None, "textformat": _ah},
    "/ConsumedAmphours": {"value": None, "textformat": _ah},
    "/Capacity": {"value": None, "textformat": _ah},
    "/Soc": {"value": None, "textformat": _p},
    "/TimeToGo": {"value": None, "textformat": _n},
    # alarms
    "/Alarms/LowVoltage": {"value": 0, "textformat": _n},
    "/Alarms/HighVoltage": {"value": 0, "textformat": _n},
    "/Alarms/LowSoc": {"value": 0, "textformat": _n},
    "/Alarms/HighChargeCurrent": {"value": 0, "textformat": _n},
    "/Alarms/HighDischargeCurrent": {"value": 0, "textformat": _n},
    "/Alarms/HighCurrent": {"value": 0, "textformat": _n},
    "/Alarms/CellImbalance": {"value": 0, "textformat": _n},
    "/Alarms/HighChargeTemperature": {"value": 0, "textformat": _n},
    "/Alarms/LowChargeTemperature": {"value": 0, "textformat": _n},
    "/Alarms/LowCellVoltage": {"value": 0, "textformat": _n},
    "/Alarms/LowTemperature": {"value": 0, "textformat": _n},
    "/Alarms/HighTemperature": {"value": 0, "textformat": _n},
    "/Alarms/FuseBlown": {"value": 0, "textformat": _n},
    # info
    "/Info/ChargeRequest": {"value": None, "textformat": _n},
    "/Info/MaxChargeVoltage": {"value": None, "textformat": _v},
    "/Info/MaxChargeCurrent": {"value": None, "textformat": _a},
    "/Info/MaxDischargeCurrent": {"value": None, "textformat": _a},
    # history
    "/History/ChargeCycles": {"value": None, "textformat": _n},
    "/History/MinimumVoltage": {"value": None, "textformat": _v},
    "/History/MaximumVoltage": {"value": None, "textformat": _v},
    "/History/TotalAhDrawn": {"value": None, "textformat": _ah},
    # system
    "/System/MinVoltageCellId": {"value": None, "textformat": _s},
    "/System/MinCellVoltage": {"value": None, "textformat": _v3},
    "/System/MaxVoltageCellId": {"value": None, "textformat": _s},
    "/System/MaxCellVoltage": {"value": None, "textformat": _v3},
    "/System/MinTemperatureCellId": {"value": None, "textformat": _s},
    "/System/MinCellTemperature": {"value": None, "textformat": _t},
    "/System/MaxTemperatureCellId": {"value": None, "textformat": _s},
    "/System/MaxCellTemperature": {"value": None, "textformat": _t},
    "/System/NrOfCellsPerBattery": {"value": 0, "textformat": _n},
    "/System/NrOfModulesOnline": {"value": 1, "textformat": _n},
    "/System/NrOfModulesOffline": {"value": 0, "textformat": _n},
    "/System/NrOfModulesBlockingCharge": {"value": 0, "textformat": _n},
    "/System/NrOfModulesBlockingDischarge": {"value": 0, "textformat": _n},
}

ignore_list = [
    "/FirmwareVersion",
    "/HardwareVersion",
    "/Connected",
    "/CustomName",
    "/DeviceInstance",
    "/DeviceName",
    "/ErrorCode",
    "/Family",
    "/Manufacturer",
    "/Mgmt/Connection",
    "/Mgmt/ProcessName",
    "/Mgmt/ProcessVersion",
    "/ProductId",
    "/ProductName",
    "/Serial",
    "/Info/ChargeModeDebug",
    "/Info/ChargeModeDebugFloat",
    "/Info/ChargeModeDebugBulk",
    "/History/CanBeCleared",
    "/History/Clear",
]

class DbusMqttBatteryService:
    def __init__(
        self,
        servicename,
        deviceinstance,
        paths,
        productname="Proxy BMS",
        customname="Proxy BMS",
        connection="Proxy BMS service",
    ):

        self._dbusservice = VeDbusService(servicename, register=False)
        self._paths = paths

        logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path("/Mgmt/ProcessName", __file__)
        self._dbusservice.add_path(
            "/Mgmt/ProcessVersion",
            "Unkown version, and running on Python " + platform.python_version(),
        )
        self._dbusservice.add_path("/Mgmt/Connection", connection)

        # Create the mandatory objects
        self._dbusservice.add_path("/DeviceInstance", deviceinstance)
        self._dbusservice.add_path("/ProductId", 0xFFFF)
        self._dbusservice.add_path("/ProductName", productname)
        self._dbusservice.add_path("/CustomName", customname)
        self._dbusservice.add_path("/FirmwareVersion", "1.0.1-dev (20250217)")
        # self._dbusservice.add_path('/HardwareVersion', '')
        self._dbusservice.add_path("/Connected", 1)

        self._dbusservice.add_path("/Latency", None)

        for path, settings in self._paths.items():
            self._dbusservice.add_path(
                path,
                settings["value"],
                gettextcallback=settings["textformat"],
                writeable=True,
                onchangecallback=self._handlechangedvalue,
            )

        # register VeDbusService after all paths where added
        self._dbusservice.register()

        GLib.timeout_add(1000, self._update)  # pause 1000ms before the next request

    def _update(self):

        global last_changed, last_updated

        now = int(time())

        if last_changed != last_updated:

            last_updated = last_changed

        # increment UpdateIndex - to show that new data is available
        index = self._dbusservice["/UpdateIndex"] + 1  # increment index
        if index > 255:  # maximum value of the index
            index = 0  # overflow from 255 to 0
        self._dbusservice["/UpdateIndex"] = index
        return True

    def _handlechangedvalue(self, path, value):
        logging.debug("someone else updated %s to %s" % (path, value))
        return True  # accept the change


def main():
    _thread.daemon = True  # allow the program to quit

    from dbus.mainloop.glib import (
        DBusGMainLoop,
    )  # pyright: ignore[reportMissingImports]

    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)

    paths_dbus = {
        "/UpdateIndex": {"value": 0, "textformat": _n},
    }
    paths_dbus.update(battery_dict)

    DbusMqttBatteryService(
        servicename="com.victronenergy.battery.proxy_bms_" + str(config["DEFAULT"]["device_instance"]),
        deviceinstance=int(config["DEFAULT"]["device_instance"]),
        customname=config["DEFAULT"]["device_name"],
        paths=paths_dbus,
    )

    logging.info("Connected to dbus and switching over to GLib.MainLoop() (= event based)")
    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()
