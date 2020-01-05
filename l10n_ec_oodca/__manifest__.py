# -*- coding: utf-8 -*-

# *************************************************************************
# Ecuador contabilidad para Sociedades y Personas Naturales Obligadas
# Localización para Odoo V12
# Por: OODCA © <2019> <José Enríquez>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# *************************************************************************

{
    'name': 'Contabilidad OODCA',
    'version': '1.1',
    'author': 'OODCA',
    'category': 'Localization',
    'website': "http://www.oodca.com",
    'summary': """
        Plan de cuentas e impuestos
        """,
    'description': """
Este módulo instala la base contable ecuatoriana contemplada en las NIIFs
=========================================================================

Usar exclusivamente en Odoo V12 para la localización de:

	* Sociedades (SO), y
	* Personas Naturales Obligadas a llevar contabilidad (PNO)

*Plan de cuentas contables según formato exigido para la presentación de estados financieros anuales por la Superintendencia de Compañías ecuatoriana (actualización 2018).
Tablas de impuestos y posiciones fiscales normadas por el Servicio de Rentas Internas del Ecuador SRI (actualización 2019)*

Desarrollado por: **José Ernesto Enríquez Jurado**
""",
    'depends': [
        'account',
        'base_iban',
    ],
    'data': [
        'data/account_group.xml',
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/account_chart_template_account_account_link.xml',
        'data/account_data.xml',
        'data/account_tax_data.xml',
        'data/account_fiscal_position_template_data.xml',
        'data/account_chart_template_configure_data.xml',
    ],
}
