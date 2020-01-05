# -*- coding: utf-8 -*-

# *************************************************************************
# Ecuador contabilidad
# Localización para Odoo V12
# Por: OODCA © <2019> <José Enríquez>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# *************************************************************************

{
    'name': "Facturación Ecuador",
    'version': '1.1',
    'author': 'OODCA',
    'category': 'Localization',
    'website': "http://www.oodca.com",
    'summary': """
        Talonario de facturación SRI
        """,

    'description': """
Este módulo instala la facturación ecuatoriana de acuerdo a las normas del SRI
==============================================================================

Usar exclusivamente en Odoo V12 para la localización de:

    * Sociedades (SO), y
    * Personas Naturales Obligadas a llevar contabilidad (PNO)

Desarrollado por: **José Ernesto Enríquez Jurado**
""",
    'depends': [
        'base',
        'account',
        'account_invoice_fiscal_position_update',
        'l10n_ec_partner'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/customer_invoice_views.xml',
        'views/supplier_invoice_views.xml',
        'views/journal_invoice_views.xml',
        'views/sequence_invoice_views.xml',
        'views/edocument_invoice_views.xml',
        'views/edocument_email_template.xml',
        'views/edocument_email_lc_template.xml',
        'reports/report.xml',
        'reports/report_retention.xml',
        'reports/report_out_invoice.xml',
        'reports/report_out_refund.xml',
        'reports/report_purchase_clearance.xml',
    ],
}
