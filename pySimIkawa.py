"""Example of how to create a Peripheral device/GATT Server"""
# Standard modules
from enum import IntEnum
import logging
import struct


from RoasterBLE import BLEPeripheral
from RoasterState import IkawaEmulatedRoaster

from bluezero import adapter


def main(adapter_address):
    emulated_roaster = IkawaEmulatedRoaster()

    BLERoaster = BLEPeripheral(adapter_address,emulated_roaster)
    BLERoaster.publish()


if __name__ == '__main__':
    # Get the default adapter address and pass it to main
    main(list(adapter.Adapter.available())[0].address)
