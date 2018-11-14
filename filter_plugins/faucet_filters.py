#!/usr/bin/python

import string
import re

from jinja2.utils import soft_unicode

from ipaddress import ip_address, ip_network, ip_interface

class FilterModule(object):
    def filters(self):
        return {
            'generate_mac': self.generate_mac_filter,
            'mac_to_link_local': self.mac_to_link_local_filter,
            'to_link_identifier': self.to_link_identifier_filter,
            'map_format': self.map_format,
            'map_vlan': self.map_vlan,
            'sortbylinks': self.sortbylinks,
            'numericsort': self.numericsort,
            'dictnumericsort': self.dictnumericsort,
            'incrementip': self.incrementip,
            'decrementip': self.decrementip,
            'find_ip_in_network': self.find_ip_in_network
        }

    def tryint(self, num):
        try:
            return int(num)
        except ValueError:
            return num

    def alphanum_key(self, item):
        if isinstance(item, tuple):
            # Read the key rather than value
            item = item[0]
        return [self.tryint(c) for c in re.split('([0-9]+)', item)]

    def generate_mac_filter(self, faucet_oui, vlan):
        oui = str(faucet_oui).translate(None, ":.- ")
        device = "{:06}".format(int(vlan))
        eui = oui + device
        return ":".join(eui[i:i+2] for i in range(0, len(eui), 2))

    def mac_to_link_local_filter(self, mac):
        # Remove the most common delimiters; dots, dashes, etc.
        mac_value = int(str(mac).translate(None, ' .:-'), 16)

        # Split out the bytes that slot into the IPv6 address
        # XOR the most significant byte with 0x02, inverting the
        # Universal / Local bit
        high2 = mac_value >> 32 & 0xffff ^ 0x0200
        high1 = mac_value >> 24 & 0xff
        low1 = mac_value >> 16 & 0xff
        low2 = mac_value & 0xffff

        return 'fe80::{:04x}:{:02x}ff:fe{:02x}:{:04x}'.format(
            high2, high1, low1, low2)

    def to_link_identifier_filter(self, number):
        return string.ascii_uppercase[number - 1]

    def map_format(self, value, pattern):
        """
        Apply python string formatting on an object:
        .. sourcecode:: jinja
            {{ "%s - %s"|format("Hello?", "Foo!") }}
                -> Hello? - Foo!
        """
        return soft_unicode(pattern) % (value)

    def map_vlan(self, value):
        return soft_unicode(value.split('-')[0])

    def sortbylinks(self, value):
        return sorted(value.items(), key=lambda x: x[1]['links'][0])

    def numericsort(self, value):
        return sorted(value, key=self.alphanum_key)

    def dictnumericsort(self, value):
        return sorted(value.items(), key=self.alphanum_key)

    def incrementip(self, value, delta):
        return ip_address(value) + delta

    def decrementip(self, value, delta):
        return ip_address(value) - delta

    def find_ip_in_network(self, candidates, network):
        net_interface = ip_interface(network)
        for candidate in candidates:
            candidate_interface = ip_interface(candidate)
            if candidate_interface in net_interface.network:
                return candidate_interface.ip
