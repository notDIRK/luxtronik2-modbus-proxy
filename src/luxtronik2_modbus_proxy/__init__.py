"""Luxtronik 2.0 to Modbus TCP proxy.

Translates the proprietary Luxtronik binary protocol (port 8889) to standard
Modbus TCP (port 502), enabling evcc, Home Assistant, and other Modbus-capable
tools to control older heat pumps that lack native Modbus support.
"""

__version__ = "0.1.0"
