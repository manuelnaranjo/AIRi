#!/usr/bin/python
# -*- coding: utf-8 -*-
#testing pairing service

import gobject

import sys, os
import dbus, dbus.service, dbus.mainloop.glib
from twisted.python import log

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

def registerAgent(path):
  adapter = dbus.Interface(bus.get_object("org.bluez", path),
    "org.bluez.Adapter")
  adapter.RegisterAgent(PATH, "KeyboardOnly")
  log.msg("adapter registered for path %s" % path)


def handle_adapter_added(path, signal):
  log.msg("bluez.%s: %s" % (signal, path))
  registerAgent(path)

def handle_adapter_removed(path, signal):
  log.msg("adapter removed %s" % path)

class Rejected(dbus.DBusException):
  _dbus_error_name = "org.bluez.Error.Rejected"

class Agent(dbus.service.Object):
  exit_on_release = True

  def set_exit_on_release(self, exit_on_release):
    self.exit_on_release = exit_on_release

  @dbus.service.method("org.bluez.Agent",
    in_signature="", out_signature="")
  def Release(self):
    log.msg("Agent Release")
    if self.exit_on_release:
      log.msg("Exiting from loop")
      mainloop.quit()

  @dbus.service.method("org.bluez.Agent",
				  in_signature="os", out_signature="")
  def Authorize(self, device, uuid):
      log.msg("Authorize (%s, %s)" % (device, uuid))

  @dbus.service.method("org.bluez.Agent",
    in_signature="o", out_signature="s")
  def RequestPinCode(self, path):
    device = dbus.Interface(bus.get_object("org.bluez", path),
      "org.bluez.Device")
    dongle = dbus.Interface(bus.get_object("org.bluez",
		  device.GetProperties()['Adapter']),
	"org.bluez.Adapter")
    device=str(device.GetProperties()['Address'])
    dongle=str(dongle.GetProperties()['Address'])
    pin=getPIN(device, dongle)
    log.msg("RequestPinCode (%s->%s): %s" % (dongle, device, pin) )
    return pin

  @dbus.service.method("org.bluez.Agent",
    in_signature="o", out_signature="u")
  def RequestPasskey(self, device):
    log.msg("RequestPasskey (%s): %s" % (device, PIN) )
    return dbus.UInt32(PIN)

  @dbus.service.method("org.bluez.Agent",
    in_signature="ou", out_signature="")
  def DisplayPasskey(self, device, passkey):
    log.msg("DisplayPasskey (%s, %d)" % (device, passkey))

  @dbus.service.method("org.bluez.Agent",
    in_signature="ou", out_signature="")
  def RequestConfirmation(self, device, passkey):
    log.msg("RequestConfirmation (%s, %d)" % (device, passkey))
    device = dbus.Interface(bus.get_object("org.bluez", device),
      "org.bluez.Device")
    dongle = dbus.Interface(bus.get_object("org.bluez",
	device.GetProperties()['Adapter']),
      "org.bluez.Adapter")
    device=str(device.GetProperties()['Address'])
    dongle=str(dongle.GetProperties()['Address'])
    pin=getPIN(device, dongle)
    if passkey == pin:
	log.msg("passkey matches")
	return
    log.msg("passkey doesn't match")
    raise Rejected("Passkey doesn't match")

  @dbus.service.method("org.bluez.Agent",
    in_signature="s", out_signature="")
  def ConfirmModeChange(self, mode):
    log.msg("ConfirmModeChange (%s)" % (mode))

  @dbus.service.method("org.bluez.Agent",
    in_signature="", out_signature="")
  def Cancel(self):
    log.msg("Cancel")

def registerControlSignals(bus):
  bus.add_signal_receiver(handle_name_owner_changed,
    'NameOwnerChanged',
    'org.freedesktop.DBus',
    'org.freedesktop.DBus',
    '/org/freedesktop/DBus')

  bus.add_signal_receiver(handle_adapter_added,
    signal_name='AdapterAdded',
    dbus_interface='org.bluez.Manager',
    member_keyword='signal')

  bus.add_signal_receiver(handle_adapter_removed,
    signal_name='AdapterRemoved',
    dbus_interface='org.bluez.Manager',
    member_keyword='signal')

def initAgent():
  try:
    manager = dbus.Interface(bus.get_object("org.bluez", "/"),
						      "org.bluez.Manager")
    for path in manager.ListAdapters():
      registerAgent(path)
    log.msg("Agent registered on all paths")
  except Exception, err:
    log.err("Something went wrong on the agent application")
    log.err(err)

if __name__ == '__main__':
  log.startLogging(sys.stdout)

  dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

  try:
    bus = dbus.SessionBus()
    log.msg("Using session bus")
  except:
    bus = dbus.SystemBus()
    log.msg("Using system bus")

  registerControlSignals(bus)
  mainloop = gobject.MainLoop()
  agent = Agent(bus, PATH)
  agent.set_exit_on_release(False)
  initAgent()
  mainloop.run()
  log.msg("Agent is exiting")
