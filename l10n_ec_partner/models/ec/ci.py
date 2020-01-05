# -*- coding: utf-8 -*-

# *************************************************************************
# Ecuador Partner
# Localización para Odoo V12
# Por: Jeej © <2019> <José Enríquez>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Library:  stdnum (library) for ecuador (ec)
# *************************************************************************

# ci.py - functions for handling Ecuadorian personal identity codes
#
# Copyright (C) 2014 Jonathan Finlay
# Copyright (C) 2014-2017 Arthur de Jong
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA

# CI (Cédula de identidad, Ecuadorian personal identity code).

# The CI is a 10 digit number used to identify Ecuadorian citizens.

# **************************************************************
# Library:  stdnum (library) for ecuador (ec)
# CALLS:    import
# Notes:    Imports clean
# **************************************************************
from .util import clean
# ***************************************************************
# Library:  stdnum (library) for ecuador (ec)
# function: is_valid(number)
# Notes:    Check if the number provided is a valid CI number.
#           Initiate the proccess
# ***************************************************************
def is_valid(number):
    try:
        return bool(validate(number))
    except ValueError:
        return False
# ***************************************************************
# Library:  stdnum (library) for ecuador (ec)
# function: validate(number)
# Notes:    Check if the number provided is a valid CI number.
#           This checks the length, is number, range, and sum 
# ***************************************************************
def validate(number):
    number = compact(number)
    if len(number) != 10:
        raise
    if not number.isdigit():
        raise
    if number[:2] < '01' or number[:2] > '24':
        raise
    if number[2] > '5':
        raise
    if _checksum(number) != 0:
        raise
    return number
# ***************************************************************
# Library:  stdnum (library) for ecuador (ec)
# function: compact(number)
# Notes:    Convert the number to the minimal representation.
#           This strips the number of any valid separators and 
#           removes surrounding whitespace.
# ***************************************************************
def compact(number):
    return clean(number, ' -').upper().strip()
# ***************************************************************
# Library:  stdnum (library) for ecuador (ec)
# function: _checksum(number)
# Notes:    Calculate a checksum over the number using Module 10
# ***************************************************************
def _checksum(number):
    """Calculate a checksum over the number."""
    fold = lambda x: x - 9 if x > 9 else x
    return sum(fold((2, 1)[i % 2] * int(n))
               for i, n in enumerate(number)) % 10





