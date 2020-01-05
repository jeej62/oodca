# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# Ecuador Invoice
# Localización para Odoo V12
# Por: Oodca Sociedad Anónima © <2019> <José Enríquez>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -------------------------------------------------------------------------

# ---------------------------
# Notes:    LIBRERIAS PYTHON
# ---------------------------
from odoo import api, fields, models
from datetime import datetime

import pytz
import xml.etree.ElementTree as ET


# ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
#   O   OOOOO OOOOO OOOOO O   O O   O OOOOO     OOO  O   O O   O OOOOO  OOO  OOOOO OOOOO
#  O O  O     O     O   O O   O OO  O   O        O   OO  O O   O O   O   O   O     O
# O   O O     O     O   O O   O O O O   O        O   O O O O   O O   O   O   O     OOO
# OOOOO O     O     O   O O   O O  OO   O        O   O  OO  O O  O   O   O   O     O
# O   O OOOOO OOOOO OOOOO OOOOO O   O   O       OOO  O   O   O   OOOOO  OOO  OOOOO OOOOO
# ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def archivo_retencion_xml(self):
        # --------------
        # DECLARACIONES
        # --------------
        contribuyenteEspecial = {}
        nombreComercial = {}
        documento_electronico = {}
        correo_electronico_para_envio = {}
        # ---------------------------------------------------------------
        # RUTA TEMPORAL PARA LA CREACION DEL ARCHIVO XML
        # SEARCH: Cross-platform way of getting temp directory in Python
        # ---------------------------------------------------------------
        # import tempfile
        # ruta_archivo_xml = tempfile.gettempdir() + '/'
        ruta_archivo_xml = self.company_id.company_ruta_documentos


        journal = self.journal_id
        sequence = journal.retencion_sequence_id
        prefix = sequence.prefix
        retencion_sequence_number_next = journal.retencion_sequence_number_next

        establecimiento = journal.establecimiento
        punto_emision = journal.punto_emision
        numero_secuencial = "0" * (9 - len(str(retencion_sequence_number_next))) + str(retencion_sequence_number_next)

        referencia = establecimiento + "-" + punto_emision + "-" + numero_secuencial
        # ------------------------------------------------------------------------------------
        # FECHAS: La fecha de la retención debe ser la fecha de emisión del documento de compra
        # Si fue determinada por el usuario se mantiene
        # ------------------------------------------------------------------------------------
        if not self.doc_electronico_fecha:
            fecha_documento_electronico = self.date_invoice
        else:
            fecha_documento_electronico = self.doc_electronico_fecha

        doc_electronico_xml = prefix + str(numero_secuencial) + ".xml"
        nombre_archivo = ruta_archivo_xml + doc_electronico_xml
        dirEstab = self.env['res.partner'].search(
            [('name', '=', establecimiento), ('parent_id', '=', self.company_id.id)]).street
        if dirEstab is False:
            dirEstab = self.company_id.street
        # ----------------------------------------------
        # Fecha FECHA DE EMISION CON FORMATO dd/mm/aaaa
        # ----------------------------------------------
        Fecha_str = str(self.date_invoice)
        Fecha_obj = datetime.strptime(Fecha_str, '%Y-%m-%d').date()
        Fecha = Fecha_obj.strftime("%d/%m/%Y")

        nombreComercial_company = self.env['res.partner'].search([('id', '=', self.company_id.id)]).nombre_comercial

        # ---------------------------------
        # GENERACION clave_de_autorizacion
        # -----------------------------------------------------------------------
        # SE DEFINE EL codigo_numerico SEMANA HORA MINUTO SEGUNDO Ejmp: 30122436
        # -----------------------------------------------------------------------
        utc_now = datetime.now()
        pst_now = utc_now.astimezone(pytz.timezone("America/Guayaquil"))
        codigo_numerico_semana = str('{:02}'.format(int(pst_now.strftime("%U"))))
        codigo_numerico_hora_dia = str('{:02}'.format(int(pst_now.strftime("%H"))))
        codigo_numerico_minuto_dia = str('{:02}'.format(int(pst_now.strftime("%M"))))
        codigo_numerico_segundo_hora = str('{:02}'.format(int(pst_now.strftime("%S"))))
        codigo_numerico = codigo_numerico_semana + \
                          codigo_numerico_hora_dia + \
                          codigo_numerico_minuto_dia + \
                          codigo_numerico_segundo_hora
        # Fecha_pst_now = pst_now.strftime("%d/%m/%Y %H:%M:%S")
        # ----------------------------------------------------------
        # SE DEFINE LA clave_autorizacion SIN EL DIGITO VERIFICADOR
        # ----------------------------------------------------------
        clave_autorizacion0 = str('{:02}'.format(Fecha_obj.day)) + \
                              str('{:02}'.format(Fecha_obj.month)) + \
                              str(Fecha_obj.year)               # 8D FECHA DE EMISION DDMMAAAA
        clave_autorizacion1 = "07"                              # 2D TIPO DE COMPROBANTE 07 COMPROBANTE DE RETENCION
        clave_autorizacion2 = self.company_id.vat               # 13D NUMERO RUC 1704172269001
        clave_autorizacion3 = self.company_id.env_service       # 1D TIPO AMBIENTE 1 O 2 PRUEBAS O PRODUCCION
        clave_autorizacion4 = establecimiento + punto_emision   # 6D SERIE 001002 ESTABLECIMIENTO Y UNTO DE EMISION
        clave_autorizacion5 = numero_secuencial                 # 9D NUMERO DEL COMPROBANTE SECUENCIAL
        clave_autorizacion6 = codigo_numerico                   # 8D CODIGO NUMERICO
        clave_autorizacion7 = "1"                               # 1D TIPO DE EMISION 1 NORMAL

        clave_autorizacion = clave_autorizacion0 + clave_autorizacion1 + clave_autorizacion2 + clave_autorizacion3 + \
                             clave_autorizacion4 + clave_autorizacion5 + clave_autorizacion6 + clave_autorizacion7
        # ----------------------------------------------------
        # SE INGRESA EL FACTOR DE CHEQUEO PONDERADO MODULO 11
        # ----------------------------------------------------
        factor_chequeo_ponderado = "765432765432765432765432765432765432765432765432"
        # -------------------------------
        # SE DEFINE EL digitoVerificador
        # -------------------------------
        index = 0
        suma = 0
        for n in factor_chequeo_ponderado:
            suma = suma + int(n) * int(clave_autorizacion[index])
            index = index + 1
        residuo = suma % 11
        if residuo == 0:
            digitoVerificador = 0
        elif residuo == 1:
            digitoVerificador = 1
        else:
            digitoVerificador = 11 - residuo
        # ----------------------------------------------------------
        # SE DEFINE LA clave_autorizacion CON EL DIGITO VERIFICADOR
        # ----------------------------------------------------------
        clave_autorizacion = clave_autorizacion + str(digitoVerificador)
        self.doc_electronico_no_autorizacion = clave_autorizacion
        # ------------------------------------------------------------------
        # PROCESO DE GENERACION DEL ARCHIVO XML DE RETENCIONES ELECTRONICAS
        # ------------------------------------------------------------------
        if abs(self.total_retenciones) == 0.00:
            # ------------------------------------------------------------
            # SE ACTUALIZA EN EL FORMULARIO SIN LA GENERACION DEL ARCHIVO
            # doc_electronico_xml
            # bool_doc_enviado
            # doc_electronico_fecha
            # ------------------------------------------------------------
            referencia = "SIN RETENCION"
            clave_autorizacion = codigo_numerico
            self.bool_doc_enviado = True
            doc_electronico_xml = "SIN DOCUMENTO ELECTRONICO"
        else:
            # -------------------------------------
            # comprobanteRetencion  ESTRUCTURA XML
            # -------------------------------------
            comprobanteRetencion = ET.Element("comprobanteRetencion")
            infoTributaria = ET.SubElement(comprobanteRetencion, "infoTributaria")
            infoCompRetencion = ET.SubElement(comprobanteRetencion, "infoCompRetencion")
            impuestos = ET.SubElement(comprobanteRetencion, "impuestos")
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            if self.partner_id.email:
                infoAdicional = ET.SubElement(comprobanteRetencion, "infoAdicional")
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            comprobanteRetencion.set('id', 'comprobante')
            comprobanteRetencion.set('version', '1.0.0')
            # ------------------------------
            # infoTributaria ESTRUCTURA XML
            # ------------------------------
            ambiente = ET.SubElement(infoTributaria, "ambiente")
            tipoEmision = ET.SubElement(infoTributaria, "tipoEmision")
            razonSocial = ET.SubElement(infoTributaria, "razonSocial")
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            if nombreComercial_company:
                nombreComercial = ET.SubElement(infoTributaria, "nombreComercial")
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            ruc = ET.SubElement(infoTributaria, "ruc")
            claveAcceso = ET.SubElement(infoTributaria, "claveAcceso")
            codDoc = ET.SubElement(infoTributaria, "codDoc")
            estab = ET.SubElement(infoTributaria, "estab")
            ptoEmi = ET.SubElement(infoTributaria, "ptoEmi")
            secuencial = ET.SubElement(infoTributaria, "secuencial")
            dirMatriz = ET.SubElement(infoTributaria, "dirMatriz")
            # ---------------------------------
            # infoCompRetencion ESTRUCTURA XML
            # ---------------------------------
            fechaEmision = ET.SubElement(infoCompRetencion, "fechaEmision")
            dirEstablecimiento = ET.SubElement(infoCompRetencion, "dirEstablecimiento")
            # ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            if self.company_id.company_contribuyente_especial == "SI":
                contribuyenteEspecial = ET.SubElement(infoCompRetencion, "contribuyenteEspecial")
            # ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            obligadoContabilidad = ET.SubElement(infoCompRetencion, "obligadoContabilidad")
            tipoIdentificacionSujetoRetenido = ET.SubElement(infoCompRetencion, "tipoIdentificacionSujetoRetenido")
            razonSocialSujetoRetenido = ET.SubElement(infoCompRetencion, "razonSocialSujetoRetenido")
            identificacionSujetoRetenido = ET.SubElement(infoCompRetencion, "identificacionSujetoRetenido")
            periodoFiscal = ET.SubElement(infoCompRetencion, "periodoFiscal")
            # ----------------------
            # infoTributaria TEXTOS
            # ----------------------
            ambiente.text = "1"
            tipoEmision.text = "1"
            razonSocial.text = self.company_id.name
            # :::::::::::::::::::::::::::::::::::::::::::::::::
            if nombreComercial_company:
                nombreComercial.text = nombreComercial_company
            # :::::::::::::::::::::::::::::::::::::::::::::::::
            ruc.text = self.company_id.vat
            claveAcceso.text = clave_autorizacion
            codDoc.text = "07"
            estab.text = establecimiento
            ptoEmi.text = punto_emision
            secuencial.text = numero_secuencial
            dirMatriz.text = self.company_id.street
            # -------------------------
            # infoCompRetencion TEXTOS
            # -------------------------
            fechaEmision.text = Fecha
            dirEstablecimiento.text = dirEstab
            # ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            if self.company_id.company_contribuyente_especial == "SI":
                contribuyenteEspecial.text = self.company_id.company_registry
            # ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            obligadoContabilidad.text = self.company_id.company_obligado_contabilidad
            if self.partner_id.tipo_identidad == "ruc":
                tipoIdentificacionSujetoRetenido.text = "04"
            if self.partner_id.tipo_identidad == "cedula":
                tipoIdentificacionSujetoRetenido.text = "05"
            if self.partner_id.tipo_identidad == "pasaporte":
                tipoIdentificacionSujetoRetenido.text = "06"
            razonSocialSujetoRetenido.text = self.partner_id.name
            identificacionSujetoRetenido.text = self.partner_id.numero_identidad
            periodoFiscal.text = Fecha.split('/')[1] + '/' + Fecha.split('/')[2]
            # ----------------------------
            # impuestos & impuesto TEXTOS
            # ----------------------------
            for line in self.mapped('tax_line_ids'):
                tipo_impuesto = line.name[0:3]
                if tipo_impuesto != "IVA":
                    # -------------------------------------------
                    # impuesto XML ESTRUCTURA
                    # indicar la subRoot, en este caso  impuesto
                    # -------------------------------------------
                    impuesto = ET.SubElement(impuestos, "impuesto")
                    # --------------------------------
                    # impuesto TEXTOS
                    # listar subElementos de impuesto
                    # --------------------------------
                    codigo = ET.SubElement(impuesto, "codigo")
                    codigoRetencion = ET.SubElement(impuesto, "codigoRetencion")
                    baseImponible = ET.SubElement(impuesto, "baseImponible")
                    porcentajeRetener = ET.SubElement(impuesto, "porcentajeRetener")
                    valorRetenido = ET.SubElement(impuesto, "valorRetenido")
                    codDocSustento = ET.SubElement(impuesto, "codDocSustento")
                    numDocSustento = ET.SubElement(impuesto, "numDocSustento")
                    fechaEmisionDocSustento = ET.SubElement(impuesto, "fechaEmisionDocSustento")

                    codigo.text = str(line.codigo_tabla_19)
                    codigoRetencion.text = str(line.codigo_tabla_20).replace(' ', '')
                    baseImponible.text = str('{:.2f}'.format(line.base_imponible))
                    porcentajeRetener.text = str('{:.2f}'.format(line.porcentaje_retencion))
                    valorRetenido.text = str('{:.2f}'.format(abs(line.amount)))
                    codDocSustento.text = str(self.tipo_comprobante)
                    numDocSustento.text = self.reference.split("-")[0] + self.reference.split("-")[1] + \
                                          self.reference.split("-")[2]
                    fechaEmisionDocSustento.text = Fecha
            # ----------------------
            # campoAdicional  TEXTO
            # ----------------------
            # ::::::::::::::::::::::::::::::::::::::::::::::
            if self.partner_id.email:
                campoAdicional = ET.SubElement(infoAdicional, "campoAdicional")
                campoAdicional.set('nombre', 'Email')
                campoAdicional.text = self.partner_id.email
            # ::::::::::::::::::::::::::::::::::::::::::::::
            # ---------------------------
            # GENERACION DEL ARCHIVO XML
            # ---------------------------
            tree = ET.ElementTree(comprobanteRetencion)
            root = tree.getroot()
            tree.write(nombre_archivo, encoding='utf-8', xml_declaration=True)
            # -----------------------------------------
            # SE GUARDA EN LA BASE DE DATOS LA NUEVA
            # SECUENCIA retencion_sequence_number_next
            # -----------------------------------------
            vals = {'retencion_sequence_number_next': retencion_sequence_number_next + sequence.number_increment}
            journal.write(vals)
            # ------------------------------
            # SE GUARDA EN LA BASE DE DATOS
            # doc_electronico_no
            # doc_electronico_fecha
            # doc_electronico_xml
            # bool_doc_enviado
            # bool_onOff_generar
            # -------------------------------
            vals = {
                'doc_electronico_no': referencia,
                'doc_electronico_fecha': fecha_documento_electronico,
                'doc_electronico_no_autorizacion': clave_autorizacion,
                'doc_electronico_xml': doc_electronico_xml,
                'bool_doc_enviado': True,
                'bool_onOff_generar': False
            }
            formulario = self.env['account.invoice'].search([('id', '=', self.id)])
            formulario.write(vals)

