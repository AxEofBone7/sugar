# Copyright (C) 2006, Owen Williams.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import time
import logging

import gobject
import dbus

from sugar.graphics.xocolor import XoColor
from sugar.presence import presenceservice
from sugar import profile

class HomeActivity(gobject.GObject):
    """Activity which appears in the "Home View" of the Sugar shell
    
    This class stores the Sugar Shell's metadata regarding a
    given activity/application in the system.  It interacts with
    the sugar.activity.* modules extensively in order to 
    accomplish its tasks.
    """
    __gsignals__ = {
        'launch-timeout':          (gobject.SIGNAL_RUN_FIRST,
                                    gobject.TYPE_NONE, 
                                   ([])),
    }

    def __init__(self, bundle, activity_id):
        """Initialise the HomeActivity
        
        bundle -- sugar.activity.bundle.Bundle instance,
            provides the information required to actually
            create the new instance.  This is, in effect,
            the "type" of activity being created.
        activity_id -- unique identifier for this instance
            of the activity type
        """
        gobject.GObject.__init__(self)
        self._window = None
        self._xid = None
        self._service = None
        self._activity_id = activity_id
        self._bundle = bundle

        self._launch_time = time.time()
        self._launched = False
        self._launch_timeout_id = gobject.timeout_add(
                                    20000, self._launch_timeout_cb)

        logging.debug("Activity %s (%s) launching..." %
                      (self._activity_id, self.get_type))

    def __del__(self):
        gobject.source_remove(self._launch_timeout_id)
        self._launch_timeout_id = 0

    def _launch_timeout_cb(self, user_data=None):
        """Callback for launch operation timeouts
        """
        logging.debug("Activity %s (%s) launch timed out" %
                      (self._activity_id, self.get_type))
        self._launch_timeout_id = 0
        self.emit('launch-timeout')
        return False

    def set_window(self, window):
        """An activity is 'launched' once we get its window."""
        logging.debug("Activity %s (%s) finished launching" %
                      (self._activity_id, self.get_type))
        self._launched = True
        gobject.source_remove(self._launch_timeout_id)
        self._launch_timeout_id = 0

        if self._window or self._xid:
            raise RuntimeError("Activity is already launched!")
        if not window:
            raise ValueError("window must be valid")

        self._window = window
        self._xid = window.get_xid()

    def set_service(self, service):
        self._service = service

    def get_service(self):
        """Retrieve the application's sugar introspection service
        
        Note that non-native Sugar applications will not have
        such a service, so the return value will be None in
        those cases.
        """
        return self._service

    def get_title(self):
        """Retrieve the application's root window's suggested title"""
        if not self._launched:
            raise RuntimeError("Activity is still launching.")
        return self._window.get_name()

    def get_icon_name(self):
        """Retrieve the bundle's icon (file) name"""
        return self._bundle.get_icon()
    
    def get_icon_color(self):
        """Retrieve the appropriate icon colour for this activity
        
        Uses activity_id to index into the PresenceService's 
        set of activity colours, if the PresenceService does not
        have an entry (implying that this is not a Sugar-shared application)
        uses the local user's profile.get_color() to determine the
        colour for the icon.
        """
        pservice = presenceservice.get_instance()
        activity = pservice.get_activity(self._activity_id)
        if activity != None:
            return XoColor(activity.get_color())
        else:
            return profile.get_color()
        
    def get_activity_id(self):
        """Retrieve the "activity_id" passed in to our constructor
        
        This is a "globally likely unique" identifier generated by
        sugar.util.unique_id
        """
        return self._activity_id

    def get_xid(self):
        """Retrieve the X-windows ID of our root window"""
        if not self._launched:
            raise RuntimeError("Activity is still launching.")
        return self._xid

    def get_window(self):
        """Retrieve the X-windows root window of this application
        
        This was stored by the set_window method, which was 
        called by HomeModel._add_activity, which was called 
        via a callback that looks for all 'window-opened'
        events.
        
        HomeModel currently uses a dbus service query on the
        activity to determine to which HomeActivity the newly
        launched window belongs.
        """
        if not self._launched:
            raise RuntimeError("Activity is still launching.")
        return self._window

    def get_type(self):
        """Retrieve bundle's "service_name" for future reference"""
        return self._bundle.get_service_name()

    def get_shared(self):
        """Return whether this activity is using Presence service sharing"""
        if not self._launched:
            raise RuntimeError("Activity is still launching.")
        return self._service.get_shared()

    def get_launch_time(self):
        """Return the time at which the activity was first launched
        
        Format is floating-point time.time() value 
        (seconds since the epoch)
        """
        return self._launch_time

    def get_launched(self):
        """Return whether we have bound our top-level window yet"""
        return self._launched
