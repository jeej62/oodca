# -*- coding: utf-8 -*-

from time import sleep
from odoo.exceptions import ValidationError, Warning as UserError
from lxml import etree
from lxml.etree import fromstring, DocumentInvalid
from .xades import CheckDigit
try:
    from suds.client import Client
except ImportError:
    logging.getLogger('xades.sri').info('Instalar librerias suds-jurko')


import requests
import os
from io import StringIO
import base64
import logging

SCHEMAS = {
    'withdrawing': 'schemas/retencion.xsd',
    'out_invoice': 'schemas/factura.xsd',
    'out_refund': 'schemas/nota_credito.xsd',
    'delivery': 'schemas/guia_remision.xsd',
    'in_refund': 'schemas/nota_debito.xsd',
    'purchase_clearance': 'schemas/liquidacion_compra.xsd',
}

class DocumentXML(object):
    logger = None
    _schema = False
    document = False

    @classmethod
    def __init__(self, document, type='out_invoice'):
        """
        document: XML representation
        type: determinate schema
        """
        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        self.document = fromstring(document.encode('utf-8'), parser=parser)
        self.type_document = type
        self._schema = SCHEMAS[self.type_document]
        self.signed_document = False
        self.logger = logging.getLogger('xades.sri')

    @classmethod
    def validate_xml(self):
        """
        Validar esquema XML
        """
        # self.logger.info('Validacion de esquema')
        # self.logger.debug(etree.tostring(self.document, pretty_print=True))
        respuesta_sri_error = {}
        file_path = os.path.join(os.path.dirname(__file__), self._schema)
        schema_file = open(file_path)
        xmlschema_doc = etree.parse(schema_file)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        try:
            xmlschema.assertValid(self.document)
            return True, respuesta_sri_error
        except etree.DocumentInvalid as e:
            respuesta_sri_error = e
            return False, respuesta_sri_error

    @classmethod
    def send_receipt(self, document, url_recepcion):
        # ----------------------------------------------------
        # PROCESO DE ENVIO DEL COMPROBANTE ELECTRONICO AL SRIsend_receipt
        # ----------------------------------------------------
        error_intentos = "\n"
        for i in [1, 2, 3]:
            try:
                # -------------------------------------------
                # VERIFICACION DE CONEXION CON EL WS DEL SRI
                # -------------------------------------------
                self.logger.info('ENVIO: Intento de conexión No %s' % i)
                res = requests.head(url_recepcion, timeout=3)

                # -------------------------------
                # SI NO SE GENERA ERROR CONTINUA
                # -------------------------------
                self.logger.info('ENVIO: SRI Web Service ACTIVO')
                respuesta_sri = "WS ACTIVO"
                buf = StringIO()
                buf.write(document)
                buffer_xml = base64.encodebytes(buf.getvalue().encode()).decode('ascii')
                # ----------------------------------------------
                # SE PROCEDE A VALIDAR EL COMPROBANTE EN EL SRI
                # ----------------------------------------------
                client = Client(url_recepcion)
                resultado = client.service.validarComprobante(buffer_xml)

                self.logger.info('ENVIO: Archivo xml Transferido')
                self.logger.info('ENVIO: Respuesta: %s' % resultado.estado)
                respuesta_sri = respuesta_sri + " - Respuesta SRI: " + resultado.estado

                errores = []
                codigo_error = False
                if resultado.estado == 'RECIBIDA':
                    return True, errores, codigo_error, respuesta_sri

                else:
                    for comp in resultado.comprobantes:
                        for m in comp[1][0].mensajes:
                            rs = [m[1][0].tipo, m[1][0].identificador, m[1][0].mensaje]
                            rs.append(getattr(m[1][0], 'informacionAdicional', ''))
                            errores.append(' '.join(rs))
                            codigo_error = getattr(m[1][0], 'identificador', '')
                    self.logger.error(errores)
                    respuesta_sri = respuesta_sri + " - Respuesta SRI:" + str(errores)
                    return False, ', '.join(errores), codigo_error, respuesta_sri

            except Exception as error_message:
                #  except requests.exceptions.RequestException:
                if i<=2:
                    error_intentos = error_intentos + '\t' + str(i) + ': ' + str(error_message) + '\n'
                    sleep(3)
                else:
                    respuesta_sri = ''
                    codigo_error = False
                    error_intentos = error_intentos + '\t' + str(i) + ': ' + str(error_message)
                    return False, error_intentos, codigo_error, respuesta_sri
        # -------------------
        # CONTROL DE ERRORES
        # -------------------
        log_msg = 'ENVIO: 5 intentos de conexión sin éxito. SRI Web Service NO DISPONIBLE. Intente nuevamente en un momento'
        self.logger.info(log_msg)
        respuesta_sri = log_msg
        errores = []
        codigo_error = False
        return False, errores, codigo_error, respuesta_sri


    def request_authorization(self, access_key,url_recept):
        for i in [1, 2, 3]:
            try:
                # -------------------------------------------
                # VERIFICACION DE CONEXION CON EL WS DEL SRI
                # -------------------------------------------
                self.logger.info('ODOO INTENTO DE CONEXION AL WS DEL SRI No %s' % i)
                res = requests.head(url_recept, timeout=3)
                # -------------------------------
                # SI NO SE GENERA ERROR CONTINUA
                # -------------------------------
                self.logger.info('SRI SW ESTÁ ACTIVO')
                self.logger.info('ODOO SOLICITANDO AUTORIZACION AL SRI')
                messages = []
                client = Client(url_recept)
                result = client.service.autorizacionComprobante(access_key)

                if result.numeroComprobantes=='0':
                    self.logger.info('SRI: La Clave de Acceso: ' + access_key + ' No tiene comprobantes registrados')
                    messages = "SIN INFORMACION"
                    return True, messages

                autorizacion = result.autorizaciones[0][0]
                mensajes = autorizacion.mensajes and autorizacion.mensajes[0] or []
                self.logger.info('SRI ESTADO DE DOCUMENTO: %s' % autorizacion.estado)

                for m in mensajes:
                    self.logger.error('{0} {1}'.format(m.identificador, m.mensaje))
                    messages.append([m.identificador, m.mensaje])

                if not autorizacion.estado == 'AUTORIZADO':
                    return False, messages

                return autorizacion, messages

            except requests.exceptions.RequestException:
                sleep(3)

class SriService(object):

    __AMBIENTE_PRUEBA = '1'
    __AMBIENTE_PROD = '2'
    __ACTIVE_ENV = False
    # revisar el utils
    __WS_TEST_RECEIV = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'  # noqa
    __WS_TEST_AUTH = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'  # noqa
    __WS_RECEIV = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'  # noqa
    __WS_AUTH = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'  # noqa

    __WS_TESTING = (__WS_TEST_RECEIV, __WS_TEST_AUTH)
    __WS_PROD = (__WS_RECEIV, __WS_AUTH)

    _WSDL = {
        __AMBIENTE_PRUEBA: __WS_TESTING,
        __AMBIENTE_PROD: __WS_PROD
    }
    __WS_ACTIVE = __WS_TESTING

    @classmethod
    def set_active_env(self, env_service):
        if env_service == self.__AMBIENTE_PRUEBA:
            self.__ACTIVE_ENV = self.__AMBIENTE_PRUEBA
        else:
            self.__ACTIVE_ENV = self.__AMBIENTE_PROD
        self.__WS_ACTIVE = self._WSDL[self.__ACTIVE_ENV]

    @classmethod
    def get_active_env(self):
        return self.__ACTIVE_ENV

    @classmethod
    def get_env_test(self):
        return self.__AMBIENTE_PRUEBA

    @classmethod
    def get_env_prod(self):
        return self.__AMBIENTE_PROD

    @classmethod
    def get_ws_test(self):
        return self.__WS_TEST_RECEIV, self.__WS_TEST_AUTH

    @classmethod
    def get_ws_prod(self):
        return self.__WS_RECEIV, self.__WS_AUTH

    @classmethod
    def get_active_ws(self):
        return self.__WS_ACTIVE

    @classmethod
    def create_access_key(self, values):
        """
        values: tuple ([], [])
        """
        env = self.get_active_env()
        dato = ''.join(values[0]  + values[1])
        modulo = CheckDigit.compute_mod11(dato)
        access_key = ''.join([dato, str(modulo)])
        return access_key
