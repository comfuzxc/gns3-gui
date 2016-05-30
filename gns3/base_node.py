# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Base class for node classes.
"""

from .qt import QtCore
from .controller import Controller
from .ports.port import Port


import logging
log = logging.getLogger(__name__)


class BaseNode(QtCore.QObject):

    """
    BaseNode implementation.

    :param module: Module instance
    :param server: client connection to a server
    :param project: Project instance
    """

    # signals used to let the GUI know about some events.
    created_signal = QtCore.Signal(int)
    started_signal = QtCore.Signal()
    stopped_signal = QtCore.Signal()
    suspended_signal = QtCore.Signal()
    updated_signal = QtCore.Signal()
    loaded_signal = QtCore.Signal()
    deleted_signal = QtCore.Signal()
    delete_links_signal = QtCore.Signal()
    error_signal = QtCore.Signal(int, str)
    warning_signal = QtCore.Signal(int, str)
    server_error_signal = QtCore.Signal(int, str)

    _instance_count = 1
    _allocated_names = set()

    # node statuses
    stopped = 0
    started = 1
    suspended = 2

    # node categories
    routers = 0
    switches = 1
    end_devices = 2
    security_devices = 3

    def __init__(self, module, compute, project):

        super().__init__()
        # create an unique ID
        self._id = BaseNode._instance_count
        BaseNode._instance_count += 1

        self._module = module
        self._compute = compute
        self._project = project
        self._initialized = False
        self._loading = False
        self._status = BaseNode.stopped
        self._ports = []
        self._links = set()

    def links(self):
        """
        Links connected to the node
        """
        return self._links

    def addLink(self, link):
        self._links.add(link)

    def deleteLink(self, link):
        self._links.remove(link)

    @classmethod
    def reset(cls):
        """
        Reset the instance count.
        """

        cls._instance_count = 1
        cls._allocated_names.clear()

    def allocateName(self, base_name):
        """
        Allocates a new name for a node.

        :param base_name: base name for the node which will be completed with a
        unique number

        :returns: allocated name or None if one could not be found
        """

        for number in range(1, 100000):
            if '{0}' in base_name or '{id}' in base_name:
                name = base_name.format(number, id=number)
            else:
                name = base_name + str(number)
            if name not in self._allocated_names:
                self._allocated_names.add(name)
                return name
        return None

    def removeAllocatedName(self):
        """
        Removes an allocated name from a node.
        """

        if self.name() in self._allocated_names:
            self._allocated_names.remove(self.name())

    def updateAllocatedName(self, name):
        """
        Updates a name for a node.

        :param name: new node name
        """

        self.removeAllocatedName()
        self._allocated_names.add(name)

    def setName(self, name):
        """
        Set a name for a node.

        :param name: node name
        """

        self._allocated_names.add(name)

    def hasAllocatedName(self, name):
        """
        Returns either a name is already allocated or not.

        :param name: node name

        :returns: boolean
        """

        if name in self._allocated_names:
            return True
        return False

    def module(self):
        """
        Returns this node module.

        :returns: Module instance
        """

        return self._module

    def compute(self):
        """
        Returns this node compute.

        :returns: Compute instance
        """
        return self._compute

    def project(self):
        """
        Returns this node project.

        :returns: Project instance
        """

        return self._project

    def id(self):
        """
        Returns this node identifier.

        :returns: node identifier (integer)
        """

        return self._id

    def setId(self, new_id):
        """
        Sets an identifier for this node.

        :param new_id: node identifier (integer)
        """

        self._id = new_id

        # update the instance count to avoid conflicts
        if new_id >= BaseNode._instance_count:
            BaseNode._instance_count = new_id + 1

    def status(self):
        """
        Returns the status of this node.
        0 = stopped, 1 = started, 2 = suspended.

        :returns: node status (integer)
        """

        return self._status

    def setStatus(self, status):
        """
        Sets a status for this node.
        0 = stopped, 1 = started, 2 = suspended.

        :param status: node status (integer)
        """

        if status == self._status:
            return
        self._status = status
        if status == self.started:
            for port in self._ports:
                # set ports as started
                port.setStatus(Port.started)
            self.started_signal.emit()
        elif status == self.stopped:
            for port in self._ports:
                # set ports as stopped
                port.setStatus(Port.stopped)
            self.stopped_signal.emit()
        elif status == self.suspended:
            for port in self._ports:
                # set ports as suspended
                port.setStatus(Port.suspended)
            self.suspended_signal.emit()

    def initialized(self):
        """
        Returns if the node has been initialized

        :returns: boolean
        """

        return self._initialized

    def setInitialized(self, initialized):
        """
        Sets if the node has been initialized

        :param initialized: boolean
        """

        self._initialized = initialized

    def dump(self):
        """
        Returns a representation of this node.
        Must be overloaded.

        :returns: dictionary
        """

        raise NotImplementedError()

    def load(self, node_info):
        """
        Loads a node representation
        (from a topology file).
        Must be overloaded.

        :param node_info: representation of the node (dictionary)
        """

        raise NotImplementedError()

    def update(self, new_settings):
        """
        Updates the settings for this node.
        Must be overloaded.

        :param new_settings: settings dictionary
        """

        raise NotImplementedError()

    def ports(self):
        """
        Returns all the ports for this node.

        :returns: list of Port instances
        """

        return self._ports

    @staticmethod
    def defaultCategories():
        """
        Returns the default categories.

        :returns: dict
        """

        categories = {"Routers": BaseNode.routers,
                      "Switches": BaseNode.switches,
                      "End devices": BaseNode.end_devices,
                      "Security devices": BaseNode.security_devices}

        return categories

    def configPage(self):
        """
        Returns the configuration page widget to be used by the node properties dialog.
        Must be overloaded.

        :returns: QWidget instance
        """

        raise NotImplementedError()

    @staticmethod
    def defaultSymbol():
        """
        Returns the default symbol path for this node.
        Must be overloaded.

        :returns: symbol path (or resource).
        """

        raise NotImplementedError()

    @staticmethod
    def symbolName():
        """
        Returns the symbol name (for the nodes view).

        :returns: name (string)
        """

        raise NotImplementedError()

    @staticmethod
    def categories(self):
        """
        Returns the node categories the node is part of (used by the device panel).

        :returns: list of node category (integer)
        """

        raise NotImplementedError()

    def __str__(self):
        """
        Must be overloaded.
        """

        raise NotImplementedError()

    def controllerHttpPost(self, path, callback, body={}, context={}, **kwargs):
        """
        POST on current server / project

        :param path: Remote path
        :param callback: callback method to call when the server replies
        :param body: params to send (dictionary)
        :param context: Pass a context to the response callback
        """

        self._project.post(path, callback, body=body, context=context, **kwargs)

    def controllerHttpPut(self, path, callback, body={}, context={}, **kwargs):
        """
        PUT on current server / project

        :param path: Remote path
        :param callback: callback method to call when the server replies
        :param body: params to send (dictionary)
        :param context: Pass a context to the response callback
        """

        self._project.put(path, callback, body=body, context=context, **kwargs)

    def controllerHttpGet(self, path, callback, context={}, **kwargs):
        """
        Get on current server / project

        :param path: Remote path
        :param callback: callback method to call when the server replies
        :param body: params to send (dictionary)
        :param context: Pass a context to the response callback
        """

        self._project.get(path, callback, context=context, **kwargs)


    def controllerHttpDelete(self, path, callback, context={}, **kwargs):
        """
        Delete on current server / project

        :param path: Remote path
        :param callback: callback method to call when the server replies
        :param context: Pass a context to the response callback
        """

        self._project.delete(path, callback, context=context, **kwargs)
