# -*- coding: utf-8 -*-

# *************************************************************************
# Ecuador Partners
# Localización para Odoo V12
# Por: Jeej © <2019> <José Enríquez>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Library:  stdnum (library) for ecuador (ec)
# *************************************************************************

# ruc.py - functions for handling Ecuadorian fiscal numbers
#
# Copyright (C) 2014 Jonathan Finlay
# Copyright (C) 2014-2015 Arthur de Jong
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

# RUC (Registro Único de Contribuyentes, Ecuadorian company tax number).

# The RUC is a tax identification number for legal entities. It has 13 digits
# where the third digit is a number denoting the type of entity.

# **************************************************************
# Library:  stdnum (library) for ecuador (ec)
# CALLS:    import
# Notes:    Imports functions from ci
#           Initiate the proccess
# **************************************************************
from . import ci
__all__ = [ 
        'is_valid',
        'validate',
        'compact'  
    ]
# ----- field definition -----
# use the same compact function as CI
compact = ci.compact
# ***************************************************************
# Library:  stdnum (library) for ecuador (ec)
# function: is_valid(number)
# Notes:    Check if the number provided is a valid RUC number.
# ***************************************************************
def is_valid(number):
    """Check if the number provided is a valid RUC number. This checks the
    length, formatting and check digit."""
    try:
        return bool(validate(number))
    except ValueError:
        return False
# ***************************************************************
# Library:  stdnum (library) for ecuador (ec)
# function: validate(number)
# Notes:    Check if the number provided is a valid RUC number.
#           This checks the length, is number, range, and sum 
# ***************************************************************
def validate(number):
    number = compact(number)
    if len(number) != 13:
        raise ValueError
    if not number.isdigit():
        raise ValueError
    if number[:2] < '01' or number[:2] > '24':
        raise ValueError
        # 3th digit 7 & 8 not used on ecuadorian RUC and CI
    if number[2] == '7' or number[2] == '8':
        raise ValueError
        # 0..5 = natural RUC: CI plus establishment number
    if number[2] < '6':
        if number[-3:] == '000':
            raise ValueError
        ci.validate(number[:10])
        # 6 = public RUC
    elif number[2] == '6':
        if number[-4:] == '0000':
            raise ValueError
        if _checksum(number[:9], (3, 2, 7, 6, 5, 4, 3, 2, 1)) != 0:
            raise ValueError
        # 9 = juridical RUC
    elif number[2] == '9':
        if number[-3:] == '000':
            raise ValueError
        if _checksum(number[:10], (4, 3, 2, 7, 6, 5, 4, 3, 2, 1)) != 0:
            raise ValueError
    else:
        raise ValueError
    return number
# ****************************************************************
# Library:  stdnum (library) for ecuador (ec)
# function: _checksum(number)
# Notes:    Calculate a checksum over the number given the weights
#           using Module 11.
# ****************************************************************
def _checksum(number, weights):
    return sum(w * int(n) for w, n in zip(weights, number)) % 11

