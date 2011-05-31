#!/usr/bin/python
# -*- coding: utf-8 -*-
from twisted.internet import reactor
from twisted.python import log

from functools import partial
import sys, os
import gobject, dbus, dbus.service
from dbus.exceptions import DBusException
from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)

PATH="/net/aircable/pairing"

from settings import getSettings
settings=getSettings()

def getPIN(address, dongle):
    return settings.getPIN(address)

def handle_name_owner_changed(own, old, new):
    if own.startswith('org.bluez'):
        if new is None or len(str(new))==0:
            log.msg( "bluez has gone down, time to get out")
        else:
            log.msg( "bluez started, time to restart")

def registerAgent(bus, path):
    try:
        adapter = dbus.Interface(bus.get_object("org.bluez", path),
            "org.bluez.Adapter")
        adapter.RegisterAgent(PATH, "KeyboardOnly")
        Agent.listeners.append(path)
        log.msg("adapter registered for path %s" % path)
    except DBusException, err:
        if "org.bluez.Error.AlreadyExists" == err.get_dbus_name():
            log.msg("Can't register pairing agent for %s" % path)
            Agent.bus_non_available=True
            return False
        log.err(err)
    return True

def handle_adapter_added(path, signal, bus):
    log.msg("bluez.%s: %s" % (signal, path))
    registerAgent(bus, path)

def handle_adapter_removed(path, signal):
    log.msg("adapter removed %s" % path)
    if path in Agent.listeners: Agent.listeners.pop(path)

class Rejected(dbus.DBusException):
    _dbus_error_name = "org.bluez.Error.Rejected"

class Agent(dbus.service.Object):
    listeners = list()
    exit_on_release = True
    instance = None

    def __init__(self, *args, **kwargs):
        dbus.service.Object.__init__(self, *args, **kwargs)
        self.bus = self._connection
        self.path = self._object_path

    def set_exit_on_release(self, exit_on_release):
        self.exit_on_release = exit_on_release

    def log(self, message):
        log.msg("%s: %s" % (self.path, message))

    @dbus.service.method("org.bluez.Agent",
            in_signature="", out_signature="")
    def Release(self):
        self.log("Agent Release")
        self.bus._unregister_object_path(self.path)
        if self.exit_on_release:
            self.log("Exiting from loop")
            reactor.stop()

    @dbus.service.method("org.bluez.Agent",
                  in_signature="os", out_signature="")
    def Authorize(self, device, uuid):
        self.log("Authorize (%s, %s)" % (device, uuid))

    @dbus.service.method("org.bluez.Agent",
                in_signature="o", out_signature="s")
    def RequestPinCode(self, path):
        self.log("RequestPinCode (%s)" % path)
        device = dbus.Interface(self.bus.get_object("org.bluez", path),
                "org.bluez.Device")
        dongle = dbus.Interface(self.bus.get_object("org.bluez",
            device.GetProperties()['Adapter']),
            "org.bluez.Adapter")
        device=str(device.GetProperties()['Address'])
        dongle=str(dongle.GetProperties()['Address'])
        pin=getPIN(device, dongle)
        self.log("RequestPinCode (%s->%s): %s" % (dongle, device, pin))
        return pin

    @dbus.service.method("org.bluez.Agent",
            in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        self.log("RequestPasskey (%s): %s" % (device, PIN) )
        return dbus.UInt32(PIN)

    @dbus.service.method("org.bluez.Agent",
            in_signature="ou", out_signature="")
    def DisplayPasskey(self, device, passkey):
        self.log("DisplayPasskey (%s, %d)" % (device, passkey))

    @dbus.service.method("org.bluez.Agent",
            in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        self.log("RequestConfirmation (%s, %d)" % (device, passkey))
        device = dbus.Interface(self.bus.get_object("org.bluez", device),
                "org.bluez.Device")
        dongle = dbus.Interface(self.bus.get_object("org.bluez",
            device.GetProperties()['Adapter']),
            "org.bluez.Adapter")
        device=str(device.GetProperties()['Address'])
        dongle=str(dongle.GetProperties()['Address'])
        pin=getPIN(device, dongle)
        if passkey == pin:
            self.log("passkey matches")
            return
        self.log("passkey doesn't match")
        raise Rejected("Passkey doesn't match")

    @dbus.service.method("org.bluez.Agent",
            in_signature="s", out_signature="")
    def ConfirmModeChange(self, mode):
        self.log("ConfirmModeChange (%s)" % (mode))

    @dbus.service.method("org.bluez.Agent",
            in_signature="", out_signature="")
    def Cancel(self):
        self.log("Cancel")

    @dbus.service.method(dbus_interface="net.aircable.airi.Pair",
            in_signature='', out_signature='b')
    def isRegistered(self):
        return len(Agent.listeners)>0


def registerControlSignals(bus):
    bus.add_signal_receiver(handle_name_owner_changed,
        'NameOwnerChanged',
        'org.freedesktop.DBus',
        'org.freedesktop.DBus',
        '/org/freedesktop/DBus')

    bus.add_signal_receiver(
            partial(handle_adapter_added, bus=bus),
            signal_name='AdapterAdded',
            dbus_interface='org.bluez.Manager',
            member_keyword='signal')

    bus.add_signal_receiver(handle_adapter_removed,
            signal_name='AdapterRemoved',
            dbus_interface='org.bluez.Manager',
            member_keyword='signal')

def initAgent(bus):
    try:
        manager = dbus.Interface(bus.get_object("org.bluez", "/"),
                "org.bluez.Manager")
        f = True
        for path in manager.ListAdapters():
            if not registerAgent(bus, path):
                f=False
        if f:
            log.msg("Agent registered on all paths")
    except Exception, err:
        log.err("Something went wrong on the agent application")
        log.err(err)

def main():
    try:
        bus = dbus.SessionBus()
        manager = dbus.Interface(bus.get_object("org.bluez", "/"),
                "org.bluez.Manager")
        log.msg("Using session bus")
    except Exception, err:
        print err
        bus = dbus.SystemBus()
        log.msg("Using system bus")
    registerControlSignals(bus)
    agent = Agent(bus, PATH)
    agent.set_exit_on_release(False)
    initAgent(bus)

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    reactor.callWhenRunning(main)
    reactor.run()
    log.msg("Agent is exiting")

