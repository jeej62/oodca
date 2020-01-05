# -*- coding: utf-8 -*-


# -------------------------------------------------------------------------
# Ecuador Partner
# Localización para Odoo V12
# Por: Jeej © <2019> <José Enríquez>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -------------------------------------------------------------------------

# --------------------------------------------------------------
# CALLS:    import
# Notes:    Imports api, field, models & exceptions from ODOO
#
# CALLS:    import
# Notes:    Import funtions (def validar_numero_identidad) from 
#           other files (utils)
# ------------------------------
# noinspection PyUnresolvedReferences
from odoo import models, fields, api

# noinspection PyUnresolvedReferences
from odoo.exceptions import (
    ValidationError,
    Warning as UserError
)
from .utils import validar_numero_identidad
import functools
import xmlrpc.client as xmlrpclib

# noinspection PyUnresolvedReferences
from odoo import api, fields, models,  tools
# noinspection PyUnresolvedReferences
from odoo.modules import get_module_resource
import base64
import time
from datetime import datetime
from datetime import timedelta
import pytz


# --------------------------------------------------------------
# CALLS:    import
# LIBRARY:  logging
# Notes:    To show warnings in the terminal or to notify for 
#           extreme problems in the logfile (NOT USED)
# ------------------------------
import logging

logger = logging.getLogger(__name__)


# --------------------------------------------------------------
# CLASS:    ResPartner
# OBJECT:   res.partners    ->  inherit
# Notes:    Modificactions & Calculation on contacts identities
# ------------------------------
class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ----- field definition -----
    numero_identidad = fields.Char(
        size=13,
        help='Número de Identificación (cédula, RUC o pasaporte)'
    )

    # ----- field definition -----
    nombre_comercial = fields.Char()

    # ----- field definition -----
    tipo_identidad = fields.Selection(
        [
            ('cedula', 'CEDULA'),
            ('ruc', 'RUC'),
            ('pasaporte', 'PASAPORTE')
        ],
        string='Tipo ID',
        required=True,
        default='pasaporte',
        help='Tipo de identificación tributaria'
    )

    # ----- field definition -----
    tipo_persona = fields.Selection(
        compute='_compute_tipo_persona',
        selection=[
            ('0', 'ERROR 3er dígito [7,8] NO VALIDO'),
            ('1', 'Entidad Extranjera'),
            ('5', 'Persona Natural'),
            ('6', 'Entidad Pública'),
            ('9', 'Persona Jurídica')
        ],
        string='Tipo Persona',
        help='Tipo de personería tributaria',
        store=True
    )
    update_date = fields.Date(
        string='Ultima actualización',
        readonly=False,
        required=False,
        index=True,
        copy=False,
        states={},
        help=u"Fecha de la última actualización del contacto con información del SRI"
    )

    # --------------------------------------------------------------
    # API:      model_cr_context
    # function: init(self)
    # Notes:    Postgresql -> To create a unique index:
    #                         unique_company_partner_numero_identidad
    #                         on database
    # ------------------------------
    @api.model_cr_context
    def init(self):
        self.update_numero_identidad()
        super(ResPartner, self).init()
        sql_index = """
        CREATE UNIQUE INDEX IF NOT EXISTS
        unique_company_partner_numero_identidad_type on res_partner
        (company_id, tipo_identidad, numero_identidad)
        WHERE tipo_identidad <> 'pasaporte'"""
        self._cr.execute(sql_index)

    # --------------------------------------------------------------
    # API:      multi
    # function: update_numero_identidad(self)
    # Notes:    Postgresql -> To create and update numero_identidad
    #           on database as blank record
    # ------------------------------
    @api.multi
    def update_numero_identidad(self):
        sql = """UPDATE res_partner SET numero_identidad=''
        WHERE numero_identidad is NULL"""
        self.env.cr.execute(sql)

    # --------------------------------------------------------------
    # API:      one
    # function: _check_numero_identidad(self)
    # Notes:    Calls the validation function and gets a boolean
    #           return
    #           Shows a warning box on ValidationError
    # ------------------------------
    @api.one
    @api.constrains('numero_identidad', 'tipo_identidad')
    def _check_numero_identidad(self):
        res = validar_numero_identidad(self.numero_identidad, self.tipo_identidad)
        if not res:
            raise ValidationError('Número de Identificación NO VALIDO')
        return True

    # --------------------------------------------------------------
    # API:      one
    #           depends -> trigger calculations after pointer changes
    # function: _compute_tipo_persona(self)
    # fields:   tipo_identidad
    #           numero_identidad
    #           tipo_persona
    # Notes:    Trigger after field (numero_identidad) changes
    #           This trigger initiates after module start up
    # ------------------------------
    @api.one
    @api.depends('numero_identidad', 'tipo_identidad')
    def _compute_tipo_persona(self):
        if self.numero_identidad:
            if self.tipo_identidad == 'pasaporte':
                self.tipo_persona = '1'
            elif int(self.numero_identidad[2]) in [0, 1, 2, 3, 4, 5]:
                self.tipo_persona = '5'
            elif int(self.numero_identidad[2]) == 6:
                self.tipo_persona = '6'
            elif int(self.numero_identidad[2]) in [7, 8]:
                self.tipo_persona = '0'
            elif int(self.numero_identidad[2]) == 9:
                self.tipo_persona = '9'

    # --------------------------------------------------------------
    # API:      change_numero_identidad
    # function: change_numero_identidad(self)
    # Notes:    Postgresql -> To change the partner fiscal position depending on the
    #                         payment method
    #                         This trigger initiates only when numero_identidad changes
    # ------------------------------
    @api.onchange('numero_identidad', 'tipo_identidad')
    def change_numero_identidad_tipo_identidad(self):
        self.ensure_one()
        FISCAL = self.env['account.fiscal.position']
        fiscal_position = {}

        utc_now = datetime.today()
        pst_now = utc_now.astimezone(pytz.timezone("America/Guayaquil"))
        pst_now_str = pst_now.strftime("%Y-%m-%d")

        try:
            if self.numero_identidad:

                if self.tipo_identidad == 'pasaporte':
                    # -------------------------------------------------------------------------------
                    # RECUPERA DEL DISCO EL ARCHIVO PNG CON LA IMAGEN PREDEFINIDA DE LA SECCION CIIU
                    # -------------------------------------------------------------------------------
                    nombre_archivo_png = get_module_resource('l10n_ec_partner', 'static/src/img', 'ciiu_seccion_PAS.png')
                    # noinspection PyAttributeOutsideInit
                    self.image = self._get_default_image_value(nombre_archivo_png)
                    self.company_type = 'company'

                if self.tipo_identidad == 'ruc' or self.tipo_identidad == 'cedula':

                    if self.tipo_identidad == 'cedula':
                        self.numero_identidad = self.numero_identidad[0:10]
                        self.company_type = 'person'

                        # -------------------------------------------------------------------------------
                        # RECUPERA DEL DISCO EL ARCHIVO PNG CON LA IMAGEN PREDEFINIDA DE LA SECCION CIIU
                        # -------------------------------------------------------------------------------
                        nombre_archivo_png = get_module_resource('l10n_ec_partner', 'static/src/img', 'ciiu_seccion_PN.png')
                        # noinspection PyAttributeOutsideInit
                        self.image = self._get_default_image_value(nombre_archivo_png)

                    # Limita la búsqueda solo a los numeros de identidad cuyos 2 primeros dígitos sean <= 24
                    # y cuyo número de dígitos >=9 (mínimo necesario para realizar una búsqueda certera
                    # en la base de datos del SRI)
                    if int(self.numero_identidad[0:2]) <= 30 and len(self.numero_identidad) >= 9:

                        # Busca en la base de datos local coincidencia de numero_identidad y tipo_identidad
                        query_sql = "SELECT * FROM res_partner " + "WHERE numero_identidad ILIKE '" + self.numero_identidad + "' and tipo_identidad = '" + self.tipo_identidad + "'"
                        self.env.cr.execute(query_sql)

                        # Si encuentra coincidencia borra los campos y advierte que el numero_identidad
                        # ya existe en la base de datos local. Deja sin borrar el numero_identidad = ref = barcode
                        if self.env.cr.rowcount == 1:
                            message_1 = {}
                            message_2 = {}
                            if self.tipo_identidad == 'ruc':
                                if len(self.numero_identidad) <= 12:
                                    message_1 = 'El Nº de Identificación '
                                    message_2 = self.numero_identidad + ' está contenido en un CONTACTO con RUC en la base de datos local.'
                                if len(self.numero_identidad) == 13:
                                    message_1 = 'El RUC Nº '
                                    message_2 = self.numero_identidad + ' ya EXISTE como CONTACTO en la base de datos local.'

                            if self.tipo_identidad == 'cedula':
                                message_1 = 'La CEDULA Nº '
                                message_2 = self.numero_identidad + ' ya EXISTE como CONTACTO en la base de datos local.'

                            message_3 = 'Ingrese otro No de Identificación, o salga del formulario de creación de contactos'
                            message = message_1 + message_2 + "\n" + "\n" + message_3

                            self.company_type = 'company'
                            self.tipo_identidad = 'pasaporte'
                            self.property_payment_term_id = 1
                            self.property_supplier_payment_term_id = 1
                            self.ref = self.numero_identidad
                            self.barcode = self.numero_identidad

                            return {'warning': {'title': "ADVERTENCIA", 'message': message}}

                        # Si no encuentra en la base de datos local busca en la base de datos del sri_ruc_db
                        # busca coincidencia únicamente del (numero_ruc ILIKE numero_identidad%)
                        elif self.tipo_identidad == 'ruc':
                            if self.company_id.ip_ruc:
                                # ----------------------------------------------------
                                # CONEXION DE SERVICIOS WEB XMLRPC
                                # SE CONECETA CON LA BASE DE DATOS sri CREADA EN ODDO
                                # Y UBICADA EN UN SERVIDOR EXTERNO
                                # ----------------------------------------------------
                                HOST = self.company_id.ip_ruc
                                DB = 'sri'
                                USER = self.env['res.users'].search([('id', '=', 2)]).login
                                PASS = self.env['res.partner'].search([('id', '=', 1)]).vat
                                ROOT = 'http://%s/xmlrpc/' % (HOST)
                                try:
                                    uid = xmlrpclib.ServerProxy(ROOT + 'common').login(DB, USER, PASS)
                                    print("Logged in as %s (uid:%d)" % (USER, uid))

                                    # 2. Read the Contribuyente info
                                    call = functools.partial(xmlrpclib.ServerProxy(ROOT + 'object').execute, DB, uid,
                                                             PASS)
                                    contribuyente = call('sri.ruc', 'search_read',
                                                         [('name', 'like', self.numero_identidad)],
                                                         ['name',
                                                          'razon_social',
                                                          'nombre_comercial',
                                                          'street', 'street2',
                                                          'city', 'provincia',
                                                          'posicion_fiscal',
                                                          'codigo_ciiu',
                                                          'actividad_economica'
                                                          ]
                                                         )
                                except Exception as error_message:
                                    if "operator does not exist" in str(error_message):
                                        error_message = 'El usuario (' + USER + ') o su clave de usuario, no están registrados en la base de datos de verificación del RUC. Contacte con su partner de Odoo'
                                    raise UserError(str(error_message))

                                # Si no encuentra coincidencia borra todos los campos y advierte que el numero_identidad
                                # no se encuentra como RUC activo en el SRI. Deja sin borrar el numero_identidad = ref = barcode
                                if not contribuyente:
                                    message_1 = 'El No de Identificación ' + self.numero_identidad + ' no se encuentra ' \
                                                                                                     'ACTIVO en el SRI.'
                                    message_2 = 'Ingrese otro No de Identificación, ' \
                                                'o salga del formulario de creación de contactos.'
                                    message = message_1 + "\n" + "\n" + message_2

                                    self.company_type = 'company'
                                    self.tipo_identidad = 'pasaporte'
                                    self.property_payment_term_id = 1
                                    self.property_supplier_payment_term_id = 1
                                    self.ref = self.numero_identidad
                                    self.barcode = self.numero_identidad

                                    return {'warning': {'title': "ADVERTENCIA", 'message': message}}

                                # Si encuentra coincidencia asigna los campos de Odoo con los del SRI
                                else:
                                    contribuyente = contribuyente[0]
                                    PROVINCIAS = self.env['res.country.state'].search([('country_id', '=', 63)])
                                    # for row in cur: # Para todas las lecturas row[] en cur

                                    # ----- Inicia Actualización de campos -----
                                    self.numero_identidad = contribuyente['name']
                                    # noinspection PyAttributeOutsideInit
                                    self.name = contribuyente['razon_social'].replace('"', '')
                                    self.nombre_comercial = contribuyente['nombre_comercial'].replace('"', '')
                                    # noinspection PyAttributeOutsideInit
                                    self.street = contribuyente['street'].replace('"', '')
                                    # noinspection PyAttributeOutsideInit
                                    self.street2 = contribuyente['street2'].replace('"', '')
                                    # noinspection PyAttributeOutsideInit
                                    self.city = contribuyente['city'].replace('"', '')

                                    for provincia in PROVINCIAS:
                                        if contribuyente['provincia'] == provincia.name:
                                            # noinspection PyAttributeOutsideInit
                                            self.state_id = provincia.id

                                    if contribuyente['posicion_fiscal'] == 'Contribuyente Especial':
                                        fiscal_position = FISCAL.browse([1])
                                    if contribuyente['posicion_fiscal'] == 'Contribuyente RISE':
                                        fiscal_position = FISCAL.browse([3])
                                    if contribuyente['posicion_fiscal'] == 'Entidad Pública':
                                        fiscal_position = FISCAL.browse([4])
                                    if contribuyente['posicion_fiscal'] == 'Persona Natural No Obligada':
                                        fiscal_position = FISCAL.browse([5])
                                    if contribuyente['posicion_fiscal'] == 'Persona Natural Obligada':
                                        fiscal_position = FISCAL.browse([6])
                                    if contribuyente['posicion_fiscal'] == 'Sociedad':
                                        fiscal_position = FISCAL.browse([7])
                                    if fiscal_position:
                                        # noinspection PyAttributeOutsideInit
                                        self.property_account_position_id = fiscal_position

                                    # noinspection PyAttributeOutsideInit
                                    self.company_type = 'company'

                                    # -------------------------------------------------------------------------------
                                    # RECUPERA DEL DISCO EL ARCHIVO PNG CON LA IMAGEN PREDEFINIDA DE LA SECCION CIIU
                                    # -------------------------------------------------------------------------------
                                    seccion_ciiu = contribuyente['codigo_ciiu'][0]
                                    nombre_archivo_png = get_module_resource('l10n_ec_partner', 'static/src/img', 'ciiu_seccion_' + seccion_ciiu + '.png')
                                    # noinspection PyAttributeOutsideInit
                                    self.image = self._get_default_image_value(nombre_archivo_png)

                                    # Lee toda la TABLA res_partner_industry y busca coincidencia en el código ciiu
                                    # y escoge la actividad industrial específica del partner
                                    query_sql = "SELECT id, name,full_name FROM res_partner_industry"
                                    self.env.cr.execute(query_sql)
                                    for res in self.env.cr.fetchall():
                                        if res[2][0] == contribuyente['codigo_ciiu'][0]:  # compara los primeros dígitos de full_name & codigo_ciiu
                                            # noinspection PyAttributeOutsideInit
                                            self.industry_id = res
                                            break
                                    # noinspection PyAttributeOutsideInit
                                    self.comment = contribuyente['codigo_ciiu'] + ' - ' + contribuyente[
                                        'actividad_economica']
                                    self.tipo_identidad = 'ruc'
                                    # noinspection PyAttributeOutsideInit
                                    self.country_id = 63  # country_id (Ecuador (EC) = 63)
                    else:
                        message_1 = 'El No de Identificación ' + self.numero_identidad + ' está fuera de rango.'
                        message_2 = 'Ingrese otro No de Identificación, ' \
                                    'o salga del formulario de creación de contactos.'
                        message = message_1 + "\n\n" + message_2
                        return {'warning': {'title': "ADVERTENCIA", 'message': message}}
            # Al terminar la busqueda en la base local o en el SRI, define siempre los siguientes campos:
            # noinspection PyAttributeOutsideInit
            self.property_payment_term_id = 1
            # noinspection PyAttributeOutsideInit
            self.property_supplier_payment_term_id = 1
            # noinspection PyAttributeOutsideInit
            self.ref = self.numero_identidad
            # noinspection PyAttributeOutsideInit
            self.barcode = self.numero_identidad
            self.update_date = pst_now_str

        except Exception as e:
            raise UserError(e)

    # --------------------------------------------------------------
    # API:      ACTUALIZAR_TODOS
    # function: actualizar_ruc(self)
    # ------------------------------
    @api.one
    def actualizar_todos(self):

        finish_at = time.time() + 119

        utc_now = datetime.today()
        pst_now = utc_now.astimezone(pytz.timezone("America/Guayaquil"))
        pst_now_str = pst_now.strftime("%Y-%m-%d")
        # pst_now_obj = datetime.strptime(pst_now_str, '%Y-%m-%d').date()

        ahora = pst_now.date()
        hace_30_dias = ahora - timedelta(days=30)

        CONTACTOS = self.env['res.partner'].search([])
        total_contactos = len(CONTACTOS)
        total_avance = 0
        for contacto in CONTACTOS:
            if not contacto.update_date:
                fecha_contacto = datetime.strptime('2000-01-01', '%Y-%m-%d').date()
            else:
                fecha_contacto = datetime.strptime(str(contacto.update_date), '%Y-%m-%d').date()
            if fecha_contacto <= hace_30_dias:
                temporizador = time.time()
                logging.info('ACTUALIZANDO ID: ' + str(contacto.id) + ' / ' + str(contacto.name) + ' / ' + str('{:.1f}'.format(finish_at - temporizador)))

                if contacto.tipo_identidad == 'pasaporte':
                    # -------------------------------------------------------------------------------
                    # RECUPERA DEL DISCO EL ARCHIVO PNG CON LA IMAGEN PREDEFINIDA DE LA SECCION CIIU
                    # -------------------------------------------------------------------------------
                    contacto.company_type = 'company'

                    if not contacto.image:
                        nombre_archivo_png = get_module_resource('l10n_ec_partner', 'static/src/img',
                                                                 'ciiu_seccion_PAS.png')

                        # noinspection PyAttributeOutsideInit
                        contacto.image = contacto._get_default_image_value(nombre_archivo_png)


                if contacto.tipo_identidad == 'cedula':
                    contacto.numero_identidad = contacto.numero_identidad[0:10]
                    contacto.company_type = 'person'

                    # -------------------------------------------------------------------------------
                    # RECUPERA DEL DISCO EL ARCHIVO PNG CON LA IMAGEN PREDEFINIDA DE LA SECCION CIIU
                    # -------------------------------------------------------------------------------
                    if not contacto.image:
                        nombre_archivo_png = get_module_resource('l10n_ec_partner', 'static/src/img', 'ciiu_seccion_PN.png')

                        # noinspection PyAttributeOutsideInit
                        contacto.image = contacto._get_default_image_value(nombre_archivo_png)

                if contacto.tipo_identidad == 'ruc':
                    # -------------------------------------------------------------------------------
                    # RECUPERA DEL DISCO EL ARCHIVO PNG CON LA IMAGEN PREDEFINIDA DE LA SECCION CIIU
                    # -------------------------------------------------------------------------------
                    valor_bool = contacto.actualizar(True)[0]
                    if not contacto.image:
                        if valor_bool:
                            seccion_ciiu = contacto.comment[0]
                            nombre_archivo_png = get_module_resource('l10n_ec_partner', 'static/src/img','ciiu_seccion_' + seccion_ciiu + '.png')
                        else:
                            nombre_archivo_png = get_module_resource('l10n_ec_partner', 'static/src/img', 'ciiu_seccion_PAS.png')

                        # noinspection PyAttributeOutsideInit
                        contacto.image = contacto._get_default_image_value(nombre_archivo_png)

                total_avance = total_avance + 1
                contacto.update_date = pst_now_str

                if time.time() > finish_at:
                    return

        return

    # --------------------------------------------------------------
    # API:      ACTUALIZAR_RUC
    # function: actualizar_ruc(self)
    # ------------------------------
    @api.one
    def actualizar(self, boton = False):

        retorno = False

        if self.tipo_identidad == 'pasaporte':
            # -------------------------------------------------------------------------------
            # RECUPERA DEL DISCO EL ARCHIVO PNG CON LA IMAGEN PREDEFINIDA DE LA SECCION CIIU
            # -------------------------------------------------------------------------------
            if not self.image:
                nombre_archivo_png = get_module_resource('l10n_ec_partner', 'static/src/img', 'ciiu_seccion_PAS.png')
                # noinspection PyAttributeOutsideInit
                self.image = self._get_default_image_value(nombre_archivo_png)
                self.company_type = 'company'
            retorno = True

        if self.tipo_identidad == 'cedula':
            self.numero_identidad = self.numero_identidad[0:10]
            self.company_type = 'person'

            # -------------------------------------------------------------------------------
            # RECUPERA DEL DISCO EL ARCHIVO PNG CON LA IMAGEN PREDEFINIDA DE LA SECCION CIIU
            # -------------------------------------------------------------------------------
            if not self.image:
                nombre_archivo_png = get_module_resource('l10n_ec_partner', 'static/src/img', 'ciiu_seccion_PN.png')
                # noinspection PyAttributeOutsideInit
                self.image = self._get_default_image_value(nombre_archivo_png)
            retorno = True

        if self.tipo_identidad == 'ruc':
            if self.company_id.ip_ruc:
                fiscal_position = {}
                FISCAL = self.env['account.fiscal.position']
                # ----------------------------------------------------
                # CONEXION DE SERVICIOS WEB XMLRPC
                # SE CONECETA CON LA BASE DE DATOS sri CREADA EN ODDO
                # Y UBICADA EN UN SERVIDOR EXTERNO
                # ----------------------------------------------------
                HOST = self.company_id.ip_ruc
                DB = 'sri'
                USER = self.env['res.users'].search([('id', '=', 2)]).login
                PASS = self.env['res.partner'].search([('id', '=', 1)]).vat
                ROOT = 'http://%s/xmlrpc/' % (HOST)
                try:
                    uid = xmlrpclib.ServerProxy(ROOT + 'common').login(DB, USER, PASS)
                    logging.info("Logged in as %s (uid:%d)" % (USER, uid))

                    # 2. Read the Contribuyente info
                    call = functools.partial(xmlrpclib.ServerProxy(ROOT + 'object').execute, DB, uid,
                                             PASS)
                    contribuyente = call('sri.ruc', 'search_read',
                                         [('name', 'like', self.numero_identidad)],
                                         ['name',
                                          'razon_social',
                                          'nombre_comercial',
                                          'street', 'street2',
                                          'city', 'provincia',
                                          'posicion_fiscal',
                                          'codigo_ciiu',
                                          'actividad_economica'
                                          ]
                                         )
                except Exception as error_message:
                    if "operator does not exist" in str(error_message):
                        error_message = 'El usuario (' + USER + ') o su clave de usuario, no están registrados en la base de datos de verificación del RUC. Contacte con su partner de Odoo'
                    raise UserError(str(error_message))

                # Si no encuentra coincidencia borra todos los campos y advierte que el numero_identidad
                # no se encuentra como RUC activo en el SRI. Deja sin borrar el numero_identidad = ref = barcode
                if not contribuyente:
                    message_1 = 'El No de Identificación ' + self.numero_identidad + ' no se encuentra ' \
                                                                                     'ACTIVO en el SRI.'
                    message_2 = 'Ingrese otro No de Identificación, ' \
                                'o salga del formulario de creación de contactos.'
                    message = message_1 + "\n" + "\n" + message_2

                    self.company_type = 'company'
                    self.tipo_identidad = 'pasaporte'
                    self.property_payment_term_id = 1
                    self.property_supplier_payment_term_id = 1
                    self.ref = self.numero_identidad
                    self.barcode = self.numero_identidad

                    if boton:
                        retorno = False
                    else:
                        return {'warning': {'title': "ADVERTENCIA", 'message': message}}

                # Si encuentra coincidencia asigna los campos de Odoo con los del SRI
                else:
                    logging.info("Actualizando RUC " + contribuyente[0]['name'] + " (" + contribuyente[0]['razon_social'] + ")")
                    contribuyente = contribuyente[0]
                    PROVINCIAS = self.env['res.country.state'].search([('country_id', '=', 63)])
                    # for row in cur: # Para todas las lecturas row[] en cur

                    # ----- Inicia Actualización de campos -----
                    self.numero_identidad = contribuyente['name']
                    # noinspection PyAttributeOutsideInit
                    self.name = contribuyente['razon_social'].replace('"','')
                    self.nombre_comercial = contribuyente['nombre_comercial'].replace('"','')
                    # noinspection PyAttributeOutsideInit
                    self.street = contribuyente['street'].replace('"','')
                    # noinspection PyAttributeOutsideInit
                    self.street2 = contribuyente['street2'].replace('"','')
                    # noinspection PyAttributeOutsideInit
                    self.city = contribuyente['city'].replace('"','')

                    for provincia in PROVINCIAS:
                        if contribuyente['provincia'] == provincia.name:
                            # noinspection PyAttributeOutsideInit
                            self.state_id = provincia.id

                    if contribuyente['posicion_fiscal'] == 'Contribuyente Especial':
                        fiscal_position = FISCAL.browse([1])
                    if contribuyente['posicion_fiscal'] == 'Contribuyente RISE':
                        fiscal_position = FISCAL.browse([3])
                    if contribuyente['posicion_fiscal'] == 'Entidad Pública':
                        fiscal_position = FISCAL.browse([4])
                    if contribuyente['posicion_fiscal'] == 'Persona Natural No Obligada':
                        fiscal_position = FISCAL.browse([5])
                    if contribuyente['posicion_fiscal'] == 'Persona Natural Obligada':
                        fiscal_position = FISCAL.browse([6])

                    if contribuyente['posicion_fiscal'] == 'Sociedad':
                        fiscal_position = FISCAL.browse([7])

                    if fiscal_position:
                        # noinspection PyAttributeOutsideInit
                        self.property_account_position_id = fiscal_position

                    self.company_type = 'company'

                    # Lee toda la TABLA res_partner_industry y busca coincidencia en el código ciiu
                    # y escoge la actividad industrial específica del partner
                    query_sql = "SELECT id, name,full_name FROM res_partner_industry"
                    self.env.cr.execute(query_sql)
                    for res in self.env.cr.fetchall():
                        # compara los primeros dígitos de full_name & codigo_ciiu
                        if res[2][0] == contribuyente['codigo_ciiu'][0]:
                            # noinspection PyAttributeOutsideInit
                            self.industry_id = res
                            break
                    # noinspection PyAttributeOutsideInit
                    self.comment = contribuyente['codigo_ciiu'] + ' - ' + contribuyente['actividad_economica']

                    # -------------------------------------------------------------------------------
                    # RECUPERA DEL DISCO EL ARCHIVO PNG CON LA IMAGEN PREDEFINIDA DE LA SECCION CIIU
                    # -------------------------------------------------------------------------------
                    if not self.image:
                        seccion_ciiu = contribuyente['codigo_ciiu'][0]
                        nombre_archivo_png = get_module_resource('l10n_ec_partner', 'static/src/img','ciiu_seccion_' + seccion_ciiu + '.png')
                        # noinspection PyAttributeOutsideInit
                        self.image = self._get_default_image_value(nombre_archivo_png)

                        self.tipo_identidad = 'ruc'
                        # noinspection PyAttributeOutsideInit
                        self.country_id = 63  # country_id (Ecuador (EC) = 63)

                    retorno = True

        # Al terminar la busqueda en la base local o en el SRI, define siempre los siguientes campos:
        # noinspection PyAttributeOutsideInit
        self.property_payment_term_id = 1
        # noinspection PyAttributeOutsideInit
        self.property_supplier_payment_term_id = 1
        # noinspection PyAttributeOutsideInit
        self.ref = self.numero_identidad
        # noinspection PyAttributeOutsideInit
        self.barcode = self.numero_identidad

        return retorno

    # --------------------------------------------------------------
    # API:      change_tipo_identidad
    # function: change_tipo_identidad(self)
    # Notes:    Postgresql -> 
    #                         
    # ------------------------------
    @api.onchange('tipo_identidad')
    def change_tipo_identidad(self):
        self.ensure_one()
        FISCAL = self.env['account.fiscal.position']
        fiscal_position = {}

        try:
            if self.tipo_identidad == 'cedula' and self.numero_identidad:
                self.numero_identidad = self.numero_identidad[0:10]
                fiscal_position = FISCAL.browse([5])
                self.company_type = 'person'
                # noinspection PyAttributeOutsideInit
                self.country_id = 63

            if self.tipo_identidad == 'pasaporte' and self.numero_identidad:
                fiscal_position = FISCAL.browse([9])
                self.company_type = 'company'

            if self.tipo_identidad == 'ruc' and self.numero_identidad:
                if len(self.numero_identidad) == 10:
                    self.numero_identidad = self.numero_identidad + '001'
                # noinspection PyAttributeOutsideInit
                self.company_type = 'company'

            # Al terminar, define siempre los siguientes campos:
            # noinspection PyAttributeOutsideInit
            self.property_payment_term_id = 1
            # noinspection PyAttributeOutsideInit
            self.property_supplier_payment_term_id = 1
            # noinspection PyAttributeOutsideInit
            self.ref = self.numero_identidad
            # noinspection PyAttributeOutsideInit
            self.barcode = self.numero_identidad

            if fiscal_position:
                # noinspection PyAttributeOutsideInit
                self.property_account_position_id = fiscal_position

        except Exception as e:
            raise UserError(str(e))

    @api.model
    def _get_default_image_value(self, img_path):
        try:
            image = False
            if img_path:
                with open(img_path, 'rb') as f:  # read the image from the path
                    image = f.read()

            return tools.image_resize_image_big(base64.b64encode(image))

        except Exception as error_mesage:

            valor_bool = self.actualizar(True)[0]
            if valor_bool:
                seccion_ciiu = self.comment[0]
                img_path = get_module_resource('l10n_ec_partner', 'static/src/img', 'ciiu_seccion_' + seccion_ciiu + '.png')
                image = False
            else:
                img_path = get_module_resource('l10n_ec_partner', 'static/src/img', 'ciiu_seccion_PAS.png')
                image = False
            if img_path:
                with open(img_path, 'rb') as f:  # read the image from the path
                    image = f.read()
            return tools.image_resize_image_big(base64.b64encode(image))

# --------------------------------------------------------------
# CLASS:    ResCompany
# OBJECT:   res.company    ->  inherit
# Notes:    Modificactions & Calculation on company fields
# ------------------------------
class ResCompany(models.Model):
    _inherit = 'res.company'

    # ----- field definition -----
    company_contador_id = fields.Many2one(
        'res.partner',
        string='Contacto Contador',
        help='Información del contador de la empresa'
    )
    # ----- field definition -----
    company_sri_id = fields.Many2one(
        'res.partner',
        string='Contacto SRI',
        help='Información del Servicio de Rentas Internas ecuatoriano'
    )
    # ----- field definition -----
    company_representante_legal = fields.Many2one(
        'res.partner',
        string='Contacto Rep. Legal',
        help='Información del representante legal de la empresa'
    )
    # ----- field definition -----
    company_contribuyente_especial = fields.Selection(
        [
            ('SI', 'SI'),
            ('NO', 'NO')
        ],
        string='Contribuyente Especial',
        required=True,
        help='Información de la empresa: ¿Es o no es contribuyente especial?',
        default='NO'
    )
    # ----- field definition -----
    company_obligado_contabilidad = fields.Selection(
        [
            ('SI', 'SI'),
            ('NO', 'NO')
        ],
        string='Obligado Contabilidad',
        required=True,
        help='Información de la empresa: ¿Es o no obligado a llevar contabilidad?',
        default='NO'
    )
    ip_ruc = fields.Char(
        string='IP Servidor RUC',
        help='IP de acceso al servidor con la base de datos del SRI de RUCs activos',
    )
