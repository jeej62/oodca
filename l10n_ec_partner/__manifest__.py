# -*- coding: utf-8 -*-

# *************************************************************************
# Ecuador Partner
# Localización para Odoo V12
# Por: OODCA © <2019> <José Enríquez>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# *************************************************************************

{
    'name': "Contactos Ecuador",
    'version': '1.1',
    'author': "OODCA",
    'category': 'Localization',
    'website': "http://www.oodca.com",
    'summary': """
        RUC, cédulas y pasaportes
        """,
    'description': """
Este módulo instala los recursos necesarios para la administración de las identificaciones en el Ecuador
========================================================================================================

Usar exclusivamente en Odoo V12

Para todas las contabilidades

Desarrollado por: **José Ernesto Enríquez Jurado**
    """,
    'depends': [
        'base',
        'account',
        'contacts',
    ],
    'data': [
        'views/partner_views.xml',
        'data/partner.xml',
        'data/res.country.state.csv',
    ],
    'external_dependencies': {
        'python': [
            'stdnum',
        ]
    },
    'installable': True,
}
