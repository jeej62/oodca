# -*- coding: utf-8 -*-

# *************************************************************************
# Ecuador contabilidad para Sociedades y Personas Naturales Obligadas
# Localización para Odoo V12
# Por: OODCA © <2019> <José Enríquez>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# *************************************************************************

{
    'name': "Comprobantes Contables",
    'version': '1.1',
    'author': 'OODCA',
    'category': 'Localization',
    'website': "http://www.oodca.com",
    'summary': """
        Impresión de Asientos contables
        """,
    'description': """
Este módulo instala varios Reportes contables
=============================================

Usar exclusivamente en Odoo V12 para la localización de:

    * Sociedades (SO), y
    * Personas Naturales Obligadas a llevar contabilidad (PNO)

Desarrollado por: **José Ernesto Enríquez Jurado**
""",
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'report/reports.xml',
        'report/report_account_move.xml',
        'report/report_retention.xml',
        'report/report_out_invoice.xml',
        'report/report_out_refund.xml',
        'report/report_purchase_clearance.xml',
    ],
}
