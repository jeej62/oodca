# -*- coding: utf-8 -*-

# *************************************************************************
# Ecuador Partner
# Localización para Odoo V12
# Por: Jeej © <2019> <José Enríquez>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# *************************************************************************

# **************************************************************
# CALLS:    try, import
# Notes:    Imports from stdnum (library) for ecuador (ec)
# **************************************************************
try:
    from stdnum import ec
except ImportError:
    from . import ec
# ***************************************************************
# function: validar_numero_identidad(self)
# Notes:    routes proccess to cedula or ruc functions
# ***************************************************************
def validar_numero_identidad(numero_identidad, tipo_identidad):
    if tipo_identidad == 'cedula':
        return ec.ci.is_valid(numero_identidad)
    elif tipo_identidad == 'ruc':
        return ec.ruc.is_valid(numero_identidad)
    else:
        return True
