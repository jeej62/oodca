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

# noinspection PyUnresolvedReferences,PyProtectedMember
from odoo import api, fields, models, _
from datetime import datetime, date

# noinspection PyUnresolvedReferences
from odoo.exceptions import (
    AccessDenied, RedirectWarning, MissingError, except_orm,
    AccessError, DeferredException, ValidationError, Warning
    as UserError
)
# noinspection PyUnresolvedReferences
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, pycompat, date_utils


# ----------------------------------------------------------------------------------------------------------------------
#   O   OOOOO OOOOO OOOOO O   O O   O OOOOO     OOO  O   O O   O OOOOO  OOO  OOOOO OOOOO
#  O O  O     O     O   O O   O OO  O   O        O   OO  O O   O O   O   O   O     O
# O   O O     O     O   O O   O O O O   O        O   O O O O   O O   O   O   O     OOO
# OOOOO O     O     O   O O   O O  OO   O        O   O  OO  O O  O   O   O   O     O
# O   O OOOOO OOOOO OOOOO OOOOO O   O   O       OOO  O   O   O   OOOOO  OOO  OOOOO OOOOO
# ----------------------------------------------------------------------------------------------------------------------
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    # ---------------------
    # DEFINICION DE CAMPOS
    # ---------------------
    secuencia_emision = fields.Char(
        string='No Reversión',
        readonly=True,
        help='Número secuencial del documento de compra'
    )
    numero_identidad = fields.Char(
        string='No ID',
        size=13,
        required=False,
        default='0000000000',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=True,
        help='Número de Identificación (cédula, RUC o pasaporte)'
    )
    numero_autorizacion = fields.Char(
        string='No Autorización',
        size=49,
        required=True,
        default='0000000000',
        readonly=True,
        copy=True,
        states={'draft': [('readonly', False)]},
        help='No. de autorización del Documento de Compra (10 or 49 dígitos)'
    )
    codigo_sustento_descripcion = fields.Char(string='Descripción del Código de Sustento')
    codigo_sustento = fields.Selection(
        [
            ('00', 'Casos especiales cuyo sustento no aplica en las opciones anteriores'),
            ('01', 'Crédito Tributario para declaración de IVA (b&s distintos de inventarios y activos fijos)'),
            ('02', 'Costo o Gasto para declaración de IR (b&s distintos de inventarios y activos fijos)'),
            ('03', 'Activo Fijo - Crédito Tributario para declaración de IVA'),
            ('04', 'Activo Fijo - Costo o Gasto para declaración de IR'),
            ('05', 'Liquidación Gastos de Viaje, hospedaje y alimentación (a nombre de empleados y no de la empresa)'),
            ('06', 'Inventario - Crédito Tributario para declaración de IVA'),
            ('07', 'Inventario - Costo o Gasto para declaración de IR'),
            ('08', 'Valor pagado para solicitar Reembolso de Gasto (intermediario)'),
            ('09', 'Reembolso por Siniestros'),
            ('10', 'Distribución de Dividendos, Beneficios o Utilidades'),
            ('11', 'Convenios de débito o recaudación para IFI´s'),
            ('12', 'Impuestos y retenciones presuntivos'),
            ('13', 'Valores reconocidos por entidades del sector público a favor de sujetos pasivos'),
            ('14', 'Valores facturados por socios a operadoras de transporte (no constituyen gasto de la operadora))')
        ],
        string='Código de Sustento',
        required=True,
        default='01',
        readonly=True,
        copy=True,
        states={'draft': [('readonly', False)]},
        help='Código de Sustento del Documento de Compra'
    )
    tipo_comprobante_descripcion = fields.Char(string='Descripción del Tipo Comprobante')
    tipo_comprobante = fields.Selection(
        [
            ('01', 'Factura'),
            ('02', 'Nota de venta'),
            ('03', 'Liquidación de compra'),
            ('08', 'Boletos o entradas'),
            ('09', 'Tiquetes Máq.Regis.'),
            ('11', 'Pasajes áereos'),
            ('12', 'Documentos IFIS'),
            ('15', 'Comprobante Exterior'),
            ('16', 'FUE, DAU o DAV'),
            ('18', 'Documentos autorizados'),
            ('19', 'Comprobantes de Pago'),
            ('20', 'Documentos del Estado'),
            ('21', 'Carta de Porte Aéreo'),
            ('41', 'Comprobante reembolso'),
            ('45', 'Liquidación Seguros'),
        ],
        string='Tipo Comprobante',
        required=True,
        default='01',
        readonly=True,
        copy=True,
        states={'draft': [('readonly', False)]},
        help='Tipos de comprobantes autorizados'
    )
    metodo_pago_descripcion = fields.Char(string='Descripción de las Formas de Pago')
    metodo_pago = fields.Selection(
        [
            ('01', 'Sin Utilización del Sistema Financiero'),
            ('02', 'Cheque Propio'),
            ('03', 'Cheque Certificado'),
            ('04', 'Cheque de Gerencia'),
            ('05', 'Cheque del Exterior'),
            ('06', 'Débito de Cuenta'),
            ('07', 'Transferencia Propio Banco'),
            ('08', 'Transferencia Otro Banco Nacional'),
            ('09', 'Transferencia Banco Exterior'),
            ('10', 'Tarjeta de Crédito Nacional'),
            ('11', 'Tarjeta de Crédito Internacional'),
            ('12', 'Giro'),
            ('13', 'Depósito en Cuenta (Corriente / Ahorros'),
            ('14', 'Endoso de Inversión'),
            ('15', 'Compensación de Deudas'),
            ('16', 'Tarjeta de Débito'),
            ('17', 'Dinero Electrónico'),
            ('18', 'Tarjeta Prepago'),
            ('19', 'Tarjeta de Crédito'),
            ('20', 'Otros con Utilización del Sistema Financiero'),
            ('21', 'Endoso de Títulos')
        ],
        string='Formas de Pago',
        required=True,
        default='01',
        readonly=True,
        copy=True,
        states={'draft': [('readonly', False)]},
        help='Formas de Pago SRI TABLA 24'
    )
    # ------------------------------------------------
    # DEFINCION DE CAMPOS PIE DE DOCUMENTOS DE COMPRA
    # ------------------------------------------------
    subtotal_0 = fields.Monetary(string='Subtotal 0%', copy=True)
    subtotal_12 = fields.Monetary(string='Subtotal 12%', copy=True)
    subtotal_no_sujeto_iva = fields.Monetary(string='Subtotal No Sujeto IVA', copy=True)
    descuento = fields.Monetary(string='DESCUENTO', copy=True)
    ice = fields.Monetary(string='ICE', copy=True)
    irbpnr = fields.Monetary(string='IRBPNR', copy=True)
    iva_12 = fields.Monetary(string='IVA 12%', copy=True)
    propina = fields.Monetary(string='PROPINA', copy=True)
    valor_total = fields.Monetary(string='VALOR TOTAL', copy=True)
    total_retenciones = fields.Monetary(string='Total Retenciones', copy=True)
    # ----------------------------------------------------------
    # DEFINICION DE CAMPOS DOCUMENTOS ELECTRONICOS FV, NCV & CR
    # ----------------------------------------------------------
    doc_electronico_no = fields.Char(string='Documento No', store=True, copy=False, readonly=True)
    doc_electronico_fecha = fields.Date(string='Fecha Retención', store=True, copy=False, readonly=True)
    doc_electronico_xml = fields.Char(string='Documento XML', store=True, copy=False, readonly=True)
    doc_electronico_no_autorizacion = fields.Char(string='No Aut. SRI', copy=False, readonly=True)
    doc_electronico_fecha_autorizacion = fields.Char(string='Fecha Aut. SRI', copy=False, readonly=True)
    doc_electronico_tipo = fields.Char(string='Tipo Doc Electrónico', copy=True, readonly=True)
    retencion_tabla = fields.Text(string='Tabla Retenciones', copy=True)
    doc_electronico_no_anulacion = fields.Char(string='No Anulación Ret', copy=False)
    # ----------------------------------------------------------
    # DEFINICION DE CAMPOS DOCUMENTOS ELECTRONICOS FV, NCV & CR
    # ----------------------------------------------------------
    doc_electronico_no_lc = fields.Char(string='Documento No ', store=True, copy=False, readonly=True)
    doc_electronico_fecha_lc = fields.Date(string='Fecha Autorización ', store=True, copy=False, readonly=True)
    doc_electronico_xml_lc = fields.Char(string='Documento XML ', store=True, copy=False, readonly=True)
    doc_electronico_no_autorizacion_lc = fields.Char(string='No Aut. SRI ', copy=False, readonly=True)
    doc_electronico_fecha_autorizacion_lc = fields.Char(string='Fecha Aut. SRI ', copy=False, readonly=True)
    # ----------------------------------
    # DEFINICION DE CAMPOS many2one
    # ----------------------------------
    select_numDiarioModificado_compras = fields.Many2one(
        'account.invoice',
        string='Documento de Origen',
        domain="[('partner_id', '=', partner_id), ('type', '=', 'in_invoice')]",
        help='Número de Diario Modificado solo en Notas de Crédito de Compras',
        store=True,
        compute='name_get'
    )
    select_numDiarioModificado_ventas = fields.Many2one(
        'account.invoice',
        string='Documento de Origen.',
        domain="[('partner_id', '=', partner_id), ('type', '=', 'out_invoice')]",
        help='Número de Diario Modificado solo en Notas de Crédito de Ventas',
        store=True,
        compute='name_get'
    )
    # --------------------------------
    # DEFINICION DE OTROS CAMPOS CHAR
    # --------------------------------
    tipo_documento_tributario = fields.Char(
        string='Tipo Documento Tributario',
        readonly=False,
        copy=True,
        help='Tipo de documento tributario',
        default="TIPO DE DOCUMENTO TRIBUTARIO",
    )
    char_numDocModificado = fields.Char(
        string='No Documento Origen',
        readonly=False,
        copy=True,
        store=True,
        help='Número de Documento de Origen en Notas de Crédito'
    )
    char_docModificado_fecha = fields.Char(
        string='Fecha Doc.Origen',
        readonly=False,
        copy=True,
        store=True,
        help='Fecha del Documento de Origen en Notas de Crédito'
    )
    char_usuarioNombreComercial = fields.Char(
        string='Usuario nombre corto',
        readonly=True,
        copy=True,
        help='Nombre corto del usuario'
    )
    tipo_formulario = fields.Char(
        string='Tipo',
        copy=True,
        help='Abreviación del documento tributario',
    )
    establecimiento_venta = fields.Char(
        string='Agencia',
        copy=True,
        help='Punto de emisión y venta',
    )

    valor_total_letras = fields.Char(
        string='Valor Total',
        copy=True,
        help='Valor total en letras',
    )

    # --------------------------
    # DEFINICION DE CAMPOS BOOL
    # --------------------------
    bool_doc_enviado = fields.Boolean(
        string='Documento enviado',
        default=False,
        copy=False,
        help='Comprobante de Retención GENERADO'
    )
    # bool_doc_anulado = fields.Boolean(
    #    string='Documento Anulado',
    #    default=False,
    #    copy=False,
    #    help='Documento de compra ANULADO'
    # )
    bool_doc_revertido = fields.Boolean(
        string='Documento Revertido',
        default=False,
        copy=False,
        help='Documento de compra REVERTIDO'
    )
    bool_confirm_sri = fields.Boolean(
        string='Confirmación de anulación del CRF en el SRI',
        default=False,
        copy=False,
        help='Solicitud de Anulación RECIBIDA desde el SRI'
    )
    bool_validar = fields.Boolean(
        string='Validación de procesos de compra',
        default=False,
        copy=False,
        help='Si todos los procesos de compra están realizados, entonces CHEQUEADO'
    )
    bool_onOff_generar = fields.Boolean(
        string='Semáforo de generación de documentos electrónicos',
        default=True,
        copy=False,
        help='Se prende o apaga a necesidad de las condiciones del botón'
    )
    bool_onOff_no_anulacion = fields.Boolean(
        string='Semáforo del numero de validación de documentos electrónicos',
        default=True,
        copy=False,
        help='Se prende o apaga a necesidad de las condiciones del botón'
    )
    # ----------------------------------
    # MODIFICACION DE CAMPOS EXISTENTES
    # ----------------------------------
    reference = fields.Char(
        default='000-000-000000000',
        copy=True,
        size=21
    )
    name = fields.Char(
        string='Reference/Description',
        index=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=True,
        help='The name that will be used on account move lines'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        change_default=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='always',
        ondelete='restrict',
        help="You can find a contact by its Name, TIN, Email or Internal Reference."
    )

    # ------------------
    # CONTROL DE ESTADO
    # ------------------
    ultimo_estado = fields.Char(
        string='Ultimo Estado',
        compute='_control_flujo',
        store=True,
        copy=True,
        help='Mantiene el último estado de la transacción. Se usa para verificar cambios de estado'
    )

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def action_invoice_open(self):
        # ---------------------------------------------------------------------------
        # AL VALIDAR UN FORMULARIO DE LA CLASE AccountInvoice, ANTES QUE NADA
        # SE ACTUALIZA EL NO DE REFERENCIA self.reference PARA doc_electronico_tipo:
        # FACTURA
        # NOTA DE CREDITO
        # LIQUIDACION DE COMPRA
        # ---------------------------------------------------------------------------
        formulario_sequence_number_next = {}

        det = self.doc_electronico_tipo
        if self.type == 'in_invoice' and self.tipo_comprobante == '03':
            det = 'LIQUIDACION DE COMPRA'

        if det == 'FACTURA' or det == 'NOTA DE CREDITO' or det == 'LIQUIDACION DE COMPRA':
            journal = self.journal_id

            if det == 'FACTURA':
                formulario_sequence_number_next = journal.factura_sequence_number_next
            if det == 'NOTA DE CREDITO':
                formulario_sequence_number_next = journal.notaCredito_sequence_number_next
            if det == 'LIQUIDACION DE COMPRA':
                formulario_sequence_number_next = journal.liquidacionCompra_sequence_number_next

            numero_secuencial = "0" * (9 - len(str(formulario_sequence_number_next))) + str(
                formulario_sequence_number_next)

            establecimiento = journal.establecimiento
            punto_emision = journal.punto_emision

            referencia = establecimiento + "-" + punto_emision + "-" + numero_secuencial
            self.reference = referencia
        # ---------------------------------------------------------------------------
        # SE MANTIENE LA ESTRUCTURA DEL PROGRAMA DE ODOO:
        # tipo:     @api.multi
        # FUNCION:  def action_invoice_open(self)
        # ORIGEN:   /addons/account/models/account_invoice.py
        # CLASS:    class AccountInvoice(models.Model):
        # ---------------------------------------------------------------------------
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: not inv.partner_id):
            raise UserError(_("The field Vendor is required, please complete it to validate the Vendor Bill."))
        if to_open_invoices.filtered(lambda inv: inv.state != 'draft'):
            raise UserError(_("Invoice must be in draft state in order to validate it."))
        if to_open_invoices.filtered(
                lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
            raise UserError(_(
                "You cannot validate an invoice with a negative total amount. You should create a credit note instead."))
        if to_open_invoices.filtered(lambda inv: not inv.account_id):
            raise UserError(
                _('No account was found to create the invoice, be sure you have installed a chart of account.'))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        return to_open_invoices.invoice_validate()

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.one
    @api.depends('state', 'tipo_comprobante')
    def _control_flujo(self):
        # ------------------------------------------------
        # CONTROL DE FLUJOS DE ESTADO DE DOCUMENTOS state
        # ------------------------------------------------
        # -----------------------------------------------------------
        # CORRIGE EL numero_identidad en la NOTA DE CREDITO GENERADA
        # -----------------------------------------------------------
        self._compute_partner_id()
        # --------------------
        # FACTURA DE VENTA FV
        # --------------------
        if self.type == "out_invoice":
            self._zcalcular_talonario()
            self.tipo_documento_tributario = "FACTURA DE VENTA"
            self.tipo_formulario = "FACTURA"
            self.doc_electronico_tipo = "FACTURA"

            # ----------------------------------------------
            # GENERACION DE LA FACTURA DE VENTA ELECTRONICA
            # ----------------------------------------------
            if self.state == "open":
                if not self.doc_electronico_xml:
                    # journal = self.journal_id
                    self.archivo_factura_xml()
            # -------------------------------------------------------
            # CORRECCION DE CAMPOS char_numDocModificado & reference
            # -------------------------------------------------------
            if self.state == "draft":
                self.reference = "000-000-000000000"
                self.numero_autorizacion = "0000000000"
            # ------------------------------------------------------------
            # CORRECCION DE LA ref EN EL DIARIO CONTABLE account.move
            # ------------------------------------------------------------
            if self.state == "open":
                vals = {
                    'ref': self.reference,
                    'narration': self.name
                }
                move = self.env['account.move'].search([('id', '=', self.move_id.id)])
                move.write(vals)
            # -------------------------------------
            # VALIDACION TRIBUTARIA DEL FORMULARIO
            # -------------------------------------
            if self.state == "paid":
                if not self.bool_validar:
                    if self.doc_electronico_xml:
                        self.bool_validar = True
            vals = {
                'tipo_documento_tributario': self.tipo_documento_tributario,
                'tipo_formulario': self.tipo_formulario,
                'doc_electronico_tipo': self.doc_electronico_tipo,
                'bool_validar': self.bool_validar,
                'reference': self.reference,
                'numero_autorizacion': self.numero_autorizacion,
            }
            formulario = self.env['account.invoice'].search([('number', '=', self.number), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
            formulario.write(vals)
        # -----------------------------
        # NOTA DE CREDITO DE VENTA NCV
        # -----------------------------
        if self.type == "out_refund":
            self._zcalcular_talonario()
            if self.origin:
                self.tipo_documento_tributario = "NOTA DE CREDITO DE VENTA"
                self.tipo_formulario = "NOTA CREDITO"
                self.doc_electronico_tipo = "NOTA DE CREDITO"
                self.name = "DEVOLUCION"
                vals = {
                    'tipo_documento_tributario': self.tipo_documento_tributario,
                    'tipo_formulario': self.tipo_formulario,
                    'doc_electronico_tipo': self.doc_electronico_tipo,
                    'name': self.name,
                    'payment_term_id': 1,
                }
                formulario = self.env['account.invoice'].search([('origin', '=', self.origin), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
                formulario.write(vals)
            else:
                self.tipo_documento_tributario = "COMPROBANTE DE RETENCION DE VENTA"
                self.tipo_formulario = "RETENCION"
                self.doc_electronico_tipo = "RETENCION DE VENTA"
                self.name = "RETENCION"
                vals = {
                    'tipo_documento_tributario': self.tipo_documento_tributario,
                    'tipo_formulario': self.tipo_formulario,
                    'doc_electronico_tipo': self.doc_electronico_tipo,
                    'name': self.name,
                    'payment_term_id': 1,
                }
                formulario = self.env['account.invoice'].search([('number', '=', self.number), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
                formulario.write(vals)
            # -------------------------------------------------------
            # CORRECCION DE CAMPOS char_numDocModificado & reference
            # -------------------------------------------------------
            if self.state == "draft" and self.origin is not False:
                formulario = self.env['account.invoice'].search(
                    [('type', '=', 'out_invoice'), ('number', '=', self.origin)])
                Fecha_str = str(formulario.date_invoice)
                Fecha_obj = datetime.strptime(Fecha_str, '%Y-%m-%d').date()
                Fecha = Fecha_obj.strftime("%d/%m/%Y")
                self.char_docModificado_fecha = Fecha
                self.char_numDocModificado = self.reference
                self.reference = "000-000-000000000"
                vals = {
                    'char_docModificado_fecha': self.char_docModificado_fecha,
                    'char_numDocModificado': self.char_numDocModificado,
                    'reference': self.reference,
                }
                formulario = self.env['account.invoice'].search([('origin', '=', self.origin)])
                formulario.write(vals)
            # -------------------------------------------------------
            # GENERACION DE LA NOTA DE CREDITO DE VENTA ELECTRONICA
            # -------------------------------------------------------
            if self.state == "open" and self.origin is not False:
                if not self.doc_electronico_xml:
                    self.archivo_notaCredito_xml()
            # ------------------------------------------------------------
            # CORRECCION DE LA ref EN EL DIARIO CONTABLE account.move
            # ------------------------------------------------------------
            if self.state == "open":
                vals = {
                    'ref': self.reference,
                    'narration': self.name
                }
                move = self.env['account.move'].search([('id', '=', self.move_id.id)])
                move.write(vals)
            # -------------------------------------
            # VALIDACION TRIBUTARIA DEL FORMULARIO
            # -------------------------------------
            if self.state == "paid":
                if not self.bool_validar:
                    if self.doc_electronico_xml is not False or self.select_numDiarioModificado_ventas is not False:
                        self.bool_validar = True
                    else:
                        self.bool_validar = False
                    vals = {
                        'bool_validar': self.bool_validar,
                    }
                    formulario = self.env['account.invoice'].search([('number', '=', self.number), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
                    formulario.write(vals)
        # ------------------------
        # DOCUMENTOS DE COMPRA DC
        # ------------------------
        if self.type == "in_invoice":
            self._zcalcular_talonario()
            self.tipo_documento_tributario = "DOCUMENTO DE COMPRA"
            self.doc_electronico_tipo = "COMPROBANTE DE RETENCION"
            self.tipo_formulario = "FACTURA"
            self.establecimiento_venta = self.journal_id.establecimiento + "-" + self.journal_id.punto_emision
            # ------------------------------------------------------------------------------------------------
            # MODIFICACION DEL reference EN CASO DE QUE HAYA SIDO MODIFICADO POR EL PROCESO DE REVERSION PARA
            # type = in_invoice & state = draft
            # ------------------------------------------------------------------------------------------------
            if self.state == "draft" and self.tipo_comprobante == "03":
                self.reference = "000-000-000000000"
                self.numero_autorizacion = "0000000000"
            if self.reference:
                self.reference = self.reference[0:17]
            # ----------------------------------------
            # GENERACION DEL COMPROBANTE DE RETENCION
            # ----------------------------------------
            if self.state == "open":
                if self.tipo_comprobante == "03":  # LIQUIDACION DE COMPRA
                    if not self.doc_electronico_xml_lc:
                        self.archivo_liquidacionCompra_xml()
                        self._zcalcular_talonario()
                    if not self.doc_electronico_xml:
                        self.archivo_retencion_xml()
                if not self.doc_electronico_xml:  # OTROS DOCUMENTOS DE COMPRA
                    self.archivo_retencion_xml()
            # -------------------------------------
            # VALIDACION TRIBUTARIA DEL FORMULARIO
            # -------------------------------------
            # ------------------------------------------------------------------------
            # PROCESO DE CAMBIO EN EL bool_validar EN EL DOCUMENTO DE COMPRA GENERADO
            # ------------------------------------------------------------------------
            if self.state == "paid":
                if self.bool_validar is False:
                    if self.bool_doc_revertido is True:
                        self.bool_onOff_no_anulacion = False
                    else:
                        if self.bool_doc_enviado is True:
                            self.bool_validar = True
            vals = {
                'tipo_documento_tributario': self.tipo_documento_tributario,
                'doc_electronico_tipo': self.doc_electronico_tipo,
                'tipo_formulario': self.tipo_formulario,
                'establecimiento_venta': self.establecimiento_venta,
                'bool_onOff_no_anulacion': self.bool_onOff_no_anulacion,
                'bool_validar': self.bool_validar,
                'numero_autorizacion': self.numero_autorizacion,
                'reference': self.reference
            }
            formulario = self.env['account.invoice'].search([('number', '=', self.number), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
            formulario.write(vals)
        # -----------------------------------------------------------------
        # REVERSION DE DOCUMENTO DE COMPRA & NOTA DE CREDITO DE COMPRA NCC
        # -----------------------------------------------------------------
        if self.type == "in_refund":
            self._zcalcular_talonario()
            # ---------------------------------
            # REVERSION DE DOCUMENTO DE COMPRA
            # ---------------------------------
            if self.origin:
                self.tipo_documento_tributario = "REVERSION DE DOCUMENTO DE COMPRA"
                self.doc_electronico_tipo = "REVERSION DE COMPRA"
                self.tipo_formulario = "REVERSION"
                self.name = "REVERSION"
                vals = {
                    'tipo_documento_tributario': self.tipo_documento_tributario,
                    'doc_electronico_tipo': self.doc_electronico_tipo,
                    'tipo_formulario': self.tipo_formulario,
                    'name': self.name,
                    'payment_term_id': 1,
                }
                formulario = self.env['account.invoice'].search([('origin', '=', self.origin), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
                formulario.write(vals)
                # -------------------------------------------------------
                # REVERSION DE DOCUMENTO DE COMPRA draft
                # -------------------------------------------------------
                if self.state == "draft":
                    self.char_numDocModificado = self.reference
                    origen = self.env['account.invoice'].search([('number', '=', self.origin)])
                    self.reference = origen.reference
                    self.numero_autorizacion = origen.numero_autorizacion
                    Fecha_str = str(origen.date_invoice)
                    Fecha_obj = datetime.strptime(Fecha_str, '%Y-%m-%d').date()
                    Fecha = Fecha_obj.strftime("%d/%m/%Y")
                    self.char_docModificado_fecha = Fecha
                    self.name = "REVERSION"
                    vals = {
                        'char_numDocModificado': self.char_numDocModificado,
                        'reference': self.reference,
                        'numero_autorizacion': self.numero_autorizacion,
                        'char_docModificado_fecha': self.char_docModificado_fecha,
                        'name': self.name,
                        'payment_term_id': 1,
                    }
                    formulario = self.env['account.invoice'].search(
                        [('origin', '=', self.origin), ('type', '=', self.type),
                         ('partner_id', '=', self.partner_id.id)])
                    formulario.write(vals)
                # --------------------------------------
                # REVERSION DE DOCUMENTO DE COMPRA open
                # --------------------------------------
                if self.state == "open":
                    # --------------------------------------
                    # CORRECCION EN EL DIARIO CONTABLE move
                    # --------------------------------------
                    vals = {
                        'ref': self.reference,
                        'narration': self.name,
                        'numero_autorizacion': self.numero_autorizacion
                    }
                    move = self.env['account.move'].search([('id', '=', self.move_id.id)])
                    move.write(vals)
                    self.validar_NCC()
                # --------------------------------------
                # REVERSION DE DOCUMENTO DE COMPRA paid
                # --------------------------------------
                if self.state == "paid":
                    # -----------------------------------------------------------------
                    # PROCESO DE VALIDACION DE LA NOTA DE CREDITO DE COMPRA
                    # -----------------------------------------------------------------
                    self.validar_NCC()
                vals = {
                    'tipo_documento_tributario': self.tipo_documento_tributario,
                    'doc_electronico_tipo': self.doc_electronico_tipo,
                    'tipo_formulario': self.tipo_formulario,
                    'numero_autorizacion': self.numero_autorizacion,
                    'bool_onOff_no_anulacion': self.bool_onOff_no_anulacion,
                    'bool_validar': self.bool_validar,
                    'name': self.name,
                    'reference': self.reference
                }
                formulario = self.env['account.invoice'].search([('number', '=', self.number), ('type', '=', self.type)])
                formulario.write(vals)
            # --------------------------
            # NOTA DE CREDITO DE COMPRA
            # --------------------------
            else:
                self.tipo_documento_tributario = "NOTA DE CREDITO DE COMPRA"
                self.doc_electronico_tipo = "NOTA DE CREDITO DE COMPRA"
                self.tipo_formulario = "NOTA CREDITO"
                self.name = "DEVOLUCION"
                self.bool_validar = True
                vals = {
                    'tipo_documento_tributario': self.tipo_documento_tributario,
                    'doc_electronico_tipo': self.doc_electronico_tipo,
                    'tipo_formulario': self.tipo_formulario,
                    'bool_onOff_no_anulacion': self.bool_onOff_no_anulacion,
                    'bool_validar': self.bool_validar,
                    'name': self.name,
                    'reference': self.reference
                }
                formulario = self.env['account.invoice'].search([('number', '=', self.number), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
                formulario.write(vals)
        # -----------------------------------------------------------------
        # CORRIGE EL numero_identidad EN EL FORMULARIO
        # -----------------------------------------------------------------
        self._buscar_no_identidad()
        # -----------------------------------------------------------------
        # EN depends SOLO GRABA LOS CAMPOS compute CON ATRIBUTO store=True
        # SE DEBE USAR write PARA MANTENER LOS CAMBIOS
        # -----------------------------------------------------------------
        self.establecimiento_venta = self.journal_id.establecimiento + "-" + self.journal_id.punto_emision
        # ------------------------
        # CONTROL DE ESTADO state
        # ------------------------
        self.ultimo_estado = self.state

        # ----------------------------------------------------------------
        # VALIDACION DE reference, numero_autorizacion & numero_identidad
        # ----------------------------------------------------------------
        if self.state == 'open':
            # ---------------------------
            # VALIDACION DE LA reference
            # ---------------------------
            if self.reference == '000-000-000000000':
                raise UserError(_("Número de referencia ERRONEO.\n\nIngrese su valor correcto. Actual = " + self.reference))

            establecimiento = self.reference.split('-')[0]
            punto_emision = self.reference.split('-')[1]
            secuencial = self.reference.split('-')[2]

            if establecimiento in '0000000000':
                raise UserError(_("Número de Establecimiento ERRONEO.\n\nIngrese su valor correcto. Actual = " + establecimiento))
            if punto_emision in '0000000000':
                raise UserError(_("Número del Punto de Emisión ERRONEO.\n\nIngrese su valor correcto. Actual = " + punto_emision))
            if secuencial in '0000000000':
                raise UserError(_("Número del Secuencial ERRONEO.\n\nIngrese su valor correcto. Actual = " + secuencial))
            # -----------------------------------
            # VALIDACION DEL numero_autorizacion
            # -----------------------------------
            if self.numero_autorizacion in '00000000000000000000000000000000000000000000000000':
                raise UserError(_("Número de Autorización ERRONEO.\n\nIngrese su valor correcto. Actual = " + self.numero_autorizacion))

            try:
                print(int(self.numero_autorizacion))
            except Exception as e:
                raise UserError("Número de Autorización ERRONEO. NO PUEDE CONTENER LETRAS.\n\nIngrese su valor correcto. \n\n[" + str(e).upper() + "]")

            longitud_numero_autorizacion = len(self.numero_autorizacion)
            if longitud_numero_autorizacion != 10 and longitud_numero_autorizacion != 49:
                raise UserError(_("Longitud del Número de Autorización ERRONEO.\n\nIngrese su longitud correcta 10 o 49. Actual = " + str(longitud_numero_autorizacion)))

            if longitud_numero_autorizacion == 49:
                # ----------------------------------------------------
                # SE INGRESA EL FACTOR DE CHEQUEO PONDERADO MODULO 11
                # ----------------------------------------------------------------------------
                factor_chequeo_ponderado = "765432765432765432765432765432765432765432765432"
                # ----------------------------------------------------------------------------
                # SE DEFINE EL digitoVerificador
                # ----------------------------------------------------------------------------
                clave_autorizacion = self.numero_autorizacion
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
                ultimo_digito = int(clave_autorizacion[48])

                if digitoVerificador != ultimo_digito:
                    raise UserError(_("Dígito verificador del Número de Autorización ERRONEO.\n"
                                      "El dígito verificador es el último número de la serie\n\n"
                                      "Ingrese su valor correcto. Actual: " + str(ultimo_digito) +
                                      " Correcto: " + str(digitoVerificador)))

            # --------------------------------
            # VALIDACION DEL numero_identidad
            # --------------------------------
            if self.numero_identidad == '0000000000':
                self._compute_partner_id()

            # -------------------------------------------------
            # VALIDACION DEL select_numDiarioModificado_ventas
            # -------------------------------------------------
            if not self.select_numDiarioModificado_ventas and self.tipo_documento_tributario == "COMPROBANTE DE RETENCION DE VENTA":
                raise UserError("Documento de Origen VACIO.\n\nEscoja su valor correcto.")

            # -------------------------------------------------
            # VALIDACION DEL select_numDiarioModificado_compras
            # -------------------------------------------------
            if not self.select_numDiarioModificado_compras and self.tipo_documento_tributario == "NOTA DE CREDITO DE COMPRA":
                raise UserError("Documento de Origen VACIO.\n\nEscoja su valor correcto.")




    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.onchange('invoice_line_ids', 'tipo_comprobante', 'metodo_pago')
    def _zcalcular_talonario(self):
        if self.state == 'draft':
            # -------------------------------------------------------------------
            # CALCULA LOS VALORES DEL TALONARIO DEL FORMULARIO DE COMPRA Y VENTA
            # -------------------------------------------------------------------
            # ----------------------------------------------------------------------------------------
            # ELIMINA EL CODIGO internal_reference Ejm: [ST-GV] DE LA DESCRIPCION EN invoice_line_ids
            # DE TODOS LOS FORMULARIOS DE COMPRAS Y VENTAS
            # ------------------------------------------------------------------
            reference_description = ""
            self.propina = 0.00
            for line in self.mapped('invoice_line_ids'):
                # ---------------------------------------------------------------
                # DEFINE LA INFORMACION DEL Reference/Description DEL FORMULARIO
                # ---------------------------------------------------------------
                name = line.name  # name DESCRIPCION DEL PRODUCTO EN invoice_line_ids
                if str.__contains__(name, "[") or str.__contains__(name, "]"):
                    bloque_1 = name.split("[")[1]
                    bloque_2 = bloque_1.split("]")[0]
                    bloque_extraido = "[" + bloque_2 + "]"
                    line.name = name.replace(bloque_extraido, "")
                reference_description = reference_description + "/" + line.name
                # ---------------------------------------------------------------
                # CALCULA LAS PROPINAS
                # ---------------------------------------------------------------
                if str.__contains__(line.name, "PROPINA"):
                    self.propina = self.propina + line.price_subtotal

            # -----------------------------------------------------
            # INSERTA EL CAMPO name DE LOS SIGUIENTES FORMULARIOS:
            # DOCUMENTOS DE COMPRA
            # FACTURAS DE VENTA
            # ------------------------------------------------------------------
            if self.type == "in_invoice" or self.type == "out_invoice":
                if not self.name or self.name == "" or str.__contains__(self.name, "/"):
                    self.name = reference_description
            # ------------------------------------------------------------------
            # ELIMINACION DE LOS IMPUESTOS RIR Y RIV EN EL invoice_line_tax_ids
            # DE LAS NOTAS DE CREDITO DE COMPRA
            # ------------------------------------------------------------------
            if self.type == "in_refund" and self.origin is False:
                for line in self.mapped('invoice_line_ids'):
                    tax_ids = []  # LOS IDS DE IMPUESTOS ESTAN VACIOS
                    taxes = line.invoice_line_tax_ids
                    for tax in taxes:
                        if str.__contains__(tax.name, "RIR") or str.__contains__(tax.name, "RIV"):
                            tax_ids = tax_ids  # SE QUEDA IGUAL
                        else:
                            tax_ids.append(tax.id)  # SE AÑADE EL IMPUESTO A LA LISTA tax_ids
                    line.invoice_line_tax_ids = [(6, 0, tax_ids)]  # SE REEMPLAZA LA LISTA invoice_line_tax_ids
                    # CON LA NUEVA LISTA tax_ids
            # --------------------------------------------------------------
            # ELIMINACION DE TODOS LOS IMPUESTOS EN EL invoice_line_tax_ids
            # DE LOS COMPROBANTES DE RETENCION DE VENTA
            # --------------------------------------------------------------
            if self.type == "out_refund" and self.origin is False:
                for line in self.mapped('invoice_line_ids'):
                    tax_ids = []  # LOS IDS DE IMPUESTOS ESTAN VACIOS
                    line.invoice_line_tax_ids = [(6, 0, tax_ids)]  # SE REEMPLAZA LA LISTA invoice_line_tax_ids
                    # CON LA LISTA VACIA tax_ids
            # --------------------------------------------------------------
            # CONTROL DE INGRESO AL CALCULO DEL PIE DEL DOCUMENTO DE COMPRA
            # --------------------------------------------------------------
            if self.partner_id.name:
                # --------------
                # DECLARACIONES
                # --------------
                linea0 = {}
                linea1 = {}
                linea2 = {}
                linea3 = {}
                linea4 = {}
                linea5 = {}
                linea6 = {}
                linea7 = {}
                impuesto = {}
                self.subtotal_0 = 0.00
                self.subtotal_12 = 0.00
                self.subtotal_no_sujeto_iva = 0.00
                self.descuento = 0.00
                self.ice = 0.00
                self.irbpnr = 0.00
                self.iva_12 = 0.00
                self.valor_total = 0.00
                self.total_retenciones = 0.00
                # ---------------------------------------------
                # SE DETERMINA EL tipo_comprobante_descripcion
                # ---------------------------------------------
                tipo_comprobante = ""
                lista_tipo_comprobante = self._fields['tipo_comprobante'].selection
                for campos in lista_tipo_comprobante:
                    if campos[0] == self.tipo_comprobante:
                        tipo_comprobante = campos[1].upper()
                self.tipo_comprobante_descripcion = tipo_comprobante
                # ----------------------------------------
                # SE DETERMINA EL metodo_pago_descripcion
                # ----------------------------------------
                metodo_pago = ""
                lista_metodo_pago = self._fields['metodo_pago'].selection
                for campos in lista_metodo_pago:
                    if campos[0] == self.metodo_pago:
                        metodo_pago = campos[1].upper()
                self.metodo_pago_descripcion = metodo_pago
                # --------------------------------------------
                # SE DETERMINA EL codigo_sustento_descripcion
                # --------------------------------------------
                codigo_sustento = ""
                lista_codigo_sustento = self._fields['codigo_sustento'].selection
                for campos in lista_codigo_sustento:
                    if campos[0] == self.codigo_sustento:
                        codigo_sustento = campos[1].upper()
                self.codigo_sustento_descripcion = codigo_sustento

                if self.type == "in_invoice":
                    #         SOLO PARA DOCUMENTOS DE COMPRA
                    #         ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
                    #                                         Fecha       Periodo               Base             Porcentaje        Valor
                    #         Comprobante      Número         Emisión     Fiscal           Imponible  Impuesto     Retenido     Retenido
                    #         ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
                    #         FACTURA      001-001-000000001  16/08/2019  08/2019      91,321,133.33   731 IVA       100.00 3,333,333.33
                    #         0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345
                    #                   1         2         3         4         5         6         7         8         9        10
                    #         Comprobante = 11 espacios + 2 espacios
                    #         Número      = 17 espacios + 2 espacios
                    #         Fecha       = 10 espacios + 2 espacios
                    #         Periodo     =  9 espacios + 2 espacios
                    #         Base        = 13 espacios + 2 espacios
                    #         Impuesto    = 12 espacios + 2 espacios
                    #         % Retenido  =  6 espacios + 2 espacios
                    #         Valor       = 13 espacios
                    #         ––––––––––––––––––––––––––––––––––––––
                    #         TOTAL.      = 91 espacios + 14 espacios = 105
                    #
                    linea0 = '––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––\n'
                    linea1 = '                                Fecha       Periodo               Base             Porcentaje        Valor\n'
                    linea2 = 'Comprobante      Número         Emisión     Fiscal           Imponible  Impuesto     Retenido     Retenido\n'
                    linea3 = '––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––\n'
                    linea4 = ''
                    linea5 = '––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––\n'
                    linea6 = '                                                                               TOTAL RETENIDO'
                    linea7 = '––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––\n'
                for line in self.mapped('tax_line_ids'):
                    # --------------------------------------------------------------------------------------
                    # TABLA: account_invoice_tax
                    # Se calculan los valores de los campos añadidos en tax_line_ids de account.invoice.tax
                    # porcentaje_ret_iva       FORMATO XML COMPROBANTE RETENCIÓN  Cálculo baseImp
                    # porcentaje_retencion     FORMATO XML COMPROBANTE RETENCIÓN  porcentajeRetener
                    # base_imponible           FORMATO XML COMPROBANTE RETENCIÓN  baseImponible
                    # nombre_impuesto          TALONARIO
                    # codigo_tabla_20          FORMATO XML COMPROBANTE RETENCIÓN  codigoRetencion
                    # Ver: class AccountInvoiceTax(models.Model):
                    # --------------------------------------------------------------------------------------
                    tipo_impuesto = line.name[0:3]
                    line.porcentaje_ret_iva = 100.00
                    # -----------------------------------------------------------
                    # impuesto
                    # porcentaje_ret_iva
                    # porcentaje_retencion
                    # base_imponible
                    # A CADA tipo_impuesto LE CORRESPONDE UN impuesto ESPECIFICO
                    # -----------------------------------------------------------
                    if tipo_impuesto == "RIV":
                        line.porcentaje_ret_iva = float(line.name[15:17])
                        impuesto = "IVA"
                    if tipo_impuesto == "IVA":
                        impuesto = "IVA"
                    if tipo_impuesto == "RIR":
                        impuesto = "IR"
                    if tipo_impuesto == "ISD":
                        impuesto = "IR"
                    if tipo_impuesto == "IRX":
                        impuesto = "IR"
                    if tipo_impuesto == "ICE":
                        line.porcentaje_ret_iva = float(line.name[15:17])
                        impuesto = "ICE"
                    if tipo_impuesto == "IRB":
                        line.porcentaje_ret_iva = 0.02
                        impuesto = "IRBPNR"
                    line.porcentaje_retencion = float(line.name[3:6])
                    line.base_imponible = line.base * line.porcentaje_ret_iva / 100.00
                    # ----------------
                    # nombre_impuesto
                    # ----------------
                    if line.name[19:22] == " 001" or line.name[19:22] == " 002":
                        line.nombre_impuesto = impuesto
                    else:
                        line.nombre_impuesto = line.name[19:22] + " " + impuesto
                    if line.nombre_impuesto.split(" ")[0] == " ":
                        line.nombre_impuesto = line.nombre_impuesto.split(" ")[1] + line.nombre_impuesto.split(" ")[2]
                    # ------------------------------------
                    # codigo_tabla_19 TABLA 19 DEFINICION
                    # codigo_tabla_20 TABLA 20 DEFINICION
                    # ------------------------------------
                    #             '__3__3 _2_______81 ___4
                    #              RIR 10 ssHonorProC 303
                    #              RIR 08 ssComisIntC 304A
                    #              RIV100 bsComIVA12C 731
                    #              RIV 00 bsComIVA00C 002
                    #              RIV 00 bsComNoSujC 002
                    #              -----------------------
                    #              01234567890123456789012
                    # ------------------------------------
                    if tipo_impuesto == "RIR":
                        line.codigo_tabla_19 = str("1")
                        line.codigo_tabla_20 = line.name[19:23]
                    if tipo_impuesto == "RIV":
                        line.codigo_tabla_19 = str("2")
                        # ------------------
                        # TABLA 20 PARA RIV
                        # ------------------
                        if line.name[3:6] == " 10":
                            line.codigo_tabla_20 = "9"
                        if line.name[3:6] == " 20":
                            line.codigo_tabla_20 = "10"
                        if line.name[3:6] == " 30":
                            line.codigo_tabla_20 = "1"
                        if line.name[3:6] == " 70":
                            line.codigo_tabla_20 = "2"
                        if line.name[3:6] == "100":
                            line.codigo_tabla_20 = "3"
                        if line.name[3:6] == " 00" and line.name[15:17] == "00":
                            line.codigo_tabla_20 = "7"
                        if line.name[3:6] == " 00" and line.name[12:17] == "NoSuj":
                            line.codigo_tabla_20 = "8"
                    # ---------------------------------------------------------------------------
                    # EL TALONARIO DE RETENCIONES SE GENERA UNICAMENTE PARA DOCUMENTOS DE COMPRA
                    # in_invoice
                    # ---------------------------------------------------------------------------
                    if self.type == "in_invoice":
                        # -------------------------------------------
                        # TABLA: Retenciones - PESTAÑA "Retenciones"
                        # columnas DEFINCION
                        # -------------------------------------------------------------------------------------------
                        # Se determinan los valores de todas las columnas del talonario del comprobante de retención
                        # Comprobante   TALONARIO
                        # Número        FORMATO XML COMPROBANTE RETENCIÓN  numDocSustento
                        # Fecha         FORMATO XML COMPROBANTE RETENCIÓN  fechaEmisionDocSustento
                        # BaseImp       FORMATO XML COMPROBANTE RETENCIÓN  baseImponible
                        # Impuesto      TALONARIO
                        # Retenido      FORMATO XML COMPROBANTE RETENCIÓN  porcentajeRetener
                        # Valor         FORMATO XML COMPROBANTE RETENCIÓN  valorRetenido
                        # -------------------------------------------------------------------------------------------
                        Comprobante = self.tipo_comprobante_descripcion.split(" ")[0].upper()
                        # ----------------------------------------------------
                        # TABLA DE TALONARIO DE IMPUESTOS
                        # PARA TODAS LAS RETENCIONES EN LA TABLA DE IMPUESTOS
                        # ----------------------------------------------------
                        if tipo_impuesto != "IVA":
                            if self.date_invoice:
                                Fecha_str = str(self.date_invoice)
                                Fecha_obj = datetime.strptime(Fecha_str, '%Y-%m-%d').date()
                            else:
                                Fecha_str = str(datetime.now())
                                Fecha_obj = datetime.strptime(Fecha_str, '%Y-%m-%d %H:%M:%S.%f').date()
                            Fecha = Fecha_obj.strftime("%d/%m/%Y")
                            # -------------------
                            # COLUMNAS
                            # TABLA DE IMPUESTOS
                            # -------------------
                            Numero = self.reference.split("-")[0] + self.reference.split("-")[1] + \
                                     self.reference.split("-")[2]
                            BaseImp = str('${:0,.2f}'.format(line.base_imponible))
                            Impuesto = line.nombre_impuesto
                            Retenido = str('{:.0f} %'.format(line.porcentaje_retencion))
                            Valor = str('${:0,.2f}'.format(abs(line.amount)))
                            # -----------------------
                            # COLUMNAS
                            # UBICACION DE IMPRESION
                            # -----------------------
                            Comprobante = Comprobante + " " * (11 + 2 - len(Comprobante))
                            if self.reference is False:
                                Numero = "000000000000000"
                            else:
                                Numero = Numero + " " * (17 + 2 - len(Numero))
                            Fecha = str(Fecha) + " " * (10 + 2 - len(Fecha))
                            Periodo = str(Fecha[3:10]) + " " * (9 + 2 - len(Fecha[3:10]))
                            BaseImp = " " * (13 + 2 - len(BaseImp)) + BaseImp
                            Impuesto = "  " + Impuesto + " " * (12 + 1 - len(Impuesto))
                            Retenido = " " * (6 + 2 - len(Retenido)) + Retenido
                            Valor = " " * (13 - len(Valor)) + str(Valor)
                            # -----------------------------------
                            # LINEA DE IMPRESION DE LA RETENCION
                            # -----------------------------------
                            linea4 = linea4 + Comprobante + Numero + \
                                     Fecha + Periodo + BaseImp + Impuesto + Retenido + Valor + "\n"
                    if self.tipo_documento_tributario != 'COMPROBANTE DE RETENCION DE VENTA':
                        # --------------------------------------------------------
                        # SE CALCULAN LOS SIGUIENTES CAMPOS DEL PIE DE LA FACTURA
                        # subtotal_no_sujeto_iva
                        # subtotal_0
                        # subtotal_12
                        # ice
                        # irbpnr
                        # total_retenciones
                        # --------------------------------------------------------
                        if str.__contains__(line.name, "IVA 0"):
                            if str.__contains__(line.name, "noObj"):
                                self.subtotal_no_sujeto_iva += line.base
                            else:
                                self.subtotal_0 += line.base
                        if str.__contains__(line.name, "IVA 12"):
                            self.subtotal_12 += line.base
                            self.iva_12 += line.amount
                        if str.__contains__(line.name, "ICE"):
                            self.ice += line.base
                        if str.__contains__(line.name, "IRB"):
                            self.irbpnr += line.base
                        if str.__contains__(line.name, "RIR") or str.__contains__(line.name, "RIV"):
                            if str.__contains__(line.name, "RIV"):
                                self.total_retenciones += line.amount
                            if str.__contains__(line.name, "RIR"):
                                self.total_retenciones += line.amount
                # ------------------------------------------------------------------------------
                # SE CALCULAN OTROS CAMPOS DEL PIE DE LA FACTURA DEPENDIENTES DE LOS ANTERIORES
                # descuento
                # valor_total
                # ------------------------------------------------------------------------------
                for line in self.mapped('invoice_line_ids'):
                    self.descuento += line.price_unit * (line.discount or 0.0) / 100
                self.valor_total = self.amount_untaxed + self.ice + self.irbpnr + self.iva_12 + self.propina
                # -------------------------------------------------------------------
                # FINALMENTE SE DEFINE EL VALOR DEL PIE DEL TALONARIO DE RETENCIONES
                # Y SE CONSOLIDA LA TABLA CON TODAS SUS LINEAS
                # -------------------------------------------------------------------
                if self.type == "in_invoice":
                    linea6a = str('${:0,.2f}'.format(abs(self.total_retenciones)))
                    linea6a = " " * (13 - len(linea6a)) + str(linea6a)
                    linea6 = linea6 + linea6a + "\n"
                    self.retencion_tabla = linea0 + linea1 + linea2 + linea3 + \
                                           linea4 + linea5 + linea6 + linea7
            # ---------------------------------------------------------
            # SE GUARDA TODOS LOS CAMPOS CALCULADOS EN LA BSE DE DATOS
            # ---------------------------------------------------------
            self.valor_total_letras = self.numero_a_moneda(self.valor_total)
            vals = {
                'subtotal_0': self.subtotal_0,
                'subtotal_12': self.subtotal_12,
                'subtotal_no_sujeto_iva': self.subtotal_no_sujeto_iva,
                'descuento': self.descuento,
                'ice': self.ice,
                'irbpnr': self.irbpnr,
                'iva_12': self.iva_12,
                'propina': self.propina,
                'valor_total': self.valor_total,
                'total_retenciones': self.total_retenciones,
                'retencion_tabla': self.retencion_tabla,
                'valor_total_letras': self.valor_total_letras,
            }
            formulario = self.env['account.invoice'].search([('number', '=', self.number), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
            formulario.write(vals)

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def boton_validar_doc(self):
        if self.type == "in_invoice":
            if self.state == "paid":
                if self.bool_doc_revertido is True:
                    if self.bool_doc_enviado is True and (
                            self.bool_confirm_sri == "" or self.bool_confirm_sri is False):
                        mensaje_1 = "SE HA DETECTADO LA ANULACION EN ODOO DEL COMPROBANTE DE RETENCION No (" + self.doc_electronico_no
                        mensaje_2 = '), EL CUAL AUN SE ENCUENTRA ACTIVO EN EL SRI. ESTE COMPROBANTE ELECTRONICO DEBE SER ANULADO '
                        mensaje_3 = 'MANUALMENTE A TRAVES DEL PORTAL WEB DE LA AUTORIDAD TRIBUTARIA. UNA VEZ QUE SE HAYA COMPLETADO '
                        mensaje_4 = 'ESTE PROCEDIMIENTO, REGISTRE EL DOCUMENTO DE ANULACION EN EL CAMPO EDITABLE (No Anulación) '
                        mensaje_5 = 'Y VALIDE LA COMPRA NUEVAMENTE.'
                        # --------------------------------------------------------------------------------
                        # MESSAGE_BOX CODE: USAR SOLO PARA MENSAJES INFORMATIVOS QUE NO DETENGAN PROCESOS
                        # --------------------------------------------------------------------------------
                        title = "ADVERTENCIA: Proceso faltante en el SRI (E+A+R+S-)"
                        message = mensaje_1 + mensaje_2 + mensaje_3 + mensaje_4 + mensaje_5
                        view = self.env.ref('l10n_ec_invoice.message_box_form')
                        # view_id = view and view.id or False
                        context = dict(self._context or {})
                        context['message'] = message
                        return {'name': title, 'type': 'ir.actions.act_window', 'res_model': 'message_box',
                                'view_mode': 'form',
                                'view_type': 'form', 'view_id': view.id, 'target': 'new', 'context': context, }
                    elif self.bool_doc_enviado is True and self.bool_confirm_sri != "":
                        self.bool_validar = True
                        # --------------------------------------------------------------------------------
                        # MESSAGE_BOX CODE: USAR SOLO PARA MENSAJES INFORMATIVOS QUE NO DETENGAN PROCESOS
                        # --------------------------------------------------------------------------------
                        title = "INFORMACION: (E+A+R+S+)"
                        message = "PROCESO DE VALIDACION TERMINADO CORRECTAMENTE"
                        view = self.env.ref('l10n_ec_invoice.message_box_form')
                        # view_id = view and view.id or False
                        context = dict(self._context or {})
                        context['message'] = message
                        return {'name': title, 'type': 'ir.actions.act_window', 'res_model': 'message_box',
                                'view_mode': 'form',
                                'view_type': 'form', 'view_id': view.id, 'target': 'new', 'context': context, }
                    elif self.bool_doc_enviado is False:
                        self.bool_validar = True
                        # --------------------------------------------------------------------------------
                        # MESSAGE_BOX CODE: USAR SOLO PARA MENSAJES INFORMATIVOS QUE NO DETENGAN PROCESOS
                        # --------------------------------------------------------------------------------
                        title = "INFORMACION: (E+A+R-)"
                        message = "PROCESO DE VALIDACION TERMINADO CORRECTAMENTE"
                        view = self.env.ref('l10n_ec_invoice.message_box_form')
                        # view_id = view and view.id or False
                        context = dict(self._context or {})
                        context['message'] = message
                        return {'name': title, 'type': 'ir.actions.act_window', 'res_model': 'message_box',
                                'view_mode': 'form',
                                'view_type': 'form', 'view_id': view.id, 'target': 'new', 'context': context, }
                elif self.bool_doc_revertido is False:
                    total_retenciones = abs(self.total_retenciones)
                    if total_retenciones > 0:
                        if self.bool_doc_enviado is True:
                            self.bool_validar = True
                            # --------------------------------------------------------------------------------
                            # MESSAGE_BOX CODE: USAR SOLO PARA MENSAJES INFORMATIVOS QUE NO DETENGAN PROCESOS
                            # --------------------------------------------------------------------------------
                            title = "INFORMACION: (E+A-R+)"
                            message = "PROCESO DE VALIDACION TERMINADO CORRECTAMENTE"
                            view = self.env.ref('l10n_ec_invoice.message_box_form')
                            # view_id = view and view.id or False
                            context = dict(self._context or {})
                            context['message'] = message
                            return {'name': title, 'type': 'ir.actions.act_window', 'res_model': 'message_box',
                                    'view_mode': 'form',
                                    'view_type': 'form', 'view_id': view.id, 'target': 'new', 'context': context, }
                        elif self.bool_doc_enviado is False:
                            # --------------------------------------------------------------------------------
                            # MESSAGE_BOX CODE: USAR SOLO PARA MENSAJES INFORMATIVOS QUE NO DETENGAN PROCESOS
                            # --------------------------------------------------------------------------------
                            title = "ADVERTENCIA: Proceso incompleto (E+A-R-)"
                            message = "NO SE HA GENERADO AUN EL COMPROBANTE DE RETENCION EN LA FUENTE"
                            view = self.env.ref('l10n_ec_invoice.message_box_form')
                            # view_id = view and view.id or False
                            context = dict(self._context or {})
                            context['message'] = message
                            return {'name': title, 'type': 'ir.actions.act_window', 'res_model': 'message_box',
                                    'view_mode': 'form',
                                    'view_type': 'form', 'view_id': view.id, 'target': 'new', 'context': context, }
                    elif self.total_retenciones <= 0.0009:
                        self.bool_validar = True
                        # --------------------------------------------------------------------------------
                        # MESSAGE_BOX CODE: USAR SOLO PARA MENSAJES INFORMATIVOS QUE NO DETENGAN PROCESOS
                        # --------------------------------------------------------------------------------
                        title = "INFORMACION: (E+A-R0)"
                        message = "PROCESO DE VALIDACION TERMINADO CORRECTAMENTE"
                        view = self.env.ref('l10n_ec_invoice.message_box_form')
                        # view_id = view and view.id or False
                        context = dict(self._context or {})
                        context['message'] = message
                        return {'name': title, 'type': 'ir.actions.act_window', 'res_model': 'message_box',
                                'view_mode': 'form',
                                'view_type': 'form', 'view_id': view.id, 'target': 'new', 'context': context, }
            else:
                # --------------------------------------------------------------------------------
                # MESSAGE_BOX CODE: USAR SOLO PARA MENSAJES INFORMATIVOS QUE NO DETENGAN PROCESOS
                # --------------------------------------------------------------------------------
                title = "ADVERTENCIA: Estado Abierto (E-)"
                message = "NO SE PUEDE VALIDAR UN PROCESO EN ESTADO ABIERTO. COMPLETE EL PAGO PARA CONTINUAR."
                view = self.env.ref('l10n_ec_invoice.message_box_form')
                # view_id = view and view.id or False
                context = dict(self._context or {})
                context['message'] = message
                return {'name': title, 'type': 'ir.actions.act_window', 'res_model': 'message_box',
                        'view_mode': 'form',
                        'view_type': 'form', 'view_id': view.id, 'target': 'new', 'context': context, }

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def validar_NCC(self):
        if self.type == "in_refund":
            # ---------------------------------------------------------------------------------------
            # VERIFICA SI EL DOCUMENTO FUE GENERADO POR EL PROCESO DE GENERACION DE NCC DE ODOO
            # Y COMPLETA LA INFORMACION FALTANTE:
            # numero_identidad en la NCC
            # char_numDocModificado en la NCC
            # select_numDiarioModificado_compras en la NCC y
            # origin en la FACTURA MODIFICADA
            # bool_validar en la FACTURA MODIFICADA
            # ADICIONALMENTE MODIFICA reference EN LA FACTURA MODIFICADA PARA QUE PUEDA SER VALIDADO
            # CON EL MISMO NUMERO DE REFERENCIA ORIGINAL
            # ---------------------------------------------------------------------------------------
            origen = self.env['account.invoice'].search([('number', '=', self.origin)])
            # -----------------------------------------------
            # MODIFICA EL reference DEL FORMULARIO DE ORIGEN
            # -----------------------------------------------
            if str.__contains__(origen.reference, "R"):
                reference = origen.reference
            else:
                reference = origen.reference + "R"
            # ----------------------------------------------------------------------------
            # MODIFICA EL bool_onOff_no_anulacion & bool_validar DEL FORMULARIO DE ORIGEN
            # ----------------------------------------------------------------------------
            if origen.total_retenciones == 0:
                anulacion = True
                validar = True
            else:
                anulacion = False
                if origen.bool_confirm_sri is True:
                    validar = True
                else:
                    validar = False
            # ----------------------------------------------------------
            # CAMBIA EL ESTADO DE DOCUMENTO REVERTIDO
            # ----------------------------------------------------------
            vals = {
                'bool_doc_revertido': True,
                'reference': reference,
                'bool_onOff_no_anulacion': anulacion,
                'bool_validar': validar,
            }
            origen.write(vals)
            # --------------------------------------------------------------
            # MODIFICA EL reference DEL DOCUMENTO DE REVERSION
            # VALIDAR PROCESO
            # --------------------------------------------------------------
            vals = {
                'reference': reference,
                'bool_validar': True
            }
            formulario = self.env['account.invoice'].search([('number', '=', self.number), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
            formulario.write(vals)

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # @api.one
    # @api.depends('state')
    # def _calcular_validaciones(self):
    # for record in self:
    # if record.state == "open" and record.type == "in_invoice":
    # record.doc_electronico_no = self.doc_electronico_no
    # record.doc_electronico_fecha = self.doc_electronico_fecha
    # record.doc_electronico_xml = self.doc_electronico_xml
    # record.bool_doc_enviado = self.bool_doc_enviado

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.onchange('metodo_pago')
    def _cambiar_posicion_fiscal(self):
        self.ensure_one()
        FISCAL = self.env['account.fiscal.position']
        # --------------------------------------------------------------
        # MODIFICA LAS POSICIONES FISCALES EN FUCION DEL MÉTODO DE PAGO
        # --------------------------------------------------------------
        if self.metodo_pago == "10" or self.metodo_pago == "19":  # 10 o 19 Tarjeta de Crédito
            # --------------------------------
            # 11 Compras Pago Tarjeta Crédito
            # --------------------------------
            fiscal_position = FISCAL.browse([11])
        elif self.metodo_pago == "16":  # 16 Tarjeta de Débito
            # --------------------------------
            # 11 Compras Pago Tarjeta Crédito
            # --------------------------------
            fiscal_position = FISCAL.browse([11])
        elif self.metodo_pago == "06":  # 06 Débito de Cuenta
            # --------------------------------
            # 10 Compras Pago Convenio Débito
            # --------------------------------
            fiscal_position = FISCAL.browse([10])
        else:  # Others
            # -----------------------------------
            # MANTIENE LA POSICION FISCAL ACTUAL
            # -----------------------------------
            fiscal_position = self.partner_id.property_account_position_id
        if fiscal_position:
            self.fiscal_position_id = fiscal_position
        return {}

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.onchange('reference', 'tipo_comprobante', 'date_invoice')
    def _crear_no_documento(self):
        espacio = " "
        coma = ","
        punto = "."
        guion = "-"
        reference_new = self.reference
        try:
            if reference_new:
                if str.__contains__(reference_new, espacio):  # separador espacio
                    numero_establecimiento = str('%03i' % int(reference_new.split(espacio)[0]), )
                    punto_emision = str('%03i' % int(reference_new.split(espacio)[1]), )
                    numero_factura = str('%09i' % int(reference_new.split(espacio)[2]), )
                    self.reference = numero_establecimiento + "-" + punto_emision + "-" + numero_factura
                if str.__contains__(reference_new, coma):  # separador coma
                    numero_establecimiento = str('%03i' % int(reference_new.split(coma)[0]), )
                    punto_emision = str('%03i' % int(reference_new.split(coma)[1]), )
                    numero_factura = str('%09i' % int(reference_new.split(coma)[2]), )
                    self.reference = numero_establecimiento + "-" + punto_emision + "-" + numero_factura
                if str.__contains__(reference_new, punto):  # separador punto
                    numero_establecimiento = str('%03i' % int(reference_new.split(punto)[0]), )
                    punto_emision = str('%03i' % int(reference_new.split(punto)[1]), )
                    numero_factura = str('%09i' % int(reference_new.split(punto)[2]), )
                    self.reference = numero_establecimiento + "-" + punto_emision + "-" + numero_factura
                if str.__contains__(reference_new, guion):  # separador guion
                    numero_establecimiento = str('%03i' % int(reference_new.split(guion)[0]), )
                    punto_emision = str('%03i' % int(reference_new.split(guion)[1]), )
                    numero_factura = str('%09i' % int(reference_new.split(guion)[2]), )
                    self.reference = numero_establecimiento + "-" + punto_emision + "-" + numero_factura
            # --------------------------------------------------------------
            # SE DEBE USAR write PARA MANTENER LOS CAMBIOS EN EL FORMULARIO
            # --------------------------------------------------------------
            vals = {
                'reference': self.reference,
                'doc_electronico_no': self.doc_electronico_no,
                'secuencia_emision': self.secuencia_emision
            }
            factura = self.env['account.invoice'].search(
                [('reference', '=', self.reference), ('numero_autorizacion', '=', self.numero_autorizacion)])
            factura.write(vals)
        except Exception as e:
            error_line_message_1 = "Usar UN SOLO TIPO de separador de números: espacio , . -"
            error_line_message_2 = "Por ejemplo si escribimos: 1-3-45 [Enter] obtendremos: 001-003-000000045"
            error_line_message_3 = "Python Error: { " + (str(e)) + " }"
            raise UserError(
                error_line_message_1 + "\n" + "\n" + error_line_message_2 + "\n" + "\n" + error_line_message_3)

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.onchange('partner_id')
    def _compute_partner_id(self):
        self.numero_identidad = self.partner_id.numero_identidad
        model = 'res.partner'
        domain = [('name', '=', self.partner_id.name)]
        ids = self.env[model].search(domain)
        self.partner_id = ids.id
        self.numero_identidad = ids.numero_identidad

        # mensaje = {}
        # self.env['bus.bus'].sendone(('oodca_02', 'account.invoice'), mensaje)

        # if self.type == "out_invoice" and self.number is not False:
        # establecimiento = self.env['account.journal'].search([('id', '=', self.journal_id.id)]).name[0:3]
        # punto_emision = self.env['account.journal'].search([('id', '=', self.journal_id.id)]).name[4:7]
        # numero_secuencial = "0" * (9 - len(self.number.split('/')[2])) + self.number.split('/')[2]
        # self.reference = establecimiento + "-" + punto_emision + "-" + numero_secuencial
        # ------------------------------
        # SE GUARDA EN LA BASE DE DATOS
        # numero_identidad
        # ------------------------------
        vals = {
            'numero_identidad': self.numero_identidad
        }
        formulario = self.env['account.invoice'].search([('number', '=', self.number), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
        formulario.write(vals)

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.onchange('numero_identidad')
    def _buscar_no_identidad(self):
        if self.numero_identidad:
            # ---------------------------------------------------------------------------------------
            # Limita la búsqueda solo a los numeros de identidad cuyos 2 primeros dígitos sean <= 24
            # y cuyo número de dígitos >=9 (mínimo necesario para realizar una búsqueda certera
            # en la base de datos del SRI)
            # ---------------------------------------------------------------------------------------
            if int(self.numero_identidad[0:2]) <= 24 and len(self.numero_identidad) >= 9:
                query_sql = "SELECT * FROM res_partner " + \
                            "WHERE numero_identidad ILIKE '" + self.numero_identidad + "%'"
                self.env.cr.execute(query_sql)
                for res in self.env.cr.fetchall():
                    if res:
                        self.partner_id = res
                    else:
                        self.numero_identidad = self.partner_id.numero_identidad
            else:
                self.numero_identidad = self.partner_id.numero_identidad
        self.char_usuarioNombreComercial = self.env['res.partner'].search(
            [('id', '=', self.user_id.partner_id.id)]).nombre_comercial
        # ------------------------------
        # SE GUARDA EN LA BASE DE DATOS
        # doc_electronico_no
        # doc_electronico_fecha
        # doc_electronico_xml
        # bool_doc_enviado
        # ------------------------------
        vals = {
            'numero_identidad': self.numero_identidad,
            'char_usuarioNombreComercial': self.char_usuarioNombreComercial
        }
        formulario = self.env['account.invoice'].search([('number', '=', self.number), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
        formulario.write(vals)

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.onchange('doc_electronico_no_anulacion')
    def _cambiar_marcador_confirmacion(self):
        if self.doc_electronico_no_anulacion:
            if self.doc_electronico_no_anulacion == "":
                self.bool_confirm_sri = False
            else:
                self.bool_confirm_sri = True
        else:
            self.bool_confirm_sri = False
        # ----------------------------------------------------------------------------------------------
        # en onchange se trabaja sobre un entorno virtual. Se debe usar write para mentener los cambios
        # ----------------------------------------------------------------------------------------------
        factura = self.env['account.invoice'].search([('number', '=', self.number), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
        factura.write({'bool_confirm_sri': self.bool_confirm_sri})

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.onchange('select_numDiarioModificado_compras')
    def _cambiar_diario_modificado_compras(self):
        FACTURAS = self.env['account.invoice'].search([('number', '=', self.select_numDiarioModificado_compras.number)])
        for factura in FACTURAS:
            if factura.id == self.select_numDiarioModificado_compras.id:
                Fecha_str = str(factura.date_invoice)
                Fecha_obj = datetime.strptime(Fecha_str, '%Y-%m-%d').date()
                Fecha = Fecha_obj.strftime("%d/%m/%Y")
                self.char_numDocModificado = factura.reference
                self.char_docModificado_fecha = Fecha
                break
            else:
                self.char_numDocModificado = ""
        vals = {
            'char_numDocModificado': self.char_numDocModificado,
            'char_docModificado_fecha': self.char_docModificado_fecha
        }
        formulario = self.env['account.invoice'].search([('number', '=', self.number), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
        formulario.write(vals)

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.onchange('select_numDiarioModificado_ventas')
    def _cambiar_diario_modificado_ventas(self):
        FACTURAS = self.env['account.invoice'].search([('number', '=', self.select_numDiarioModificado_ventas.number)])
        for factura in FACTURAS:
            if factura.id == self.select_numDiarioModificado_ventas.id:
                Fecha_str = str(factura.date_invoice)
                Fecha_obj = datetime.strptime(Fecha_str, '%Y-%m-%d').date()
                Fecha = Fecha_obj.strftime("%d/%m/%Y")
                self.char_numDocModificado = factura.reference
                self.char_docModificado_fecha = Fecha
                break
            else:
                self.char_numDocModificado = ""
        vals = {
            'char_numDocModificado': self.char_numDocModificado,
            'char_docModificado_fecha': self.char_docModificado_fecha
        }
        formulario = self.env['account.invoice'].search([('number', '=', self.number), ('type', '=', self.type), ('partner_id', '=', self.partner_id.id)])
        formulario.write(vals)

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def name_get(self):
        # ------------------------------------------------------------
        # CAMBIA LA PRESENTACION EN PANTALLA DE LOS SIGUIENTES CAMPOS
        # select_numDiarioModificado_ventas
        # ------------------------------------------------------------
        result = []
        cadena = {}
        for record in self:
            if record.number and record.amount_untaxed:
                cadena = record.number + " " + " " + record.reference + " " + str('${:0,.2f}'.format(record.amount_untaxed))
            result.append((record.id, cadena))
        return result

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def tipo_tributario(self):
        # ------------------------------------------------------------
        # CAMBIA LA PRESENTACION EN PANTALLA DE LOS SIGUIENTES CAMPOS
        # tipo_documento_tributario
        # char_numDocModificado
        # name
        # ------------------------------------------------------------
        if len(self._ids) <= 1:
            FORMULARIOS = self.env['account.invoice'].search([])
            for formulario in FORMULARIOS:
                # ----------------------------------------------------------------------------
                # CORRIGE EL CAMPO DEL COMPROBANTE ELECTRONICO EN CASO DE QUE SE HAYA BORRADO
                # ----------------------------------------------------------------------------
                # if not formulario.doc_electronico_no:
                #    if formulario.doc_electronico_no_autorizacion:
                #        vals = {
                #            'doc_electronico_no':
                #                formulario.doc_electronico_no_autorizacion[24:27] + "-" +
                #                formulario.doc_electronico_no_autorizacion[27:30] + "-" +
                #                formulario.doc_electronico_no_autorizacion[30:39]
                #        }
                #        formulario.write(vals)
                if formulario.type == "out_invoice":
                    formulario.tipo_documento_tributario = "FACTURA DE VENTA"
                    formulario.tipo_formulario = "FACTURA"
                if formulario.type == "out_refund":
                    if formulario.origin is not False:
                        formulario.tipo_documento_tributario = "NOTA DE CREDITO DE VENTA"
                        formulario.tipo_formulario = "NOTA CREDITO"
                        formulario.name = "DEVOLUCION"
                    else:
                        formulario.tipo_documento_tributario = "COMPROBANTE DE RETENCION DE VENTA"
                        formulario.tipo_formulario = "RETENCION"
                        formulario.name = "RETENCION"
                if formulario.type == "in_invoice":
                    formulario.tipo_documento_tributario = "DOCUMENTO DE COMPRA"
                    formulario.tipo_formulario = "FACTURA"
                if formulario.type == "in_refund":
                    if formulario.origin is not False:
                        formulario.tipo_documento_tributario = "REVERSION DE DOCUMENTO DE COMPRA"
                        formulario.tipo_formulario = "REVERSION"
                        formulario.name = "REVERSION"
                    else:
                        formulario.tipo_documento_tributario = "NOTA DE CREDITO DE COMPRA"
                        formulario.tipo_formulario = "NOTA CREDITO"
                        # noinspection PyAttributeOutsideInit
                        formulario.name = "DEVOLUCION"
                formulario.establecimiento_venta = formulario.journal_id.establecimiento + "-" + formulario.journal_id.punto_emision
                vals = {
                    'tipo_documento_tributario': formulario.tipo_documento_tributario,
                    'char_numDocModificado': formulario.char_numDocModificado,
                    'name': formulario.name,
                    'tipo_formulario': formulario.tipo_formulario,
                    'establecimiento_venta': formulario.establecimiento_venta
                }
                formulario_nuevo = formulario.env['account.invoice'].search([('number', '=', formulario.number)])
                formulario_nuevo.write(vals)

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def numero_a_letras(self, numero):
        MAX_NUMERO = 999999999999

        numero_entero = int(numero)

        if numero_entero > MAX_NUMERO:
            raise OverflowError('Número demasiado alto y fuera de rango')
        if numero_entero < 0:
            return 'MENOS %s' % self.numero_a_letras(abs(numero))

        letras_decimal = ''
        parte_decimal = int(round((abs(numero) - abs(numero_entero)) * 100))
        if parte_decimal > 9:
            letras_decimal = ' CON %s' % self.numero_a_letras(parte_decimal)
        elif parte_decimal > 0:
            letras_decimal = ' CON %s' % self.numero_a_letras(parte_decimal)

        if numero_entero <= 99:
            resultado = self.leer_decenas(numero_entero)
        elif numero_entero <= 999:
            resultado = self.leer_centenas(numero_entero)
        elif numero_entero <= 999999:
            resultado = self.leer_miles(numero_entero)
        elif numero_entero <= 999999999:
            resultado = self.leer_millones(numero_entero)
        else:
            resultado = self.leer_millardos(numero_entero)

        resultado = resultado.replace('uno mil', 'un mil')
        resultado = resultado.strip()
        resultado = resultado.replace(' _ ', ' ')
        resultado = resultado.replace('  ', ' ')
        resultado = '%s %s' % (resultado, letras_decimal)
        return resultado

    def numero_a_moneda(self, numero):
        MONEDA_SINGULAR = 'DOLAR'
        MONEDA_PLURAL = 'DOLARES'
        CENTAVOS_SINGULAR = 'CENTAVO'
        CENTAVOS_PLURAL = 'CENTAVOS'
        # MAX_NUMERO = 999999999999

        numero_entero = int(numero)
        parte_decimal = int(round((abs(numero) - abs(numero_entero)) * 100))
        # centavos = ''
        if parte_decimal == 1:
            centavos = CENTAVOS_SINGULAR
        else:
            centavos = CENTAVOS_PLURAL
        # moneda = ''
        if numero_entero == 1:
            moneda = MONEDA_SINGULAR
        else:
            moneda = MONEDA_PLURAL
        letras = self.numero_a_letras(numero_entero)
        letras = letras.replace('UNO', 'UN')
        letras_decimal = ' CON %s%s' % (self.numero_a_letras(parte_decimal).replace('UNO', 'UN'), centavos)
        letras = '%s%s%s' % (letras, moneda, letras_decimal)
        return letras

    @staticmethod
    def leer_decenas(numero):
        UNIDADES = (
            'CERO',
            'UN',
            'DOS',
            'TRES',
            'CUATRO',
            'CINCO',
            'SEIS',
            'SIETE',
            'OCHO',
            'NUEVE'
        )
        DECENAS = (
            'DIEZ',
            'ONCE',
            'DOCE',
            'TRECE',
            'CATORCE',
            'QUINCE',
            'DIECISEIS',
            'DIECISIETE',
            'DIECIOCHO',
            'DIECINUEVE'
        )
        DIEZ_DIEZ = (
            'CERO',
            'DIEZ',
            'VEINTE',
            'TREINTA',
            'CUARENTA',
            'CINCUENTA',
            'SESENTA',
            'SETENTA',
            'OCHENTA',
            'NOVENTA'
        )
        if numero < 10:
            return UNIDADES[numero]
        decena, unidad = divmod(numero, 10)
        if numero <= 19:
            resultado = DECENAS[unidad]
        elif 21 <= numero <= 29:
            resultado = 'VEINTI%s' % UNIDADES[unidad]
        else:
            resultado = DIEZ_DIEZ[decena]
            if unidad > 0:
                resultado = '%s Y %s' % (resultado, UNIDADES[unidad])
        return resultado

    def leer_centenas(self, numero):
        CIENTOS = (
            '_',
            'CIENTO',
            'DOSCIENTOS',
            'TRESCIENTOS',
            'CUATROCIENTOS',
            'QUINIENTOS',
            'SEISCIENTOS',
            'SETECIENTOS',
            'OCHOCIENTOS',
            'NOVECIENTOS'
        )
        centena, decena = divmod(numero, 100)
        if centena == 1 and decena == 0:
            resultado = 'CIEN'
        else:
            resultado = CIENTOS[centena]
            if decena > 0:
                resultado = '%s %s' % (resultado, self.leer_decenas(decena))
        return resultado

    def leer_miles(self, numero):
        UNIDADES = (
            'CERO',
            'UNO',
            'DOS',
            'TRES',
            'CUATRO',
            'CINCO',
            'SEIS',
            'SIETE',
            'OCHO',
            'NUEVE'
        )
        millar, centena = divmod(numero, 1000)
        resultado = ''
        if millar == 1:
            resultado = ''
        if 2 <= millar <= 9:
            resultado = UNIDADES[millar]
        elif 10 <= millar <= 99:
            resultado = self.leer_decenas(millar)
        elif 100 <= millar <= 999:
            resultado = self.leer_centenas(millar)
        resultado = '%s MIL' % resultado
        if centena > 0:
            resultado = '%s %s' % (resultado, self.leer_centenas(centena))
        return resultado

    def leer_millones(self, numero):
        UNIDADES = (
            'CERO',
            'UNO',
            'DOS',
            'TRES',
            'CUATRO',
            'CINCO',
            'SEIS',
            'SIETE',
            'OCHO',
            'NUEVE'
        )
        millon, millar = divmod(numero, 1000000)
        resultado = ''
        if millon == 1:
            resultado = ' UN MILLON '
        if 2 <= millon <= 9:
            resultado = UNIDADES[millon]
        elif 10 <= millon <= 99:
            resultado = self.leer_decenas(millon)
        elif 100 <= millon <= 999:
            resultado = self.leer_centenas(millon)
        if millon > 1:
            resultado = '%s MILLONES' % resultado
        if 0 < millar <= 999:
            resultado = '%s %s' % (resultado, self.leer_centenas(millar))
        elif 1000 <= millar <= 999999:
            resultado = '%s %s' % (resultado, self.leer_miles(millar))
        return resultado

    def leer_millardos(self, numero):
        millardo, millon = divmod(numero, 1000000)
        return '%s MILLONES %s' % (self.leer_miles(millardo), self.leer_millones(millon))


# ----------------------------------------------------------------------------------------------------------------------
#   O   OOOOO OOOOO OOOOO O   O O   O OOOOO     OOO  O   O O   O OOOOO  OOO  OOOOO OOOOO    OOOOO   O   O   O
#  O O  O     O     O   O O   O OO  O   O        O   OO  O O   O O   O   O   O     O          O    O O   O O
# O   O O     O     O   O O   O O O O   O        O   O O O O   O O   O   O   O     OOO        O   O   O   O
# OOOOO O     O     O   O O   O O  OO   O        O   O  OO  O O  O   O   O   O     O          O   OOOOO  O O
# O   O OOOOO OOOOO OOOOO OOOOO O   O   O       OOO  O   O   O   OOOOO  OOO  OOOOO OOOOO      O   O   O O   O
# ----------------------------------------------------------------------------------------------------------------------
class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    # ----- DEFINICION DE CAMPOS ADICIONALES EN LA TABLA DE IMPUESTOS -----
    base_imponible = fields.Monetary(string='Base imponible')
    porcentaje_ret_iva = fields.Float(string='% Retención IVA')
    porcentaje_retencion = fields.Float(string='% Retención')
    nombre_impuesto = fields.Char(string='Nombre Impuesto')
    codigo_tabla_19 = fields.Char(string='SRI Tabla 19')
    codigo_tabla_20 = fields.Char(string='SRI Tabla 20')


# ----------------------------------------------------------------------------------------------------------------------
# OOOOO OOOOO OOOOO    OOOOO OOOOO O   O OOOOO   O   O   O O   O
# O   O O     O        O     O   O OO OO O   O  O O  OO  O O   O
# OOOOO OOO   OOOOO    O     O   O O O O OOOOO O   O O O O  OOO
# O  O  O         O    O     O   O O   O O     OOOOO O  OO   O
# O   O OOOOO OOOOO    OOOOO OOOOO O   O O     O   O O   O   O
# ----------------------------------------------------------------------------------------------------------------------
class ResCompany(models.Model):
    _inherit = 'res.company'

    # ----- field definition -----
    company_facturacion_electronica = fields.Selection(
        [
            ('SI', 'SI'),
            ('NO', 'NO')
        ],
        string='Factura Electrónica',
        help='Facturación electrónica: MODIFICAR desde la parametrización de la COMPAÑÍA',
        readonly=True,
        required=True,
        default='NO'
    )
    company_ruta_documentos = fields.Char(
        string='Ruta Doc Electrónicos',
        readonly=True,
        help='Ruta de la carpeta donde se generarán los documentos electrónicos',
    )

    electronic_signature = fields.Char(
        'Ruta Firma Electrónica',
        size=128,
        help="Ruta y nombre del archivo que contiene la FIRMA ELECTRONICA de la compañía",
    )
    password_electronic_signature = fields.Char(
        'Clave Firma',
        size=255,
        help="Clave de la FIRMA ELECTRONICA"
    )
    expiration_date = fields.Date(
        string=u'Fecha Caduca Firma',
        readonly=False,
        required=True,
        index=True,
        copy=False,
        states={},
        default=datetime.now().strftime('%Y-%m-01'),
        help=u"Fecha Expiración"
    )
    emission_code = fields.Selection(
        [
            ('1', 'Normal'),
            ('2', 'Indisponibilidad')
        ],
        string='Tipo Emisión',
        required=True,
        default='1',
        help="Tipo de emisión de los Documentos Electrónicos"
    )
    env_service = fields.Selection(
        [
            ('1', 'Pruebas'),
            ('2', 'Producción')
        ],
        string='Tipo Ambiente',
        required=True,
        default='1',
        help="Tipo de ambiente del Servicio"
    )
    type_environment = fields.Selection(
        [
            ('1', 'Pruebas'),
            ('2', 'Producción')
        ],
        string='Tipo Ambiente DocEl',
        index=True,
        readonly=False,
        default='1',
        help="Tipo de ambiente de los Documentos Electrónicos"
    )
    sri_scheme = fields.Selection(
        [
            ('1', 'Offline'),
            ('2', 'Online')
        ],
        string='Esquema SRI',
        required=True,
        default='1',
        help="Esquema de trabajo con el SRI"
    )

    ws_receipt_test = fields.Char(
        u'URL del WS de Pruebas de SRI para Recepción de Documentos',
        required=False,
        help=u"",
        default="https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl"
    )
    ws_receipt_production = fields.Char(
        u'URL del WS de Producción de SRI para Recepción de Documentos',
        required=False,
        help=u"",
        default='https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'
    )
    ws_receipt_test_offline = fields.Char(
        u'URL del WS de Pruebas de SRI para Recepción de Documentos (Offline)',
        required=False,
        help=u"",
        default="https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl"
    )
    ws_receipt_production_offline = fields.Char(
        u'URL del WS de Producción de SRI para Recepción de Documentos (Offline)',
        required=False,
        help=u"",
        default='https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'
    )

    ws_receipt_grouped_test = fields.Char(
        u'URL del WS de Pruebas de SRI para Recepción Lotes Masivos de Documentos',
        required=False,
        help=u"",
    )
    ws_receipt_grouped_production = fields.Char(
        u'URL del WS de Producción de SRI para Recepción Lotes Masivos de Documentos',
        required=False,
        help=u"",
    )

    ws_auth_test = fields.Char(
        u'URL del WS de Pruebas de SRI para Autorización de Documentos',
        required=False,
        help=u"",
        default="https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl"
    )
    ws_auth_production = fields.Char(
        u'URL del WS de Producción SRI para Autorización de Documentos',
        required=False,
        help=u"",
        default='https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'
    )

    ws_auth_test_offline = fields.Char(
        u'URL del WS de Pruebas de SRI para Autorización de Documentos (Offline)',
        required=False,
        help=u"",
        default="https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl"
    )
    ws_auth_production_offline = fields.Char(
        u'URL del WS de Producción SRI para Autorización de Documentos (Offline)',
        required=False,
        help=u"",
        default='https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
    )

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.onchange('env_service')
    def _facturacion_electronica_creation(self):
        # --------------------------
        # CONSULTA TIPO DE AMBIENTE
        # --------------------------
        self.type_environment = self.env_service

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    def _get_ws(self):
        # -----------------
        # SRI WEB SERVICES
        # -----------------
        if self.sri_scheme == "1":
            # --------------
            # SI ES OFFLINE
            # --------------
            if self.type_environment == "1":
                # --------------
                # SI ES PRUEBAS
                # --------------
                return self.ws_receipt_test_offline, self.ws_auth_test_offline
            else:
                # -----------------
                # SI ES PRODUCCION
                # -----------------
                return self.ws_receipt_production_offline, self.ws_auth_production_offline
        else:
            # -------------
            # SI ES ONLINE
            # -------------
            if self.type_environment == "1":
                # --------------
                # SI ES PRUEBAS
                # --------------
                return self.ws_receipt_test, self.ws_auth_test
            else:
                # -----------------
                # SI ES PRODUCCION
                # -----------------
                return self.ws_receipt_production, self.ws_auth_production


# ----------------------------------------------------------------------------------------------------------------------
#   O   OOOOO OOOOO OOOOO O   O O   O OOOOO        O OOOOO O   O OOOOO O   O   O   O
#  O O  O     O     O   O O   O OO  O   O          O O   O O   O O   O OO  O  O O  O
# O   O O     O     O   O O   O O O O   O          O O   O O   O OOOOO O O O O   O O
# OOOOO O     O     O   O O   O O  OO   O      O   O O   O O   O O  O  O  OO OOOOO O
# O   O OOOOO OOOOO OOOOO OOOOO O   O   O      OOOOO OOOOO OOOOO O   O O   O O   O OOOOO
# ----------------------------------------------------------------------------------------------------------------------
class AccountJournal(models.Model):
    _inherit = 'account.journal'

    # ----------------------
    # PUNTO DE EMISION
    # ----------------------
    establecimiento = fields.Char(
        string='',
        help="",
        size=3,
        default='001',
    )
    # ----------------------
    # PUNTO DE VENTA
    # ----------------------
    punto_emision = fields.Char(
        string='',
        help="",
        size=3,
        default='001',
    )
    # ----------------------
    # NOMBRE
    # ----------------------
    nombre = fields.Char(
        string='',
        help="",
    )
    # ----------------------
    # NOMBRE DEL DIARIO
    # ----------------------
    nombre_diario = fields.Char(
        string='',
        help="",
    )
    # ----------------------
    # LIQUIDACION DE COMPRA
    # ----------------------
    liquidacionCompra_electronica = fields.Boolean(
        string='Liq.Comp. electrónica',
        help="Marque esta casilla si desea generar liquidaciones de compra electrónicas para este diario",
        default=False
    )
    liquidacionCompra_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Liq.Comp.: Secuencia',
        help="Este campo contiene la información relacionada con la numeración de las Liquidaciones de Compra de este diario",
        copy=False
    )
    liquidacionCompra_sequence_number_next = fields.Integer(
        string='Liq.Comp: Próximo No',
        default=1,
        help='Este número será usado en la siguiente Liquidación de Compra'
    )
    # -------------------------
    # COMPROBANTE DE RETENCION
    # -------------------------
    retencion_electronica = fields.Boolean(
        string='Retención electrónica',
        help="Marque esta casilla si desea generar comprobantes de retención electrónicos para este diario",
        default=False
    )
    retencion_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Retención: Secuencia',
        help="Este campo contiene la información relacionada con la numeración de los Comprobantes de Retención de este diario",
        copy=False
    )
    retencion_sequence_number_next = fields.Integer(
        string='Retención: Próximo No',
        default=1,
        help='Este número será usado en el siguiente Comprobante de Retención'
    )
    # -----------------
    # FACTURA DE VENTA
    # -----------------
    factura_electronica = fields.Boolean(
        string='Factura electrónica',
        help="Marque esta casilla si desea generar facturas electrónicas para este diario",
        default=False
    )
    factura_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Factura: Secuencia',
        help="Este campo contiene la información relacionada con la numeración de las Facturas de Venta de este diario",
        copy=False
    )
    factura_sequence_number_next = fields.Integer(
        string='Factura: Próximo.No',
        default=1,
        help='Este número será usado en la siguiente Factura de Venta'
    )
    # -------------------------
    # NOTA DE CREDITO DE VENTA
    # -------------------------
    notaCredito_electronica = fields.Boolean(
        string='Nota Créd. electrónica',
        help="Marque esta casilla si desea generar notas de crédito electrónicas para este diario",
        default=False
    )
    notaCredito_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Nota Crédito: Secuencia',
        help="Este campo contiene la información relacionada con la numeración de las Notas de Crédito de Venta de este diario",
        copy=False
    )
    notaCredito_sequence_number_next = fields.Integer(
        string='Nota Créd: Próximo No',
        default=1,
        help='Este número será usado en la siguiente Nota de Crédito'
    )
    # -----------------
    # GUIA DE REMISION
    # -----------------
    guia_electronica = fields.Boolean(
        string='Guía Rem. electrónica',
        help="Marque esta casilla si desea generar guías de remisión electrónicas para este diario",
        default=False
    )
    guia_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Guía Remisión: Secuencia',
        help="Este campo contiene la información relacionada con la numeración de las Guías de Remisión de este diario",
        copy=False
    )
    guia_sequence_number_next = fields.Integer(
        string='Guía Rem: Próximo No',
        default=1,
        help='Este número será usado en la siguiente Guía de Remisión'
    )
    # ------------------------
    # FACTURACION ELECTRONICA
    # ------------------------
    company_facturacion_electronica = fields.Selection(
        [
            ('SI', 'SI'),
            ('NO', 'NO')
        ],
        string='Factura Electrónica',
        help='Facturación electrónica: MODIFICAR desde la parametrización de la COMPAÑÍA',
        required=True,
        default='NO'
    )
    company_ruta_documentos = fields.Char(
        string='Ruta Doc Electrónicos',
        help='Ruta de la carpeta donde se generarán los documentos electrónicos',
    )

    electronic_signature = fields.Char(
        string='Ruta Firma Electrónica',
        size=128,
        help="Ruta y nombre del archivo que contiene la FIRMA ELECTRONICA de la compañía",
    )
    password_electronic_signature = fields.Char(
        'Clave Firma',
        size=255,
        help="Clave de la FIRMA ELECTRONICA"
    )
    expiration_date = fields.Date(
        string=u'Fecha Caduca Firma',
        readonly=False,
        required=True,
        index=True,
        copy=False,
        states={},
        default=datetime.now().strftime('%Y-%m-01'),
        help=u"Fecha Expiración"
    )
    emission_code = fields.Selection(
        [
            ('1', 'Normal'),
            ('2', 'Indisponibilidad')
        ],
        string='Tipo Emisión',
        required=True,
        default='1',
        help="Tipo de emisión de los Documentos Electrónicos"
    )
    env_service = fields.Selection(
        [
            ('1', 'Pruebas'),
            ('2', 'Producción')
        ],
        string='Tipo Ambiente',
        required=True,
        default='1',
        help="Tipo de ambiente del Servicio"
    )
    type_environment = fields.Selection(
        [
            ('1', 'Pruebas'),
            ('2', 'Producción')
        ],
        string='Tipo Ambiente DocEl',
        index=True,
        readonly=False,
        default='1',
        help="Tipo de ambiente de los Documentos Electrónicos"
    )
    sri_scheme = fields.Selection(
        [
            ('1', 'Offline'),
            ('2', 'Online')
        ],
        string='Esquema SRI',
        required=True,
        default='1',
        help="Esquema de trabajo con el SRI"
    )
    # ----------------------------------
    # MODIFICACION DE CAMPOS EXISTENTES
    # ----------------------------------
    refund_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Credit Note Entry Sequence',
        help="This field contains the information related to the numbering of the credit note entries of this journal.",
        copy=False
    )

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.onchange('type', 'establecimiento', 'punto_emision', 'nombre')
    def _jornal_creation(self):
        try:
            # ---------------------
            # MODIFICACION DE name
            # ---------------------
            cuenta_bancaria_id = {}
            nombre_prefijo = ""

            CUENTAS = self.env['account.chart.template'].search([])
            PLAN_CUENTAS = self.env['account.account'].search([])
            if self.type == "sale" or self.type == "purchase":
                if self.name is False:
                    self.name = self.establecimiento + "-" + self.punto_emision
                else:
                    if self.nombre is False:
                        self.nombre = self.name.split('-')[2]


                # ----------------------------------
                # MODIFICACION DE
                # code
                # nombre
                # name
                # refund_sequence
                # default_debit_account_id
                # default_credit_account_id
                # ----------------------------------
                if self.type == "sale":
                    self.code = "VTA"
                    self.refund_sequence = True
                    self.default_debit_account_id = CUENTAS.property_account_receivable_id.id
                    self.default_credit_account_id = CUENTAS.property_account_receivable_id.id
                    if not str.__contains__(self.nombre, "VENTA"):
                        nombre_prefijo = "VENTA"
                    else:
                        nombre_prefijo = self.nombre
                    # ------------------------
                    # MODIFICACION DE FACTURA
                    # ------------------------
                    vals = {
                        'name': self.establecimiento + "-" + self.punto_emision + "-SRI FACTURA Secuencia",
                    }
                    sequence = self.env['ir.sequence'].search([('id', '=', self.factura_sequence_id.id)])
                    sequence.write(vals)
                    self.factura_sequence_id = sequence.id
                    # --------------------------------
                    # MODIFICACION DE NOTA DE CREDITO
                    # --------------------------------
                    vals = {
                        'name': self.establecimiento + "-" + self.punto_emision + "-SRI NOTA CREDITO Secuencia",
                    }
                    sequence = self.env['ir.sequence'].search([('id', '=', self.notaCredito_sequence_id.id)])
                    sequence.write(vals)
                    self.notaCredito_sequence_id = sequence.id
                    # ---------------------------------
                    # MODIFICACION DE GUIA DE REMISION
                    # ---------------------------------
                    vals = {
                        'name': self.establecimiento + "-" + self.punto_emision + "-SRI GUIA Secuencia",
                    }
                    sequence = self.env['ir.sequence'].search([('id', '=', self.guia_sequence_id.id)])
                    sequence.write(vals)
                    self.guia_sequence_id = sequence.id

                if self.type == "purchase":
                    self.code = "COM"
                    self.refund_sequence = True
                    self.default_debit_account_id = CUENTAS.property_account_payable_id.id
                    self.default_credit_account_id = CUENTAS.property_account_payable_id.id
                    if not str.__contains__(self.nombre, "COMPRA"):
                        nombre_prefijo = "COMPRA"
                    else:
                        nombre_prefijo = self.nombre
                    # --------------------------------------
                    # MODIFICACION DE LIQUIDACION DE COMPRA
                    # --------------------------------------
                    vals = {
                        'name': self.establecimiento + "-" + self.punto_emision + "-SRI LIQUIDACION COMPRA Secuencia",
                    }
                    sequence = self.env['ir.sequence'].search([('id', '=', self.liquidacionCompra_sequence_id.id)])
                    sequence.write(vals)
                    self.liquidacionCompra_sequence_id = sequence.id
                    # ----------------------------
                    # MODIFICACION DE RETENCIONES
                    # ----------------------------
                    vals = {
                        'name': self.establecimiento + "-" + self.punto_emision + "-SRI RETENCION Secuencia",
                    }
                    sequence = self.env['ir.sequence'].search([('id', '=', self.retencion_sequence_id.id)])
                    sequence.write(vals)
                    self.retencion_sequence_id = sequence.id

            if self.type == "cash":
                self.code = "CAJ"
                for cuenta in PLAN_CUENTAS:
                    if cuenta.code == CUENTAS.cash_account_code_prefix + "1":
                        cuenta_bancaria_id = cuenta.id
                        break
                self.default_debit_account_id = cuenta_bancaria_id
                self.default_credit_account_id = cuenta_bancaria_id
                if not str.__contains__(self.nombre, "CAJA"):
                    nombre_prefijo = "CAJA"
                else:
                    nombre_prefijo = self.nombre
            if self.type == "bank":
                self.code = "BCO"
                for cuenta in PLAN_CUENTAS:
                    if cuenta.code == CUENTAS.bank_account_code_prefix + "1":
                        cuenta_bancaria_id = cuenta.id
                self.default_debit_account_id = cuenta_bancaria_id
                self.default_credit_account_id = cuenta_bancaria_id
                if not str.__contains__(self.nombre, "BANCO"):
                    nombre_prefijo = "BANCO"
                else:
                    nombre_prefijo = self.nombre
            if self.type == "general":
                self.code = "GEN"
                if not str.__contains__(self.nombre, "GENERAL"):
                    nombre_prefijo = "GENERAL"
                else:
                    nombre_prefijo = self.nombre
            self.nombre = nombre_prefijo
            if nombre_prefijo:
                self.name = nombre_prefijo
                if self.establecimiento:
                    self.name = self.establecimiento + "-" + nombre_prefijo
                    if self.establecimiento:
                        self.name = self.establecimiento + "-" + self.punto_emision + "-" + nombre_prefijo
            vals = {
                'code': self.code,
                'nombre': self.nombre,
                'name': self.name

            }
            journal = self.env['account.journal'].search([('name', '=', self.name)])
            journal.write(vals)

            self.nombre_diario = self.name
        except Exception as error_message:
            print(error_message)
            pass

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    @api.constrains('sequence_id', 'refund_sequence', 'code', 'nombre', 'name')
    def save_journal(self):
        # ---------------------------------------------
        # CAMBIA EL NOMBRE DE LA SECUENCIA POR DEFECTO
        # ---------------------------------------------
        # prefix = self._get_sequence_prefix(self.code, refund=False)
        seq_name = '%s Secuencia' % self.name
        self.sequence_id.name = seq_name

        if self.type == "sale":
            # ---------------------------------------
            # CAMBIA EL NOMBRE DE LAS SECUENCIAS VTA
            # ---------------------------------------
            if self.sequence_id:
                sequence = self.env['ir.sequence'].search([('name', '=', self.sequence_id.name)])
                vals = {
                    'prefix': "VTA/" + self.establecimiento + "-" + self.punto_emision + "/%(range_y)s/"
                }
                sequence.write(vals)
            # ---------------------------------------
            # CAMBIA EL NOMBRE DE LAS SECUENCIAS NCV
            # ---------------------------------------
            if self.refund_sequence_id:
                ref_seq_name = '%s Secuencia' % self.name.replace(self.nombre, self.nombre + " NC")
                self.refund_sequence_id.name = ref_seq_name
                sequence = self.env['ir.sequence'].search([('name', '=', self.refund_sequence_id.name)])
                vals = {
                    'prefix': "NCV/" + self.establecimiento + "-" + self.punto_emision + "/%(range_y)s/"
                }
                sequence.write(vals)
                self.refund_sequence_id = sequence.id
            if self.refund_sequence is True:
                pass

            # -------------------------------------------
            # CREA O MODIFICA LA SECUENCIA DE LA FACTURA
            # -------------------------------------------
            if self.factura_sequence_id.name is False:
                vals = {
                    'name': self.establecimiento + "-" + self.punto_emision + "-SRI FACTURA Secuencia",
                    'implementation': 'standard',
                    'prefix': "FV-" + self.establecimiento + "-" + self.punto_emision + "-",
                    'padding': 9,
                    'number_increment': 1,
                    'use_date_range': True,
                    'documento_preImpreso': True
                }
                seq = self.env['ir.sequence'].create(vals)
                self.factura_sequence_id = seq.id
                # noinspection PyProtectedMember
                seq._create_date_range_seq(date.today())

            # ----------------------------------------
            # CREA LA SECUENCIA DE LA NOTA DE CREDITO
            # ----------------------------------------
            if self.notaCredito_sequence_id.name is False:
                vals = {
                    'name': self.establecimiento + "-" + self.punto_emision + "-SRI NOTA CREDITO Secuencia",
                    'implementation': 'standard',
                    'prefix': "NC-" + self.establecimiento + "-" + self.punto_emision + "-",
                    'padding': 9,
                    'number_increment': 1,
                    'use_date_range': True,
                    'documento_preImpreso': True
                }
                seq = self.env['ir.sequence'].create(vals)
                self.notaCredito_sequence_id = seq.id
                # noinspection PyProtectedMember
                seq._create_date_range_seq(date.today())
            # -----------------------------------------
            # CREA LA SECUENCIA DE LA GUIA DE REMISION
            # -----------------------------------------
            if self.guia_sequence_id.name is False:
                vals = {
                    'name': self.establecimiento + "-" + self.punto_emision + "-SRI GUIA REMISION Secuencia",
                    'implementation': 'standard',
                    'prefix': "GR-" + self.establecimiento + "-" + self.punto_emision + "-",
                    'padding': 9,
                    'number_increment': 1,
                    'use_date_range': True,
                    'documento_preImpreso': True
                }
                seq = self.env['ir.sequence'].create(vals)
                self.guia_sequence_id = seq.id
                # noinspection PyProtectedMember
                seq._create_date_range_seq(date.today())

        if self.type == "purchase":
            # ---------------------------------------
            # CAMBIA EL NOMBRE DE LAS SECUENCIAS COM
            # ---------------------------------------
            if self.sequence_id:
                sequence = self.env['ir.sequence'].search([('name', '=', self.sequence_id.name)])
                vals = {
                    'prefix': "COM/" + self.establecimiento + "-" + self.punto_emision + "/%(range_y)s/"
                }
                sequence.write(vals)
            # ---------------------------------------
            # CAMBIA EL NOMBRE DE LAS SECUENCIAS NCC
            # ---------------------------------------
            if self.refund_sequence_id:
                ref_seq_name = '%s Secuencia' % self.name.replace(self.nombre, self.nombre + " NC")
                self.refund_sequence_id.name = ref_seq_name
                sequence = self.env['ir.sequence'].search([('name', '=', self.refund_sequence_id.name)])
                vals = {
                    'prefix': "NCC/" + self.establecimiento + "-" + self.punto_emision + "/%(range_y)s/"
                }
                sequence.write(vals)
                self.refund_sequence_id = sequence.id
            if self.refund_sequence is True:
                pass

            # ----------------------------------------------
            # CREA LA SECUENCIA DE LA LIQUIDACION DE COMPRA
            # ----------------------------------------------
            if self.liquidacionCompra_sequence_id.name is False:
                vals = {
                    'name': self.establecimiento + "-" + self.punto_emision + "-SRI LIQUIDACION COMPRA Secuencia",
                    'implementation': 'standard',
                    'prefix': "LC-" + self.establecimiento + "-" + self.punto_emision + "-",
                    'padding': 9,
                    'number_increment': 1,
                    'use_date_range': True,
                    'documento_preImpreso': True
                }
                seq = self.env['ir.sequence'].create(vals)
                self.liquidacionCompra_sequence_id = seq.id
                # noinspection PyProtectedMember
                seq._create_date_range_seq(date.today())
            # ----------------------------------
            # CREA LA SECUENCIA DE LA RETENCION
            # ----------------------------------
            if self.retencion_sequence_id.name is False:
                vals = {
                    'name': self.establecimiento + "-" + self.punto_emision + "-SRI RETENCION Secuencia",
                    'implementation': 'standard',
                    'prefix': "CR-" + self.establecimiento + "-" + self.punto_emision + "-",
                    'padding': 9,
                    'number_increment': 1,
                    'use_date_range': True,
                    'documento_preImpreso': True
                }
                seq = self.env['ir.sequence'].create(vals)
                self.retencion_sequence_id = seq.id
                # noinspection PyProtectedMember
                seq._create_date_range_seq(date.today())

        if self.type == "general":
            # ---------------------------------------
            # CAMBIA EL NOMBRE DE LAS SECUENCIAS GEN
            # ---------------------------------------
            if self.sequence_id:
                sequence = self.env['ir.sequence'].search([('name', '=', self.sequence_id.name)])
                vals = {
                    'prefix': "GEN/" + self.establecimiento + "-" + self.punto_emision + "/%(range_y)s/"
                }
                sequence.write(vals)

        if self.type == "bank":
            # -------------------------------------------------------
            # CAMBIA LOS NOMBRES DE LA SECUENCIAS CUST, SUPP & TRANS
            # REALIZA EL CAMBIO SOLO UNA VEZ
            # -------------------------------------------------------
            SEQUENCES = self.env['ir.sequence'].search([])
            for sequence in SEQUENCES:
                if str.__contains__(sequence.prefix, "CUST.OUT"):
                    sequence.prefix = "COBRO.NCV/%(range_year)s/"
                    sequence.name = "COBRO NCV Secuencia"
                if str.__contains__(sequence.prefix, "CUST.IN"):
                    sequence.prefix = "COBRO.VTA/%(range_year)s/"
                    sequence.name = "COBRO VTA Secuencia"
                if str.__contains__(sequence.prefix, "SUPP.IN"):
                    sequence.prefix = "PAGO.NCC/%(range_year)s/"
                    sequence.name = "PAGO NCC Secuencia"
                if str.__contains__(sequence.prefix, "SUPP.OUT"):
                    sequence.prefix = "PAGO.COM/%(range_year)s/"
                    sequence.name = "PAGO COM Secuencia"
                if str.__contains__(sequence.prefix, "TRANS"):
                    sequence.name = "TRANSFERENCIA Secuencia"
                if sequence.prefix == "A":
                    sequence.name = "CONCILIACION CUENTAS Secuencia"

        # ----------------------------------------------
        # MODIFICA LOS NOMBRES DE LA SECUENCIAS DEL SRI
        # ----------------------------------------------
        if self.liquidacionCompra_sequence_id:
            sequence = self.env['ir.sequence'].search([('id', '=', self.liquidacionCompra_sequence_id.id)])
            vals = {
                'prefix': "LC-" + self.establecimiento + "-" + self.punto_emision + "-"
            }
            sequence.write(vals)
            self.liquidacionCompra_sequence_id = sequence.id
        if self.retencion_sequence_id:
            sequence = self.env['ir.sequence'].search([('id', '=', self.retencion_sequence_id.id)])
            vals = {
                'prefix': "CR-" + self.establecimiento + "-" + self.punto_emision + "-"
            }
            sequence.write(vals)
            self.retencion_sequence_id = sequence.id
        if self.factura_sequence_id:
            sequence = self.env['ir.sequence'].search([('id', '=', self.factura_sequence_id.id)])
            vals = {
                'prefix': "FV-" + self.establecimiento + "-" + self.punto_emision + "-"
            }
            sequence.write(vals)
            self.factura_sequence_id = sequence.id
        if self.notaCredito_sequence_id:
            sequence = self.env['ir.sequence'].search([('id', '=', self.notaCredito_sequence_id.id)])
            vals = {
                'prefix': "NC-" + self.establecimiento + "-" + self.punto_emision + "-"
            }
            sequence.write(vals)
            self.notaCredito_sequence_id = sequence.id
        if self.guia_sequence_id:
            sequence = self.env['ir.sequence'].search([('id', '=', self.guia_sequence_id.id)])
            vals = {
                'prefix': "GR-" + self.establecimiento + "-" + self.punto_emision + "-"
            }
            sequence.write(vals)
            self.guia_sequence_id = sequence.id

        self.nombre_diario = self.name

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.onchange(
        'liquidacionCompra_electronica',
        'retencion_electronica',
        'factura_electronica',
        'notaCredito_electronica',
        'guia_electronica',
        'factura_sequence_number_next',
        'notaCredito_sequence_number_next',
        'guia_sequence_number_next',
        'liquidacionCompra_sequence_number_next',
        'retencion_sequence_number_next',
    )
    def _get_documentos_tributarios(self):
        # ----------------------------------------------------------------
        # CONTROLA EL INGRESO DE INFORMACION DE LA FACTURACION TRIBUTARIA
        # ----------------------------------------------------------------
        if self.type == "sale":
            # -------
            # VENTAS
            # -------
            if self.factura_electronica is True or self.notaCredito_electronica is True or self.guia_electronica is True:
                self.company_facturacion_electronica = "SI"
            elif self.factura_electronica is False and self.notaCredito_electronica is False and self.guia_electronica is False:
                self.company_facturacion_electronica = "NO"

            if self.factura_electronica is True:
                sequence = self.env['ir.sequence'].search([('id', '=', self.factura_sequence_id.id)])
                sequence.documento_preImpreso = False
                sequence.use_date_range = False
                vals = {
                    'documento_preImpreso': sequence.documento_preImpreso,
                    'use_date_range': sequence.use_date_range,
                    'number_next_actual': self.factura_sequence_number_next,
                }
                sequence.write(vals)
            elif self.factura_electronica is False:
                if self.factura_sequence_id:
                    sequence = self.env['ir.sequence'].search([('id', '=', self.factura_sequence_id.id)])
                    sequence.documento_preImpreso = True
                    sequence.use_date_range = True
                    vals = {
                        'documento_preImpreso': sequence.documento_preImpreso,
                        'use_date_range': sequence.use_date_range,
                        'number_next_actual': self.factura_sequence_number_next,
                    }
                    sequence.write(vals)
                    if sequence.date_range_ids:
                        for date in sequence.date_range_ids:
                            date.number_next_actual = self.factura_sequence_number_next
                            vals = {
                                'number_next_actual': self.factura_sequence_number_next,
                            }
                            date.write(vals)

            if self.notaCredito_electronica is True:
                sequence = self.env['ir.sequence'].search([('id', '=', self.notaCredito_sequence_id.id)])
                sequence.documento_preImpreso = False
                sequence.use_date_range = False
                vals = {
                    'documento_preImpreso': sequence.documento_preImpreso,
                    'use_date_range': sequence.use_date_range,
                    'number_next_actual': self.notaCredito_sequence_number_next,
                }
                sequence.write(vals)
            elif self.notaCredito_electronica is False:
                if self.notaCredito_sequence_id:
                    sequence = self.env['ir.sequence'].search([('id', '=', self.notaCredito_sequence_id.id)])
                    sequence.documento_preImpreso = True
                    sequence.use_date_range = True
                    vals = {
                        'documento_preImpreso': sequence.documento_preImpreso,
                        'use_date_range': sequence.use_date_range,
                        'number_next_actual': self.notaCredito_sequence_number_next,
                    }
                    sequence.write(vals)
                    if sequence.date_range_ids:
                        for date in sequence.date_range_ids:
                            date.number_next_actual = self.notaCredito_sequence_number_next
                            vals = {
                                'number_next_actual': self.notaCredito_sequence_number_next,
                            }
                            date.write(vals)

            if self.guia_electronica is True:
                sequence = self.env['ir.sequence'].search([('id', '=', self.guia_sequence_id.id)])
                sequence.documento_preImpreso = False
                sequence.use_date_range = False
                vals = {
                    'documento_preImpreso': sequence.documento_preImpreso,
                    'use_date_range': sequence.use_date_range,
                    'number_next_actual': self.guia_sequence_number_next,
                }
                sequence.write(vals)
            elif self.guia_electronica is False:
                if self.guia_sequence_id:
                    sequence = self.env['ir.sequence'].search([('id', '=', self.guia_sequence_id.id)])
                    sequence.documento_preImpreso = True
                    sequence.use_date_range = True
                    vals = {
                        'documento_preImpreso': sequence.documento_preImpreso,
                        'use_date_range': sequence.use_date_range,
                        'number_next_actual': self.guia_sequence_number_next,
                    }
                    sequence.write(vals)
                    if sequence.date_range_ids:
                        for date in sequence.date_range_ids:
                            date.number_next_actual = self.guia_sequence_number_next
                            vals = {
                                'number_next_actual': self.guia_sequence_number_next,
                            }
                            date.write(vals)

        if self.type == "purchase":
            # --------
            # COMPRAS
            # --------
            if self.liquidacionCompra_electronica is True or self.retencion_electronica is True:
                self.company_facturacion_electronica = "SI"
            elif self.liquidacionCompra_electronica is False and self.retencion_electronica is False:
                self.company_facturacion_electronica = "NO"

            if self.liquidacionCompra_electronica is True:
                sequence = self.env['ir.sequence'].search([('id', '=', self.liquidacionCompra_sequence_id.id)])
                sequence.documento_preImpreso = False
                sequence.use_date_range = False
                vals = {
                    'documento_preImpreso': sequence.documento_preImpreso,
                    'use_date_range': sequence.use_date_range,
                    'number_next_actual': self.liquidacionCompra_sequence_number_next,
                }
                sequence.write(vals)
            elif self.liquidacionCompra_electronica is False:
                if self.liquidacionCompra_sequence_id:
                    sequence = self.env['ir.sequence'].search([('id', '=', self.liquidacionCompra_sequence_id.id)])
                    sequence.documento_preImpreso = True
                    sequence.use_date_range = True
                    vals = {
                        'documento_preImpreso': sequence.documento_preImpreso,
                        'use_date_range': sequence.use_date_range,
                        'number_next_actual': self.liquidacionCompra_sequence_number_next,
                    }
                    sequence.write(vals)
                    if sequence.date_range_ids:
                        for date in sequence.date_range_ids:
                            date.number_next_actual = self.liquidacionCompra_sequence_number_next
                            vals = {
                                'number_next_actual': self.liquidacionCompra_sequence_number_next,
                            }
                            date.write(vals)

            if self.retencion_electronica is True:
                sequence = self.env['ir.sequence'].search([('id', '=', self.retencion_sequence_id.id)])
                sequence.documento_preImpreso = False
                sequence.use_date_range = False
                vals = {
                    'documento_preImpreso': sequence.documento_preImpreso,
                    'use_date_range': sequence.use_date_range,
                    'number_next_actual': self.retencion_sequence_number_next,
                }
                sequence.write(vals)
            else:
                if self.retencion_sequence_id:
                    sequence = self.env['ir.sequence'].search([('id', '=', self.retencion_sequence_id.id)])
                    sequence.documento_preImpreso = True
                    sequence.use_date_range = True
                    vals = {
                        'documento_preImpreso': sequence.documento_preImpreso,
                        'use_date_range': sequence.use_date_range,
                        'number_next_actual': self.retencion_sequence_number_next,
                    }
                    sequence.write(vals)
                    if sequence.date_range_ids:
                        for date in sequence.date_range_ids:
                            date.number_next_actual = self.retencion_sequence_number_next
                            vals = {
                                'number_next_actual': self.retencion_sequence_number_next,
                            }
                            date.write(vals)
        # ---------------------------------------------------------------------------
        # FACTURACION ELECTRONICA CUANDO SE ACTIVA O DESACTIVA UN FORMULARIO DEL SRI
        # ACTUALIZA company_facturacion_electronica EN LOS DIARIOS Y EN LA COMPAÑIA
        # ULTIMO CAMBIO 25/10/2019 JEEJ
        # ---------------------------------------------------------------------------
        JOURNALS = self.env['account.journal'].search([])
        respuesta = 'NO'
        if self.factura_electronica or self.notaCredito_electronica or self.guia_electronica or self.liquidacionCompra_electronica or self.retencion_electronica:
            respuesta = 'SI'
        else:
            for journal in JOURNALS:
                if self.name != journal.name:
                    if journal.factura_electronica:
                        respuesta = 'SI'
                    if journal.notaCredito_electronica:
                        respuesta = 'SI'
                    if journal.guia_electronica:
                        respuesta = 'SI'
                    if journal.liquidacionCompra_electronica:
                        respuesta = 'SI'
                    if journal.retencion_electronica:
                        respuesta = 'SI'
        self.company_facturacion_electronica = respuesta
        vals = {'company_facturacion_electronica': respuesta}
        company = self.env['res.company'].search([('id', '=', self.company_id.id)])
        company.write(vals)
        for journal in JOURNALS:
            journal.write(vals)


# ----------------------------------------------------------------------------------------------------------------------
#  OOO  OOOOO    OOOOO OOOOO OOOOO O   O OOOOO O   O OOOOO OOOOO
#   O   O   O    O     O     O   O O   O O     OO  O O     O
#   O   OOOOO    OOOOO OOO   O O O O   O OOO   O O O O     OOO
#   O   O  O         O O     O  OO O   O O     O  OO O     O
#  OOO  O   O    OOOOO OOOOO OOOOO OOOOO OOOOO O   O OOOOO OOOOO
# ----------------------------------------------------------------------------------------------------------------------
class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    subTitulo = fields.Char(
        string="DOCUMENTOS SRI",
        required=False,
        readonly=True,
        copy=True,
        help="Información para la generación de documentos tributarios como: facturas, retenciones, etc"
    )

    documento_preImpreso = fields.Boolean(
        string='Pre-Impresos: Autorización SRI',
        help="Marque esta casilla si desea imprimir documentos pre-impresos para esta secuencia",
        default=False
    )

    numero_autorizacion = fields.Char(string="Número Autorización", required=True, store=True, default="0000000000",
                                      size=10)
    numero_desde = fields.Integer(string='Número Desde', required=True, store=True, default=1)
    numero_hasta = fields.Integer(string='Número Hasta', required=True, store=True, default=1)

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.onchange('number_next_actual', 'date_range_ids')
    def _sequence_modification(self):
        # -----------------------------------------------------------------
        # ACTUALIZA LOS DATOS EN account.journal DE LOS SIGUIENTES CAMPOS:
        # factura_sequence_number_next
        # notaCredito_sequence_number_next
        # guia_sequence_number_next
        # liquidacionCompra_sequence_number_next
        # retencion_sequence_number_next
        # -----------------------------------------------------------------
        if not self.use_date_range:
            JOURNALS = self.env['account.journal'].search([])
            for journal in JOURNALS:
                if journal.factura_sequence_id.name == self.name:
                    journal.factura_sequence_number_next = self.number_next_actual
                    vals = {
                        'factura_sequence_number_next': self.number_next_actual,
                    }
                    journal.write(vals)
                if journal.notaCredito_sequence_id.name == self.name:
                    journal.notaCredito_sequence_number_next = self.number_next_actual
                    vals = {
                        'notaCredito_sequence_number_next': self.number_next_actual,
                    }
                    journal.write(vals)
                if journal.guia_sequence_id.name == self.name:
                    journal.guia_sequence_number_next = self.number_next_actual
                    vals = {
                        'guia_sequence_number_next': self.number_next_actual,
                    }
                    journal.write(vals)
                if journal.liquidacionCompra_sequence_id.name == self.name:
                    journal.liquidacionCompra_sequence_number_next = self.number_next_actual
                    vals = {
                        'liquidacionCompra_sequence_number_next': self.number_next_actual,
                    }
                    journal.write(vals)
                if journal.retencion_sequence_id.name == self.name:
                    journal.retencion_sequence_number_next = self.number_next_actual
                    vals = {
                        'retencion_sequence_number_next': self.number_next_actual,
                    }
                    journal.write(vals)
        elif self.use_date_range:
            JOURNALS = self.env['account.journal'].search([])
            for journal in JOURNALS:
                if journal.factura_sequence_id:
                    if journal.factura_sequence_id.name == self.name:
                        for date in self.date_range_ids:
                            vals = {
                                'factura_sequence_number_next': date.number_next_actual,
                            }
                            journal.write(vals)
                if journal.notaCredito_sequence_id:
                    if journal.notaCredito_sequence_id.name == self.name:
                        for date in self.date_range_ids:
                            vals = {
                                'notaCredito_sequence_number_next': date.number_next_actual,
                            }
                            journal.write(vals)
                if journal.guia_sequence_id:
                    if journal.guia_sequence_id.name == self.name:
                        for date in self.date_range_ids:
                            vals = {
                                'guia_sequence_number_next': date.number_next_actual,
                            }
                            journal.write(vals)
                if journal.liquidacionCompra_sequence_id:
                    if journal.liquidacionCompra_sequence_id.name == self.name:
                        for date in self.date_range_ids:
                            vals = {
                                'liquidacionCompra_sequence_number_next': date.number_next_actual,
                            }
                            journal.write(vals)
                if journal.retencion_sequence_id:
                    if journal.retencion_sequence_id.name == self.name:
                        for date in self.date_range_ids:
                            vals = {
                                'retencion_sequence_number_next': date.number_next_actual,
                            }
                            journal.write(vals)


# ----------------------------------------------------------------------------------------------------------------------
# O   O OOOOO OOOOO OOOOO   O   OOOOO OOOOO    OOOOO OOOOO O   O
# OO OO O     O     O      O O  O     O        O   O O   O  O O
# O O O OOO   OOOOO OOOOO O   O OOOOO OOO      OOOO  O   O   O
# O   O O         O     O OOOOO O   O O        O   O O   O  O O
# O   O OOOOO OOOOO OOOOO O   O OOOOO OOOOO    OOOOO OOOOO O   O
# ----------------------------------------------------------------------------------------------------------------------
class message_box(models.TransientModel):
    _name = 'message_box'
    _description = "Message wizard to display messages"

    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    message = fields.Char(default=get_default)

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # –––––––––––––––––––––––––––––––––––––––––––––––––––––– @api ––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @api.multi
    def continuar(self):
        pass
