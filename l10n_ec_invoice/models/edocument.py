# -*- coding: utf-8 -*-

# ---------------------------
# Notes:    LIBRERIAS PYTHON
# ---------------------------

from odoo import api, fields, models
from odoo.exceptions import (ValidationError, Warning as UserError)

from ..xades.sri import DocumentXML
from ..xades.xades import Xades

from io import StringIO
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from xml.etree import cElementTree as ET

import xmlrpc.client as xmlrpclib
import base64
import logging
import pytz
import itertools
import os
import re


# ----------------------------------------------------------------------------------------------------------------------
# OOOOO O     OOOOO OOOOO OOOOO OOOOO OOOOO O   O OOO OOOOO   OOOO  OOOOO OOOOO O   O O   O OOOOO O   O OOOOO OOOOO
# O     O     O     O       O   O   O O   O OO  O  O  O       O   O O   O O     O   O OO OO O     OO  O   O   O
# OOO   O     OOO   O       O   OOOOO O   O O O O  O  O       O   O O   O O     O   O O O O OOO   O O O   O   OOOOO
# O     O     O     O       O   O  O  O   O O  OO  O  O       O   O O   O O     O   O O   O O     O  OO   O       O
# OOOOO OOOOO OOOOO OOOOO   O   O   O OOOOO O   O OOO OOOOO   OOOO  OOOOO OOOOO OOOOO O   O OOOOO O   O   O   OOOOO
# ----------------------------------------------------------------------------------------------------------------------
# ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
#   O   OOOOO OOOOO OOOOO O   O O   O OOOOO     OOO  O   O O   O OOOOO  OOO  OOOOO OOOOO
#  O O  O     O     O   O O   O OO  O   O        O   OO  O O   O O   O   O   O     O
# O   O O     O     O   O O   O O O O   O        O   O O O O   O O   O   O   O     OOO
# OOOOO O     O     O   O O   O O  OO   O        O   O  OO  O O  O   O   O   O     O
# O   O OOOOO OOOOO OOOOO OOOOO O   O   O       OOO  O   O   O   OOOOO  OOO  OOOOO OOOOO
# ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # ---------------------
    # DEFINICION DE CAMPOS
    # ---------------------
    estado = fields.Selection(
        [
            ('01', 'DOCUMENTO PENDIENTE'),
            ('02', 'SRI EN PROCESO'),
            ('03', 'SRI AUTORIZADO'),
            ('00', 'ERROR')
        ],
        string='Estado SRI',
        readonly=True,
        required=True,
        default='01',
        copy=False,
        help='Estado de los comprobantes electrónicos'
    )
    # ---------------------
    # DEFINICION DE CAMPOS
    # ---------------------
    estado_lc = fields.Selection(
        [
            ('01', 'DOCUMENTO PENDIENTE'),
            ('02', 'SRI EN PROCESO'),
            ('03', 'SRI AUTORIZADO'),
            ('00', 'ERROR')
        ],
        string='LC Estado SRI',
        readonly=True,
        default='01',
        required = True,
        copy=False,
        help='Estado de los comprobantes electrónicos'
    )
    bool_on_off_estado = fields.Boolean(
        string='Cambio de estado',
        default=False,
        copy=False,
        help='MARQUE PARA MODIFICAR EL ESTADO DEL DOCUMENTO'
    )
    bool_on_off_estado_lc = fields.Boolean(
        string='LC Cambio de estado',
        default=False,
        copy=False,
        help='MARQUE PARA MODIFICAR EL ESTADO DEL DOCUMENTO'
    )
    historial = fields.Text(
        string='Historial SRI',
        copy=False
    )

    adjuntos = {}

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def documento_electronico(self):

        inv_xml = {}
        fechaAutorizacion = {}

        # ------------------------------------------------------
        # UNLINK ELIMINA todos los archivos si existiere alguno
        # ------------------------------------------------------
        ADJUNTOS_IDS = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion)])
        for adjuntos_ids in ADJUNTOS_IDS:
            adjuntos_ids.unlink()
        adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion)])

        # --------------------------------------------------------------------------------------------------------------
        # INICIA EL PROCESO DE VALIDACION DE COMPROBANTES ELECTRONICOS EN EL SRI
        # -----------------------------------------------------------------------
        try:
            log_msg = '–––––––––––––––––––– COMPROBANTE ELECTRONICO –––––––––––––––––––––'
            logging.info(log_msg)
            self.history_log(log_msg)

            log_msg = 'TIPO: %s' % self.doc_electronico_tipo + ' No: ' + self.doc_electronico_no
            logging.info(log_msg)
            self.history_log(log_msg)

            log_msg = 'CLAVE DE ACCESO: ' + self.doc_electronico_no_autorizacion
            logging.info(log_msg)
            self.history_log(log_msg)

            if self.estado == '01' or self.estado == '02' or self.estado == '03':  # PENDIENTE, AUTORIZADO o EN PROCESO
                # ------------------------------------------------------------------------------------------------------
                # ODOO: LECTURA DEL ARCHIVO XML archivo_basico Y CORRECCION DE CARCATERES
                # ESPECIALES DE ESTE ARCHIVO EN archivo_basico_fix_xml
                # ------------------------------------------------------------------
                try:
                    ruta_archivo_xml = self.company_id.company_ruta_documentos
                    nombre_archivo_xml = ruta_archivo_xml + self.doc_electronico_xml
                    # ----------------------------------------------------------------------
                    # RECUPERA DEL DISCO EL ARCHIVO XML EN FORMATO TEXTO archivo_basico_xml
                    # ----------------------------------------------------------------------
                    archivo_basico = open(nombre_archivo_xml, "r", encoding='utf8')
                    archivo_basico_xml = archivo_basico.read()
                    log_msg = 'LECTURA DE INFORMACION - (Ok)'
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    # ----------------------------------------------------------------------
                    # CAMBIA LOS CARACTERES ESPECIALES Y CREA archivo_basico_fix_xml
                    # ----------------------------------------------------------------------
                    archivo_basico_fix_xml = self.replace_fix_chars(archivo_basico_xml)

                except Exception as error_message:
                    # ------------------------------------------------------------------
                    # ERROR DE LECTURA Y DE CAMBIO DE CARACTERES DEL archivo_basico_xml
                    # ------------------------------------------------------------------
                    log_msg = 'ERROR: Lectura/Modificiación archivo_basico_xml - ' + str(error_message).replace("'", "").upper()
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    self.estado = "00"  # ERROR
                    return

                # ------------------------------------------------------------------------------------------------------
                # SRI: CARGA EL ESQUEMA PARA EL TIPO DE DOCUMENTO ELECTRONICO Y
                # VALIDA EL ARCHIVO archivo_basico_fix_xml EN EL FORMATO XML
                # --------------------------------------------------------------
                try:
                    # -------------------------------------------------
                    # DEFINE inv_xml EN FUNCION DEL ESQUEMA ESPECIFICO
                    # -------------------------------------------------
                    if self.tipo_documento_tributario == 'DOCUMENTO DE COMPRA':
                        inv_xml = DocumentXML(archivo_basico_fix_xml, 'withdrawing')
                    if self.tipo_documento_tributario == 'FACTURA DE VENTA':
                        inv_xml = DocumentXML(archivo_basico_fix_xml, 'out_invoice')
                    if self.tipo_documento_tributario == 'NOTA DE CREDITO DE VENTA':
                        inv_xml = DocumentXML(archivo_basico_fix_xml, 'out_refund')
                    if self.tipo_documento_tributario == 'GUIA DE REMISION':
                        inv_xml = DocumentXML(archivo_basico_fix_xml, 'delivery')
                    # -----------------------------------------------------------
                    # VALIDA EL ARCHIVO archivo_basico_fix_xml EN EL FORMATO XML
                    # -----------------------------------------------------------
                    validador, mensaje_autorizacion = inv_xml.validate_xml()
                    if not validador:
                        log_msg = 'ERROR: VALIDADOR de archivo XML - ' + str(mensaje_autorizacion).replace("'", "")
                        logging.info(log_msg)
                        self.history_log(log_msg)
                        self.estado = "00"  # ERROR
                        return
                    log_msg = 'VALIDADOR DE ARCHIVO XML PREVIO AL ENVIO - (Ok)'
                    logging.info(log_msg)
                    self.history_log(log_msg)
                except Exception as error_message:
                    # -------------------------------------------------------------------
                    # ERROR DE LECTURA DE ESQUEMA Y VALIDACION ETREE DEL ARCHIVO XML FIX
                    # -------------------------------------------------------------------
                    log_msg = 'ERROR: Proceso validación XML - ' + str(error_message).replace("'", "")
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    self.estado = "00"  # ERROR
                    return

                # ------------------------------------------------------------------------------------------------------
                # XADES: AÑADE LA FIRMA ELECTRONICA AL ARCHIVO XML
                # ------------------------------------------
                try:
                    # -------------------------------------------------
                    # XMLRPC: GENERA LOS ARGUMENTOS DE LA API
                    # -------------------------------------------------
                    password = self.company_id.password_electronic_signature

                    # -------------------------------------------------
                    # XADES LOCAL: FIRMA ELECTRONICA DEL DOCUMENTO
                    # -------------------------------------------------
                    # xades = Xades()
                    # archivo_pk12 = self.company_id.electronic_signature
                    # password = self.company_id.password_electronic_signature
                    # archivo_firmado_xml = xades.sign(archivo_basico_fix_xml, archivo_pk12, password)
                    # archivo_firmado_xml = archivo_firmado_xml.decode('ascii')


                    # ----------------------------------------------------
                    # CONEXION DE SERVICIOS WEB XMLRPC
                    # SE CONECETA CON LA BASE DE DATOS sri CREADA EN ODDO
                    # Y UBICADA EN UN SERVIDOR EXTERNO
                    # ----------------------------------------------------
                    host_port = self.company_id.ip_ruc
                    db = 'sri'
                    user = self.env['res.users'].search([('id', '=', 2)]).login
                    pwd = self.env['res.partner'].search([('id', '=', 1)]).vat
                    srv = 'http://%s' % (host_port)
                    # -------------------------------------------------
                    # XMLRPC: VERIFICA CONECCION Y AUTENTIFICA
                    # -------------------------------------------------
                    common = xmlrpclib.ServerProxy('%s/xmlrpc/common' % srv)    # VERIFICACION
                    server_version = common.version()['server_version']
                    uid = common.authenticate(db, user, pwd, {})                # AUTENTIFICACION
                    if not uid:
                        # -------------------------------------------------
                        # ERROR EN XADES: USURIO NO REGISTRADO EN BASE sri
                        # -------------------------------------------------
                        log_msg = 'ERROR: Usuario o clave de usuario no registrados a la FIRMA ELECTRONICA. Consulte con su asesor de Odoo'
                        logging.info(log_msg)
                        self.history_log(log_msg)
                        self.estado = "00"  # ERROR
                        return
                    log_msg = 'CONECTANDO CON SERVIDOR: ' + srv + ' ODOO Version: ' + server_version + ' USUARIO REGISTRADO id: ' + str(uid)
                    logging.info(log_msg)
                    # --------------------------------------------------------
                    # XADES REMOTO: FIRMA ELECTRONICA
                    # XMLRPC: ACTIVA LA Application Programming Interface API
                    # --------------------------------------------------------
                    api = xmlrpclib.ServerProxy('%s/xmlrpc/object' % srv)

                    archivo_firmado_xml = api.execute_kw(db, uid, pwd, 'sri.ruc', 'firma_electronica', [[]],
                        {
                            'archivo_basico_fix_xml': archivo_basico_fix_xml,
                            'password': password,
                            'user_id': uid
                        }
                    )
                    # -------------------------------------------------
                    # ERROR EN XADES: FIRMA ELECTRONICA DEL DOCUMENTO
                    # -------------------------------------------------
                    if "No se puede generar KeyStore" in archivo_firmado_xml:
                        message = archivo_firmado_xml.split("\n")[0] + " / " + archivo_firmado_xml.split("\n")[1]
                        log_msg = 'ERROR: En firma electrónica Xades() - ' + str(message).replace("'", "").upper()
                        logging.info(log_msg)
                        self.history_log(log_msg)
                        self.estado = "00"  # ERROR
                        return

                    log_msg = 'FIRMA ELECTRONICA DEL DOCUMENTO - (Ok)'
                    logging.info(log_msg)
                    self.history_log(log_msg)
                except Exception as error_message:
                    # -------------------------------------------------
                    # ERROR EN XADES: FIRMA ELECTRONICA DEL DOCUMENTO
                    # -------------------------------------------------
                    log_msg = 'ERROR: En firma electrónica Xades() - ' + str(error_message).replace("'", "").upper()
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    self.estado = "00"  # ERROR
                    return
                # ------------------------------------------------------------------------------------------------------
                # SRI: VALIDAR COMPROBANTE - CONEXION, ENVIO DEL XML
                # -----------------------------
                try:
                    # ----------------------------------------------------------------------------
                    # DETERMINA EL TIPO DE CONECCION CON EL SRI (PRUEBAS/PRODUCCION/ON O OFFLINE)
                    # ----------------------------------------------------------------------------
                    url_recepcion, url_autorizacion = self.company_id._get_ws()
                    # --------------------------
                    # ENVIA EL DOCUMENTO AL SRI
                    # --------------------------
                    validador_recepcion, errores, codigo_error, respuesta_sri = inv_xml.send_receipt(
                        archivo_firmado_xml, url_recepcion)

                    if not validador_recepcion:
                        # --------------------------------------------------------------------------------------------------------
                        # SI validador_recepcion == False --> EL SRI EMITIÓ UN ERROR EN LA VALIDACION DEL COMPROBANTE ELECTRONICO
                        # --------------------------------------------------------------------------------------------------------
                        # if codigo_error != '70' and codigo_error != '43':
                        if int(codigo_error) in [2, 10, 26, 27, 28, 35, 36, 37, 39, 40, 45, 46,
                                            47, 48, 49, 50, 52, 56, 57, 58, 63, 65, 67, 80]:
                            # -----------------------------------------------------------------------------------
                            # CODIGOS DE ERRORES DE WS validarComprobante QUE DETIENEN EL PROCESO DE FACTURACION
                            # ESTOS DOCUMENTOS DEBEN REVISARSE Y ANULARSE EN EL SISTEMA. PUEDE QUE REQUIERAN
                            # REVISION EN LA CODIFICACION
                            # -----------------------------------------------------------------------------------
                            log_msg = 'ERROR: Web Service SRI ValidarComprobante: ' + str(errores).replace("'", "").upper()
                            logging.info(log_msg)
                            self.history_log(log_msg)
                            self.estado = "00"  # ERROR
                            return
                        if int(codigo_error) in [34, 42, 52, 64, 65, 69]:
                            # -----------------------------------------------------------------------------------
                            # CODIGOS DE ERRORES DE WS validarComprobante QUE DETIENEN EL PROCESO DE FACTURACION
                            # ESTOS ERRORES DEBEN SER PARTE DEL SISTEMA CONTABLE PARA EVITAR LA GENERACION Y
                            # ENVIO DE COMPROBANTES AL SRI POR PARTE DE LOS DESARROLLADORES
                            # -----------------------------------------------------------------------------------
                            log_msg = 'ERROR: ValidarComprobante - Documento no cumple requisitos de norma tributaria: ' + \
                                      str(errores).replace("'", "").upper()
                            logging.info(log_msg)
                            self.history_log(log_msg)
                            self.estado = "00"  # ERROR
                            return
                        # -----------------------------------------------------------------------------------------
                        # CODIGOS DE ERRORES DE WS validarComprobante QUE NO DETIENEN EL PROCESO DE FACTURACION
                        # GENERAN UNA ADVENTENCIA Y CONTINUAN EL PROCESO
                        # CUALQUIER ERROR NO LISTADO Y LOS ERRORES DE COMUNICACION Y RECEPCION DEL SRI NO DETIENEN
                        # EL PROCESO DE FACTURACION DE ODOO. SE EMITIRA EL RIDE Y XML SIN FECHA DE AUTORIZACION
                        # -----------------------------------------------------------------------------------------
                        # ----------------------------------------------------------------
                        # SI EL codigo_error == 70 --> CLAVE DE ACCESO EN PROCESAMIENTO O
                        # SI EL codigo_error == 43 --> CLAVE DE ACCESO REGISTRADA
                        # OTRO ERROR ES DE COMUNICACION Y NO DEBE PARAR EL PROCESO
                        # ----------------------------------------------------------------
                        if codigo_error != '70' and codigo_error != '43':
                            codigo_error = ' PROBLEMAS DE COMUNICACION CON EL WS DEL SRI:'
                        log_msg = 'SRI: ADVERTENCIA AL VALIDAR EL COMPROBANTE: ' + ' ' + str(errores).replace("'", "")
                        logging.info(log_msg)
                        self.history_log(log_msg)
                    else:
                        # ---------------------------------------------------------------
                        # SI validador_recepcion == True --> ACTUALIZA EL LOG Y CONTINUA
                        # ---------------------------------------------------------------
                        log_msg = 'ENVIO ARCHIVO XML FIRMADO AL SRI - (Ok)'
                        logging.info(log_msg)
                        self.history_log(log_msg)
                        log_msg = 'SRI: Respuesta: %s' % respuesta_sri
                        logging.info(log_msg)
                        self.history_log(log_msg)

                except Exception as error_message:
                    # -------------------------------------------------
                    # ERROR EN VALIDADOR DE RECEPCION DEL SRI
                    # -------------------------------------------------
                    log_msg = 'ADVERTENCIA: En Validador Recepción SRI - ' + str(error_message).replace("'", "")
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    self.estado = "02"  # SRI EN PROCESO
                # ------------------------------------------------------------------------------------------------------
                # SRI: AUTORIZACION
                # ------------------
                try:
                    # --------------------------------
                    # SOLICITA LA AUTORIZACION AL SRI
                    # --------------------------------
                    autorizacion, mensaje_autorizacion = inv_xml.request_authorization(self.doc_electronico_no_autorizacion, url_autorizacion)
                    log_msg = 'SOLICITUD DE AUTORIZACION AL SRI - (Ok)'
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    # --------------------------------------------------------------------------------------
                    # SI autorizacion == False --> ERROR AL RECIBIR EL CODIGO DE AUTORIZACION DEL DOCUMENTO
                    # mensaje_autorizacion CONTIENE EL MENSAJE DE ERROR
                    # SE DETIENE EL PROCESO DE VALIDACION DEL self EN ODOO
                    # --------------------------------------------------------------------------------------
                    # ERROR DENTRO DE ESTE PROCESO DETIENE LA VALIDACION DEL FORMULARIO DE ODOO
                    # --------------------------------------------------------------------------------------
                    if not autorizacion:
                        msg = ' '.join(list(itertools.chain(*mensaje_autorizacion)))
                        log_msg = 'ERROR: Autorización SRI reporta - ' + str(msg).replace("'", "").upper()
                        logging.info(log_msg)
                        self.history_log(log_msg)
                        self.estado = "00"  # ERROR
                        return
                    else:
                        # ---------------------------------------------------
                        # AÑADE LA AUTORIZACION DEL SRI AL DOCUMENTO FIRMADO
                        # ---------------------------------------------------
                        if mensaje_autorizacion == "SIN INFORMACION":
                            # ---------------------------------------------------
                            # GENERACION DE ADJUNTOS SIN FECHA DE AUTORIZACION
                            # ---------------------------------------------------
                            autorizacion_xml = archivo_firmado_xml

                            log_msg = 'SRI: CLAVE DE ACCESO SIN REGISTRO EN EL SRI. POSIBLES PROBLEMAS DE COMUNICACION.\n\tINTENTAR MAS TARDE NUEVAMENTE'
                            logging.info(log_msg)
                            self.history_log(log_msg)
                            self.estado = "02"  # SRI EN PROCESO

                            # adjuntos_ids = self.add_attachment(autorizacion_xml)[0]

                            self.add_attachment_xml(autorizacion_xml)[0]
                            self.add_attachment_pdf(autorizacion_xml)[0]

                            log_msg = 'ODOO: SE GENERARON RIDE & XML SIN FECHA DE AUTORIZACION - (Ok)'
                            logging.info(log_msg)
                            self.history_log(log_msg)

                        else:
                            # ---------------------------------------------------
                            # GENERACION DE ADJUNTOS CON FECHA DE AUTORIZACION
                            # ---------------------------------------------------
                            autorizacion_xml = self.render_authorized_document(autorizacion)
                            # ---------------------------------------------
                            # EXTRAE fechaAutorizacion DESDE autorizacion_xml
                            # ---------------------------------------------
                            root = ET.fromstring(autorizacion_xml)
                            for autorizacion in root.iter('autorizacion'):
                                fechaAutorizacion = autorizacion.find('fechaAutorizacion').text
                            # -------------------------------------------------
                            # ACTUALIZA doc_electronico_fecha_autorizacion EN
                            # EL CORRESPONDIENTE self DE account.invoice
                            # ESTO PERMITE AÑADIR ESTA FECHA EN EL RIDE
                            # -------------------------------------------------
                            self.fecha_autorizacion = fechaAutorizacion
                            vals = {
                                'doc_electronico_fecha_autorizacion': self.fecha_autorizacion
                            }
                            forma = self.env['account.invoice'].search(
                                [('doc_electronico_no_autorizacion', '=', self.doc_electronico_no_autorizacion)])
                            forma.write(vals)

                            log_msg = 'SRI: DOCUMENTO AUTORIZADO - ' + fechaAutorizacion + ' - (Ok)'
                            logging.info(log_msg)
                            self.history_log(log_msg)
                            self.estado = "03"  # SRI AUTORIZADO

                            # adjuntos_ids = self.add_attachment(autorizacion_xml)[0]

                            self.add_attachment_xml(autorizacion_xml)[0]
                            self.add_attachment_pdf(autorizacion_xml)[0]

                            log_msg = 'ODOO: SE GENERARON RIDE & XML CON FECHA DE AUTORIZACION - (Ok)'
                            logging.info(log_msg)
                            self.history_log(log_msg)

                except Exception as error_message:
                    # ------------------------------------------------------------------------------
                    # WARNING EN PROCESO DE AUTORIZACION Y GENERACION DE ARCHIVOS ADJUNTOS RIDE Y XML
                    # ------------------------------------------------------------------------------
                    log_msg = 'ADVERTENCIA: EN PROCESO DE AUTORIZACION - ' + str(error_message).replace("'", "")
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    self.estado = "02"  # SRI EN PROCESO
                    return

                # ------------------------------------------------------------------------------------------------------
                # ODOO: ENVIO DE CORREO ELECTRONICO CON ADJUNTOS RIDE & XML
                # ----------------------------------------------------------
                try:
                    adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion)])
                    self.send_document(
                        attachments=[a.ids for a in adjuntos_ids],
                        template='l10n_ec_invoice.email_template_invoice'
                    )
                    log_msg = 'CORREO ELECTRONICO ENVIADO A: ' + self.partner_id.email + ' - (Ok)'
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    # ------------------------------------------------------
                    # UNLINK ELIMINA EL PDF EN EXCESO QUE GENERA EL SISTEMA
                    # ------------------------------------------------------
                    adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion)])
                    adjuntos_ids[1].unlink()
                    adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion)])
                    a=1
                except Exception as error_message:
                    # ----------------------------------------------------------
                    # WARNING EN ENVIO DE CORREO CON ARCHIVOS ADJUNTOS RIDE Y XML
                    # ----------------------------------------------------------
                    log_msg = 'ADVERTENCIA: Envío de correo electrónico - ' + str(error_message).replace("'", "").upper()
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    return

        except Exception as error_message:
            # ------------------------------------------------------------------------------------
            # ERROR DENTRO DE ESTE PROCESO DETIENE LA VALIDACION DEL FORMULARIO DE ODOO
            # ------------------------------------------------------------------------------------
            log_msg = 'ERROR: Módulo - procesar_individual() - ' + str(error_message).replace("'", "").upper()
            logging.info(log_msg)
            self.history_log(log_msg)
            self.estado = "00"  # ERROR
        # ---------------------------------------------
        # TERMINA NORMALMENTE EL PROCESO DE VALIDACION
        # ---------------------------------------------
        return

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def documento_electronico_lc(self):

        inv_xml = {}
        fechaAutorizacion = {}

        # ------------------------------------------------------
        # UNLINK ELIMINA todos los archivos si existiere alguno
        # ------------------------------------------------------
        ADJUNTOS_IDS = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion_lc)])
        for adjuntos_ids in ADJUNTOS_IDS:
            adjuntos_ids.unlink()
        adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion_lc)])
        ADJUNTOS_IDS = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion)])
        for adjuntos_ids in ADJUNTOS_IDS:
            adjuntos_ids.unlink()
        adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion)])

        # --------------------------------------------------------------------------------------------------------------
        # INICIA EL PROCESO DE VALIDACION DE COMPROBANTES ELECTRONICOS EN EL SRI
        # -----------------------------------------------------------------------
        try:
            log_msg = '–––––––––––––––––––– COMPROBANTE ELECTRONICO –––––––––––––––––––––'
            logging.info(log_msg)
            self.history_log(log_msg)

            log_msg = 'TIPO: %s' % 'LIQUIDACION DE COMPRA' + ' No: ' + self.doc_electronico_no_lc
            logging.info(log_msg)
            self.history_log(log_msg)

            log_msg = 'CLAVE DE ACCESO: ' + self.doc_electronico_no_autorizacion
            logging.info(log_msg)
            self.history_log(log_msg)

            # if self.estado_lc == '01' or self.estado_lc == '02' or self.estado_lc == '03':  # PENDIENTE, AUTORIZADO o EN PROCESO
            # ------------------------------------------------------------------------------------------------------
            # ODOO: LECTURA DEL ARCHIVO XML archivo_basico Y CORRECCION DE CARCATERES
            # ESPECIALES DE ESTE ARCHIVO EN archivo_basico_fix_xml
            # ------------------------------------------------------------------
            try:
                ruta_archivo_xml = self.company_id.company_ruta_documentos
                nombre_archivo_xml = ruta_archivo_xml + self.doc_electronico_xml_lc
                # ----------------------------------------------------------------------
                # RECUPERA DEL DISCO EL ARCHIVO XML EN FORMATO TEXTO archivo_basico_xml
                # ----------------------------------------------------------------------
                archivo_basico = open(nombre_archivo_xml, "r", encoding='utf8')
                archivo_basico_xml = archivo_basico.read()
                log_msg = 'LECTURA DE INFORMACION'
                logging.info(log_msg)
                self.history_log(log_msg)
                # ----------------------------------------------------------------------
                # CAMBIA LOS CARACTERES ESPECIALES Y CREA archivo_basico_fix_xml
                # ----------------------------------------------------------------------
                archivo_basico_fix_xml = self.replace_fix_chars(archivo_basico_xml)

            except Exception as error_message:
                # ------------------------------------------------------------------
                # ERROR DE LECTURA Y DE CAMBIO DE CARACTERES DEL archivo_basico_xml
                # ------------------------------------------------------------------
                log_msg = 'ERROR: Lectura/Modificiación archivo_basico_xml - ' + str(error_message).replace("'","").upper()
                logging.info(log_msg)
                self.history_log(log_msg)
                self.estado_lc = "00"  # ERROR
                return

            # ------------------------------------------------------------------------------------------------------
            # SRI: CARGA EL ESQUEMA PARA EL TIPO DE DOCUMENTO ELECTRONICO Y
            # VALIDA EL ARCHIVO archivo_basico_fix_xml EN EL FORMATO XML
            # --------------------------------------------------------------
            try:
                # -------------------------------------------------
                # DEFINE inv_xml EN FUNCION DEL ESQUEMA ESPECIFICO
                # -------------------------------------------------
                if self.tipo_documento_tributario == 'DOCUMENTO DE COMPRA':
                    inv_xml = DocumentXML(archivo_basico_fix_xml, 'purchase_clearance')
                # -----------------------------------------------------------
                # VALIDA EL ARCHIVO archivo_basico_fix_xml EN EL FORMATO XML
                # -----------------------------------------------------------
                validador, mensaje_autorizacion = inv_xml.validate_xml()
                if not validador:
                    log_msg = 'ERROR: de validación XML - ' + str(mensaje_autorizacion).replace("'", "")
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    self.estado_lc = "00"  # ERROR
                    return
                log_msg = 'VALIDACION PREVIA AL ENVIO'
                logging.info(log_msg)
                self.history_log(log_msg)
            except Exception as error_message:
                # -------------------------------------------------------------------
                # ERROR DE LECTURA DE ESQUEMA Y VALIDACION ETREE DEL ARCHIVO XML FIX
                # -------------------------------------------------------------------
                log_msg = 'ERROR: Proceso validación XML - ' + str(error_message).replace("'", "")
                logging.info(log_msg)
                self.history_log(log_msg)
                self.estado_lc = "00"  # ERROR
                return

            # ------------------------------------------------------------------------------------------------------
            # XADES: AÑADE LA FIRMA ELECTRONICA AL ARCHIVO XML
            # ------------------------------------------
            try:
                # -------------------------------------------------
                # XMLRPC: GENERA LOS ARGUMENTOS DE LA API
                # -------------------------------------------------
                password = self.company_id.password_electronic_signature
                # ----------------------------------------------------
                # CONEXION DE SERVICIOS WEB XMLRPC
                # SE CONECETA CON LA BASE DE DATOS sri CREADA EN ODDO
                # Y UBICADA EN UN SERVIDOR EXTERNO
                # ----------------------------------------------------
                host_port = self.company_id.ip_ruc
                db = 'sri'
                user = self.env['res.users'].search([('id', '=', 2)]).login
                pwd = self.env['res.partner'].search([('id', '=', 1)]).vat
                srv = 'http://%s' % (host_port)
                # -------------------------------------------------
                # XMLRPC: VERIFICA CONECCION Y AUTENTIFICA
                # -------------------------------------------------
                common = xmlrpclib.ServerProxy('%s/xmlrpc/common' % srv)  # VERIFICACION
                server_version = common.version()['server_version']
                uid = common.authenticate(db, user, pwd, {})  # AUTENTIFICACION
                if not uid:
                    # -------------------------------------------------
                    # ERROR EN XADES: USURIO NO REGISTRADO EN BASE sri
                    # -------------------------------------------------
                    log_msg = 'ERROR: Usuario o clave de usuario no registrados a la FIRMA ELECTRONICA. Consulte con su asesor de Odoo'
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    self.estado = "00"  # ERROR
                    return
                log_msg = 'CONECTANDO CON SERVIDOR: ' + srv + ' ODOO Version: ' + server_version + ' USUARIO REGISTRADO id: ' + str(
                    uid)
                logging.info(log_msg)
                # --------------------------------------------------------
                # XADES REMOTO: FIRMA ELECTRONICA
                # XMLRPC: ACTIVA LA Application Programming Interface API
                # --------------------------------------------------------
                api = xmlrpclib.ServerProxy('%s/xmlrpc/object' % srv)

                archivo_firmado_xml = api.execute_kw(db, uid, pwd, 'sri.ruc', 'firma_electronica', [[]],
                                                     {
                                                         'archivo_basico_fix_xml': archivo_basico_fix_xml,
                                                         'password': password,
                                                         'user_id': uid
                                                     }
                                                     )
                # -------------------------------------------------
                # ERROR EN XADES: FIRMA ELECTRONICA DEL DOCUMENTO
                # -------------------------------------------------
                if "No se puede generar KeyStore" in archivo_firmado_xml:
                    message = archivo_firmado_xml.split("\n")[0] + " / " + archivo_firmado_xml.split("\n")[1]
                    log_msg = 'ERROR: En firma electrónica Xades() - ' + str(message).replace("'", "").upper()
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    self.estado = "00"  # ERROR
                    return

                # -------------------------------------------------
                # XADES LOCAL: FIRMA ELECTRONICA DEL DOCUMENTO
                # -------------------------------------------------
                # xades = Xades()
                # archivo_pk12 = self.company_id.electronic_signature
                # password = self.company_id.password_electronic_signature
                # archivo_firmado_xml = xades.sign(archivo_basico_fix_xml, archivo_pk12, password)
                # archivo_firmado_xml = archivo_firmado_xml.decode('ascii')

                log_msg = 'FIRMA ELECTRONICA DEL DOCUMENTO - (Ok)'
                logging.info(log_msg)
                self.history_log(log_msg)
            except Exception as error_message:
                # -------------------------------------------------
                # ERROR EN XADES: FIRMA ELECTRONICA DEL DOCUMENTO
                # -------------------------------------------------
                log_msg = 'ERROR: En firma electrónica Xades() - ' + str(error_message).replace("'", "").upper()
                logging.info(log_msg)
                self.history_log(log_msg)
                self.estado_lc= "00"  # ERROR
                return
            # ------------------------------------------------------------------------------------------------------
            # SRI: VALIDAR COMPROBANTE - CONEXION, ENVIO DEL XML
            # -----------------------------
            try:
                # ----------------------------------------------------------------------------
                # DETERMINA EL TIPO DE CONECCION CON EL SRI (PRUEBAS/PRODUCCION/ON O OFFLINE)
                # ----------------------------------------------------------------------------
                url_recepcion, url_autorizacion = self.company_id._get_ws()
                # --------------------------
                # ENVIA EL DOCUMENTO AL SRI
                # --------------------------
                validador_recepcion, errores, codigo_error, respuesta_sri = inv_xml.send_receipt(
                    archivo_firmado_xml, url_recepcion)

                if not validador_recepcion:
                    # --------------------------------------------------------------------------------------------------------
                    # SI validador_recepcion == False --> EL SRI EMITIÓ UN ERROR EN LA VALIDACION DEL COMPROBANTE ELECTRONICO
                    # --------------------------------------------------------------------------------------------------------
                    # if codigo_error != '70' and codigo_error != '43':
                    if codigo_error in [2, 10, 26, 27, 28, 35, 36, 37, 39, 40, 45, 46,
                                        47, 48, 49, 50, 52, 56, 57, 58, 63, 65, 67, 80]:
                        # -----------------------------------------------------------------------------------
                        # CODIGOS DE ERRORES DE WS validarComprobante QUE DETIENEN EL PROCESO DE FACTURACION
                        # ESTOS DOCUMENTOS DEBEN REVISARSE Y ANULARSE EN EL SISTEMA. PUEDE QUE REQUIERAN
                        # REVISION EN LA CODIFICACION
                        # -----------------------------------------------------------------------------------
                        log_msg = 'ERROR: Web Service SRI ValidarComprobante: ' + str(errores).replace("'", "").upper()
                        logging.info(log_msg)
                        self.history_log(log_msg)
                        self.estado = "00"  # ERROR
                        return
                    if codigo_error in [34, 42, 52, 64, 65, 69]:
                        # -----------------------------------------------------------------------------------
                        # CODIGOS DE ERRORES DE WS validarComprobante QUE DETIENEN EL PROCESO DE FACTURACION
                        # ESTOS ERRORES DEBEN SER PARTE DEL SISTEMA CONTABLE PARA EVITAR LA GENERACION Y
                        # ENVIO DE COMPROBANTES AL SRI POR PARTE DE LOS DESARROLLADORES
                        # -----------------------------------------------------------------------------------
                        log_msg = 'ERROR: ValidarComprobante - Documento no cumple requisitos de norma tributaria: ' + \
                                  str(errores).replace("'", "").upper()
                        logging.info(log_msg)
                        self.history_log(log_msg)
                        self.estado = "00"  # ERROR
                        return
                    # -----------------------------------------------------------------------------------------
                    # CODIGOS DE ERRORES DE WS validarComprobante QUE NO DETIENEN EL PROCESO DE FACTURACION
                    # GENERAN UNA ADVENTENCIA Y CONTINUAN EL PROCESO
                    # CUALQUIER ERROR NO LISTADO Y LOS ERRORES DE COMUNICACION Y RECEPCION DEL SRI NO DETIENEN
                    # EL PROCESO DE FACTURACION DE ODOO. SE EMITIRA EL RIDE Y XML SIN FECHA DE AUTORIZACION
                    # -----------------------------------------------------------------------------------------
                    # ----------------------------------------------------------------
                    # SI EL codigo_error == 70 --> CLAVE DE ACCESO EN PROCESAMIENTO O
                    # SI EL codigo_error == 43 --> CLAVE DE ACCESO REGISTRADA
                    # ADVIERTE LOS CODIGOS Y CONTINUA CON EL PROCESO DE AUTORIZACION
                    # ----------------------------------------------------------------
                    if codigo_error != '70' and codigo_error != '43':
                        codigo_error = ' PROBLEMAS DE COMUNICACION CON EL WS DEL SRI:'
                    log_msg = 'SRI: ADVERTENCIA AL VALIDAR EL COMPROBANTE: ' + ' ' + str(errores).replace("'", "")
                    logging.info(log_msg)
                    self.history_log(log_msg)
                else:
                    # ---------------------------------------------------------------
                    # SI validador_recepcion == True --> ACTUALIZA EL LOG Y CONTINUA
                    # ---------------------------------------------------------------
                    log_msg = 'ENVIO ARCHIVO XML FIRMADO AL SRI - (Ok)'
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    log_msg = 'SRI: Respuesta: %s' % respuesta_sri
                    logging.info(log_msg)
                    self.history_log(log_msg)

            except Exception as error_message:
                # -------------------------------------------------
                # ERROR EN VALIDADOR DE RECEPCION DEL SRI
                # -------------------------------------------------
                log_msg = 'ADVERTENCIA: En Validador Recepción SRI - ' + str(error_message).replace("'", "").upper()
                logging.info(log_msg)
                self.history_log(log_msg)
                self.estado = "02"  # SRI EN PROCESO
            # ------------------------------------------------------------------------------------------------------
            # SRI: AUTORIZACION
            # ------------------
            try:
                # --------------------------------
                # SOLICITA LA AUTORIZACION AL SRI
                # --------------------------------
                autorizacion, mensaje_autorizacion = inv_xml.request_authorization(self.doc_electronico_no_autorizacion_lc, url_autorizacion)
                log_msg = 'SOLICITUD DE AUTORIZACION AL SRI'
                logging.info(log_msg)
                self.history_log(log_msg)
                # --------------------------------------------------------------------------------------
                # SI autorizacion == False --> ERROR AL RECIBIR EL CODIGO DE AUTORIZACION DEL DOCUMENTO
                # mensaje_autorizacion CONTIENE EL MENSAJE DE ERROR
                # SE DETIENE EL PROCESO DE VALIDACION DEL self EN ODOO
                # --------------------------------------------------------------------------------------
                # ERROR DENTRO DE ESTE PROCESO DETIENE LA VALIDACION DEL FORMULARIO DE ODOO
                # --------------------------------------------------------------------------------------
                if not autorizacion:
                    msg = ' '.join(list(itertools.chain(*mensaje_autorizacion)))
                    log_msg = 'ERROR: Autorización SRI reporta - ' + str(msg).replace("'", "").upper()
                    logging.info(log_msg)
                    self.history_log(log_msg)
                    self.estado_lc = "00"  # ERROR
                    return
                else:
                    # ---------------------------------------------------
                    # AÑADE LA AUTORIZACION DEL SRI AL DOCUMENTO FIRMADO
                    # ---------------------------------------------------
                    if mensaje_autorizacion == "SIN INFORMACION":
                        # ---------------------------------------------------
                        # GENERACION DE ADJUNTOS SIN FECHA DE AUTORIZACION
                        # ---------------------------------------------------
                        autorizacion_xml = archivo_firmado_xml

                        log_msg = 'SRI: CLAVE DE ACCESO SIN REGISTRO EN EL SRI. POSIBLES PROBLEMAS DE COMUNICACION.\n\tINTENTAR MAS TARDE NUEVAMENTE'
                        logging.info(log_msg)
                        self.history_log(log_msg)
                        self.estado = "02"  # SRI EN PROCESO

                        # adjuntos_ids = self.add_attachment(autorizacion_xml)[0]

                        self.add_attachment_xml(autorizacion_xml)[0]
                        self.add_attachment_pdf(autorizacion_xml)[0]

                        log_msg = 'ODOO: SE GENERARON RIDE & XML SIN FECHA DE AUTORIZACION - (Ok)'
                        logging.info(log_msg)
                        self.history_log(log_msg)

                    else:
                        # ---------------------------------------------------
                        # GENERACION DE ADJUNTOS CON FECHA DE AUTORIZACION
                        # ---------------------------------------------------
                        autorizacion_xml = self.render_authorized_document(autorizacion)
                        # ---------------------------------------------
                        # EXTRAE fechaAutorizacion DESDE autorizacion_xml
                        # ---------------------------------------------
                        root = ET.fromstring(autorizacion_xml)
                        for autorizacion in root.iter('autorizacion'):
                            fechaAutorizacion = autorizacion.find('fechaAutorizacion').text
                        # -------------------------------------------------
                        # ACTUALIZA doc_electronico_fecha_autorizacion_lc EN
                        # EL CORRESPONDIENTE self DE account.invoice
                        # ESTO PERMITE AÑADIR ESTA FECHA EN EL RIDE
                        # -------------------------------------------------
                        self.doc_electronico_fecha_autorizacion_lc = fechaAutorizacion

                        log_msg = 'SRI: DOCUMENTO AUTORIZADO - (Ok)'
                        logging.info(log_msg)
                        self.history_log(log_msg)
                        self.estado_lc = "03"  # SRI AUTORIZADO

                        # adjuntos_ids = self.add_attachment(autorizacion_xml)[0]

                        self.add_attachment_xml(autorizacion_xml)[0]
                        self.add_attachment_pdf(autorizacion_xml)[0]

                        log_msg = 'ODOO: SE GENERARON RIDE & XML CON FECHA DE AUTORIZACION - (Ok)'
                        logging.info(log_msg)
                        self.history_log(log_msg)

            except Exception as error_message:
                # ------------------------------------------------------------------------------
                # WARNING EN PROCESO DE AUTORIZACION Y GENERACION DE ARCHIVOS ADJUNTOS RIDE Y XML
                # ------------------------------------------------------------------------------
                log_msg = 'ADVERTENCIA: EN PROCESO DE AUTORIZACION - ' + str(error_message).replace("'", "").upper()
                logging.info(log_msg)
                self.history_log(log_msg)
                self.estado = "02"  # SRI EN PROCESO
                return

            # ------------------------------------------------------------------------------------------------------
            # ODOO: ENVIO DE CORREO ELECTRONICO CON ADJUNTOS RIDE & XML
            # ----------------------------------------------------------
            try:
                adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion_lc)])
                self.send_document(
                    attachments=[a.ids for a in adjuntos_ids],
                    template='l10n_ec_invoice.email_template_purchase_clearance'
                )
                log_msg = 'CORREO ELECTRONICO ENVIADO A: ' + self.partner_id.email + ' - (Ok)'
                logging.info(log_msg)
                self.history_log(log_msg)
                # ------------------------------------------------------
                # UNLINK ELIMINA EL PDF EN EXCESO QUE GENERA EL SISTEMA
                # ------------------------------------------------------
                adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion)])
                adjuntos_ids.unlink()
                adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion)])
                adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion_lc)])
                adjuntos_ids[1].unlink()
                adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion_lc)])
                a=1
            except Exception as error_message:
                # ----------------------------------------------------------
                # WARNING EN ENVIO DE CORREO CON ARCHIVOS ADJUNTOS RIDE Y XML
                # ----------------------------------------------------------
                log_msg = 'ADVERTENCIA: Envío de correo electrónico - ' + str(error_message).replace("'", "").upper()
                logging.info(log_msg)
                self.history_log(log_msg)
                return

        except Exception as error_message:
            # ------------------------------------------------------------------------------------
            # ERROR DENTRO DE ESTE PROCESO DETIENE LA VALIDACION DEL FORMULARIO DE ODOO
            # ------------------------------------------------------------------------------------
            log_msg = 'ERROR: Módulo - procesar_individual() - ' + str(error_message).replace("'", "").upper()
            logging.info(log_msg)
            self.history_log(log_msg)
            self.estado_lc = "00"  # ERROR
        # ---------------------------------------------
        # TERMINA NORMALMENTE EL PROCESO DE VALIDACION
        # ---------------------------------------------
        return

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def procesar_individual(self):
        # ----------------------------------------------------------
        # VALIDACION DE EXISTENCIA DE CUENTAS DE CORREO ELECTRONICO
        # ----------------------------------------------------------
        if self.company_id.email:
            correo_emisor = self.company_id.email.lower().replace(' ','')
        else:
            error_message = "DIRECCION DE CORREO INEXISTENTE DE " + self.company_id.name
            log_msg = 'ERROR: PROCESO INDIVIDUAL - ' + str(error_message).replace("'", "").upper()
            logging.info(log_msg)
            self.history_log(log_msg)
            self.estado = "00"  # ERROR
            return

        if self.partner_id.email:
            correo_receptor = self.partner_id.email.lower().replace(' ','')
        else:
            error_message = "DIRECCION DE CORREO INEXISTENTE DE " + self.partner_id.name
            log_msg = 'ERROR: PROCESO INDIVIDUAL - ' + str(error_message).replace("'", "").upper()
            logging.info(log_msg)
            self.history_log(log_msg)
            self.estado = "00"  # ERROR
            return

        # -------------------------------------------------------
        # VALIDACION DEL NUMERO DE CUENTAS DE CORREO ELECTRONICO
        # -------------------------------------------------------
        no_emisor = len(correo_emisor.split(","))
        no_receptor = len(correo_receptor.split(","))
        if no_emisor > 1:
            error_message = "EMISOR, UNA SOLA CUENTA DE CORREO DE ENVIO (" + correo_emisor + ') ' + no_emisor
            log_msg = 'ERROR: PROCESO INDIVIDUAL - ' + str(error_message).replace("'", "").upper()
            logging.info(log_msg)
            self.history_log(log_msg)
            self.estado = "00"  # ERROR
            return

        # -------------------------------------------------------
        # VALIDACION DE FORMATO DE CUENTAS DE CORREO ELECTRONICO
        # -------------------------------------------------------
        if not re.match('^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}$', correo_emisor):
            error_message = "FORMATO INCORRECTO DE CORREO (" + correo_emisor + ') DE ' + self.company_id.name
            log_msg = 'ERROR: PROCESO INDIVIDUAL - ' + str(error_message).replace("'", "").upper()
            logging.info(log_msg)
            self.history_log(log_msg)
            self.estado = "00"  # ERROR
            return

        for correo in correo_receptor.split(","):
            if not re.match('^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}$', correo):
                error_message = "FORMATO INCORRECTO DE CORREO (" + correo + ') DE ' + self.partner_id.name
                log_msg = 'ERROR: PROCESO INDIVIDUAL - ' + str(error_message).replace("'", "").upper()
                logging.info(log_msg)
                self.history_log(log_msg)
                self.estado = "00"  # ERROR
                return

        # -------------------------------------------------------
        # VALIDACION DE COMPROBANTES DE RETENCION EN CERO
        # -------------------------------------------------------
        if self.bool_doc_enviado == False:
            return

        # -------------------------------------------------------------------
        # INICIO PROCESO DE VALIDACION DEL COMPROBANTE ELECTRONICO EN EL SRI
        # -------------------------------------------------------------------
        try:
            if self.tipo_comprobante == '03' and self.estado_lc != '00':
                self.documento_electronico_lc()
            if self.estado != '00':
                self.documento_electronico()
            else:
                return
        except Exception as error_message:
            # ------------------------------------------------------------------------------------
            # CUALQUIER ERROR DENTRO DE ESTE PROCESO DETIENE LA VALIDACION DEL FORMULARIO DE ODOO
            # ------------------------------------------------------------------------------------
            log_msg = 'ERROR: (procesar_individual) ' + str(error_message).replace("'", "").upper()
            logging.info(log_msg)

            self.history_log(log_msg)
            if self.tipo_comprobante == '03' and self.estado_lc != '00':
                self.estado_lc = "00"  # ERROR
                self.estado = "00"  # ERROR
            else:
                self.estado = "00"  # ERROR
            raise UserError(str(error_message))
        # -------------------------------
        # REFRESCA LA PANTALLA Y RETORNA
        # -------------------------------
        return {'type': 'ir.actions.client', 'tag': 'reload', }

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # @api.multi
    # def procesar_listado(self):
        # ----------------------------------------------------
        # LLAMA A TODOS LOS FORMULARIOS PENDIENTES DE PROCESO
        # ----------------------------------------------------
        # company = self.env['res.company'].search([('id', '=', self.company_id.id)])
        # FORMULARIOS = self.env['account.invoice'].search([('estado', 'in', ['01', '02', '03'])])
        # log_msg = 'DOCUMENTOS ELECTRONICOS: Iniciando validación masiva en el SRI'
        # logging.info(log_msg)
        # ---------------------------------------------
        # PROCESA UNO A UNO LOS FORMULARIOS PENDIENTES
        # ---------------------------------------------
        # for formulario in FORMULARIOS:
            # formulario.procesar_individual()

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def re_enviar_correo(self):
        try:
            # ------------------------------------------------------
            # SI EL DOCUMENTO ES UNA LIQUIDACION DE COMPRA LC
            # ------------------------------------------------------
            if self.tipo_comprobante == '03' and self.estado_lc != '00':
                # ------------------------------------------------------
                # ENVIA CORREO DE LIQUIDACION DE COMPRA
                # ------------------------------------------------------
                adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion_lc)])
                if adjuntos_ids and self.message_attachment_count == 4:
                    self.send_document(
                        attachments=[a.ids for a in adjuntos_ids],
                        template='l10n_ec_invoice.email_template_purchase_clearance'
                    )
                    log_msg = 'CORREO ELECTRONICO ENVIADO A: ' + self.partner_id.email + ' - (Ok)'
                    logging.info(log_msg)
                    self.history_log(log_msg)
                # ------------------------------------------------------
                # ENVIA CORREO DEL COMPROBANTE DE RETENCION CR
                # ------------------------------------------------------
                adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion)])
                if adjuntos_ids and self.message_attachment_count == 4:
                    self.send_document(
                        attachments=[a.ids for a in adjuntos_ids],
                        template='l10n_ec_invoice.email_template_invoice'
                    )
                    log_msg = 'CORREO ELECTRONICO ENVIADO A: ' + self.partner_id.email + ' - (Ok)'
                    logging.info(log_msg)
                    self.history_log(log_msg)
            # ------------------------------------------------------
            # SI EL DOCUMENTO NO ES UNA LIQUIDACION DE COMPRA
            # ------------------------------------------------------
            if self.estado != '00':
                # ---------------------------------------------------------
                # ENVIA CORREO DEL COMPROBANTE ELECTRONICO: CR, FV, NC, GR
                # ---------------------------------------------------------
                adjuntos_ids = self.env['ir.attachment'].search([('name', 'like', self.doc_electronico_no_autorizacion)])
                if adjuntos_ids and self.message_attachment_count == 2:
                    self.send_document(
                        attachments = [a.ids for a in adjuntos_ids],
                        template='l10n_ec_invoice.email_template_invoice'
                    )
                    log_msg = 'CORREO ELECTRONICO ENVIADO A: ' + self.partner_id.email + ' - (Ok)'
                    logging.info(log_msg)
                    self.history_log(log_msg)

        except Exception as error_message:
            # ----------------------------------------------------------
            # ERROR EN ENVIO DE CORREO CON ARCHIVOS ADJUNTOS RIDE Y XML
            # ----------------------------------------------------------
            log_msg = 'ERROR: Envío de correo electrónico - ' + str(error_message).replace("'", "").upper()
            logging.info(log_msg)
            self.history_log(log_msg)
            self.estado = "00"  # ERROR
            return

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def replace_fix_chars(self, code):
        # ----------------------------------------------------------------------
        # REEMPLAZA LOS CARACTERES ESPECIALES POR CARACTERES COMUNES EN EL code
        # ----------------------------------------------------------------------
        special = [
            ['º', 'o'],
            ['Ñ', 'N'],
            ['ñ', 'n'],
            ['&', 'y'],
            ['á', 'a'],
            ['é', 'e'],
            ['í', 'i'],
            ['ó', 'o'],
            ['ú', 'u'],
            ['à', 'a'],
            ['è', 'e'],
            ['ì', 'i'],
            ['ò', 'o'],
            ['ù', 'u'],
            ['ü', 'u'],
            ['Á', 'A'],
            ['É', 'E'],
            ['Í', 'I'],
            ['Ó', 'O'],
            ['Ú', 'U'],
            ['À', 'A'],
            ['È', 'E'],
            ['Ì', 'I'],
            ['Ò', 'O'],
            ['Ù', 'U'],
            ['Ü', 'U'],
        ]
        if code:
            for f, r in special:
                code = code.replace(f, r)
        return code

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.one
    def add_attachment_xml(self, xml_element):

        report_id = {}
        nombre_archivo = ""
        attach_ids = []

        if self.tipo_documento_tributario == 'DOCUMENTO DE COMPRA':
            if 'liquidacionCompra' in xml_element:
                report_id = 'l10n_ec_invoice.l10n_ec_invoice_purchase_clearance'
                nombre_archivo = self.doc_electronico_no_autorizacion_lc
            else:
                report_id = 'l10n_ec_invoice.l10n_ec_invoice_retention'
                nombre_archivo = self.doc_electronico_no_autorizacion
        if self.tipo_documento_tributario == 'FACTURA DE VENTA':
            report_id = 'l10n_ec_invoice.l10n_ec_invoice_out_invoice'
            nombre_archivo = self.doc_electronico_no_autorizacion
        if self.tipo_documento_tributario == 'NOTA DE CREDITO DE VENTA':
            report_id = 'l10n_ec_invoice.l10n_ec_invoice_out_refund'
            nombre_archivo = self.doc_electronico_no_autorizacion
        if self.tipo_documento_tributario == 'GUIA DE REMISION':
            report_id = 'l10n_ec_invoice.l10n_ec_invoice_delivery_guide'
            nombre_archivo = self.doc_electronico_no_autorizacion

        # ---------------------------------------------------------------------------------
        # ADICIONA LOS ARCHIVOS ADJUNTOS XML Y PDF AL FORMULARIO DEL DOCUMENTO ELECTRONICO
        # EN ESTE ESTADO GENERA LOS ARCHIVOS SIN LA AUTORIZACION DEL SRI
        # ---------------------------------------------------------------------------------
        # ------------
        # ARCHIVO XML
        # ------------
        buf = StringIO()
        buf.write(xml_element)
        document = base64.encodebytes(buf.getvalue().encode()).decode('ascii')
        buf.close()

        attach = self.env['ir.attachment'].create(
            {
                'name': '{0}.xml'.format(nombre_archivo),
                'datas': document,
                'datas_fname': '{0}.xml'.format(nombre_archivo),
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary'
            },
        )
        return attach_ids.append(attach)

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.one
    def add_attachment_pdf(self, xml_element):

        report_id = {}
        nombre_archivo = ""
        attach_ids = []
        ids = []

        if self.tipo_documento_tributario == 'DOCUMENTO DE COMPRA':
            if 'liquidacionCompra' in xml_element:
                report_id = 'l10n_ec_invoice.l10n_ec_invoice_purchase_clearance'
                nombre_archivo = self.doc_electronico_no_autorizacion_lc
            else:
                report_id = 'l10n_ec_invoice.l10n_ec_invoice_retention'
                nombre_archivo = self.doc_electronico_no_autorizacion
        if self.tipo_documento_tributario == 'FACTURA DE VENTA':
            report_id = 'l10n_ec_invoice.l10n_ec_invoice_out_invoice'
            nombre_archivo = self.doc_electronico_no_autorizacion
        if self.tipo_documento_tributario == 'NOTA DE CREDITO DE VENTA':
            report_id = 'l10n_ec_invoice.l10n_ec_invoice_out_refund'
            nombre_archivo = self.doc_electronico_no_autorizacion
        if self.tipo_documento_tributario == 'GUIA DE REMISION':
            report_id = 'l10n_ec_invoice.l10n_ec_invoice_delivery_guide'
            nombre_archivo = self.doc_electronico_no_autorizacion

        # ------------
        # ARCHIVO PDF
        # -----------------------------------------------------------------------------
        # self.tipo DEFINE EL TIPO DE REPORTE XML A USARSE PARA LA GENERACION DEL RIDE
        # -----------------------------------------------------------------------------
        ids.append(self.id)
        datas = {'ids': ids, 'model': self._name}

        if report_id:
            attachment_obj = self.env['ir.attachment']
            pdf = self.env.ref(report_id)
            try:
                pdf = pdf.render_qweb_pdf(self.ids)
            except Exception as error_message:
                # ------------------------------------------------------------------------------------
                # CUALQUIER ERROR DENTRO DE ESTE PROCESO DETIENE LA VALIDACION DEL FORMULARIO DE ODOO
                # ------------------------------------------------------------------------------------
                log_msg = 'ERROR: (Añadir archivos) ' + str(error_message).replace("'", "").upper()
                logging.info(log_msg)
                self.history_log(log_msg)
                self.estado = "ERROR"
                return

            ride = base64.b64encode(pdf[0])
            attach = attachment_obj.create({
                'name': '{0}.pdf'.format(nombre_archivo),
                'type': 'binary',
                'datas': ride,
                'datas_fname': '{0}.pdf'.format(nombre_archivo),
                'res_model': self._name,
                'res_id': self.id,
            })
            attach_ids.append(attach)
        return attach_ids

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def send_document(self, attachments=None, template=False):
        template = self.env.ref(template)
        # ------------------------------------------------------------------------------------
        # attachments ES UNA LISTA CON LOS IDS DE LOS ATTACHMENTS AÑADIDOS
        # attach ES UNA TUPLA PARA INGRESAR EN attachment_ids DE LA FUNCION send_mail DE ODOO
        # ------------------------------------------------------------------------------------
        attach = ()
        for element in attachments:
            tuple_element = (element[0],)
            attach = attach + tuple_element
        msg_email = template.send_mail(
            self.id,
            force_send=False,
            raise_exception=True,
            email_values={
                'attachment_ids': attach
            },
        )
        if msg_email:
            return True
        else:
            return False

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def history_log(self, msg=None):
        utc_now = datetime.now()
        pst_now = utc_now.astimezone(pytz.timezone("America/Guayaquil"))
        Fecha_pst_now = pst_now.strftime("%d/%m/%Y %H:%M:%S")
        if not self.historial:
            self.historial = str(Fecha_pst_now) + ' - ' + str(msg) + '\n'
        else:
            self.historial = self.historial + str(Fecha_pst_now) + ' - ' + str(msg) + '\n'

    def render_authorized_document(self, autorizacion):
        tmpl_path = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(tmpl_path))
        edocument_tmpl = env.get_template('authorized_withdrawing.xml')
        auth_xml = {
            'estado': autorizacion.estado,
            'numeroAutorizacion': autorizacion.numeroAutorizacion,
            'ambiente': autorizacion.ambiente,
            'fechaAutorizacion': str(autorizacion.fechaAutorizacion.strftime("%d/%m/%Y %H:%M:%S")),  # noqa
            'comprobante': autorizacion.comprobante
        }
        auth_withdrawing = edocument_tmpl.render(auth_xml)
        return auth_withdrawing

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def imprimir_comprobante(self):
        if self.tipo_documento_tributario == 'FACTURA DE VENTA':
            return self.env.ref('l10n_ec_invoice.l10n_ec_invoice_out_invoice').report_action(self)
        if self.tipo_documento_tributario == 'NOTA DE CREDITO DE VENTA':
            return self.env.ref('l10n_ec_invoice.l10n_ec_invoice_out_refund').report_action(self)
        if self.tipo_documento_tributario == 'DOCUMENTO DE COMPRA':
            return self.env.ref('l10n_ec_invoice.l10n_ec_invoice_retention').report_action(self)


    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def imprimir_liquidacion(self):
        return self.env.ref('l10n_ec_invoice.l10n_ec_invoice_purchase_clearance').report_action(self)

