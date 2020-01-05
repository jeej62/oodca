# -*- coding: utf-8 -*-
from odoo import http

# class L10nEcComprobantes(http.Controller):
#     @http.route('/l10n_ec_comprobantes/l10n_ec_comprobantes/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_ec_comprobantes/l10n_ec_comprobantes/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_ec_comprobantes.listing', {
#             'root': '/l10n_ec_comprobantes/l10n_ec_comprobantes',
#             'objects': http.request.env['l10n_ec_comprobantes.l10n_ec_comprobantes'].search([]),
#         })

#     @http.route('/l10n_ec_comprobantes/l10n_ec_comprobantes/objects/<model("l10n_ec_comprobantes.l10n_ec_comprobantes"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_ec_comprobantes.object', {
#             'object': obj
#         })