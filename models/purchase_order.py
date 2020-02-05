# -*- coding: utf-8 -*-

from odoo import models, fields, api
from openerp.exceptions import ValidationError
from odoo.exceptions import UserError
from openerp.exceptions import Warning
from openerp import models, fields, api
from datetime import datetime
from pytz import timezone 
from datetime import timedelta  
import subprocess
import time
import base64
from openerp.http import request
from odoo_pictures import IM

class purchase_order(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'

    pagado_por = fields.Char(string="Pagado por: ", readonly=True, copy=False)
    pago_caja = fields.Selection ([('pendiente','Pendiente'),('pagado','Pagado')], string='Pago', default="pendiente", readonly=True, copy=False)
    imagen_pago = fields.Binary(string="Información de pago")
    tipo_pago = fields.Selection ([('regular','Regular'), ('muy','***MUY PAGA***'), ('caja_chica','Caja Chica')], string='Metodo de Pago', required=True, default='regular')
    fecha_pago = fields.Datetime(string="Fecha Pago", readonly=True, copy=False)
    cierre_id= fields.Many2one(comodel_name='cierre', string='Cierre', readonly=True)


    # Marcar la factura como pagada y la asocia con los cierres de caja
    @api.multi
    def action_quotation_paid(self):
        # Valida si la factura fue cancelada antes de pagarla
        if str(self.state) == "cancel" :
            raise Warning ("Error: La factura fue cancelada")

        # Validar datos del cierre de caja
        if self.tipo_pago != "muy":
            self.cierre_id = self.validar_cierre(self.tipo_pago)

        self.pagado_por = self.env.user.name
        self.fecha_pago = fields.Datetime.now()
        self.pago_caja = 'pagado'

        # Ingreso Automatico de Albaranes
        stock_picking = self.env['stock.picking'].search([('state', '=', 'assigned'), ('origin', '=', self.name)])
        procesar_albaran= self.env['movement_conf'].search([('name', '=', 'Configuracion')])

        if stock_picking and procesar_albaran[0].configuracion == "activo" :
            for move in stock_picking.move_ids_without_package:
                move.quantity_done = move.product_uom_qty

            stock_picking.button_validate()
    
        
        # Fotografia de pago
        try:
            camara_caja = self.env['camara'].search([['tipo', '=', 'caja']])
            imagen_vivo = IM({"ip": camara_caja[0].ip, "user": camara_caja[0].usuario, "passwd": camara_caja[0].contrasena})
            self.imagen_pago = imagen_vivo.get_image()["image"]
        except:
            self.env.user.notify_danger(message='Error al obtener las imagenes.')
        
        # Mensaje de pago de factura
        mensaje = "<p>Factura pagada por: " + str(self.env.user.name) + " - " + str(self.fecha_pago) + "</p>"
        self.message_post(body=mensaje, content_subtype='html')
            
        # Imprimir el tiquete de caja automaticamente
        return self.env.ref('purchase_order_modifications.custom_report_tiquete_compra').report_action(self)


    def validar_cierre(self, tipo_pago):

        cierre = self.env['cierre'].search([('state', '=', 'en_proceso'), ('tipo', '=', str(self.tipo_pago))])
        # Valida que exista un cierre de caja disponible
        if cierre:
            cajero = cierre.cajero
            # Valida que solo el cajero pueda pagar facturas
            # El usuario que paga la factura no puede ser el mismo que la crea
            if cajero == str(self.env.user.name) and self.user_id.name != str(self.env.user.name):
                return cierre
            else:
                raise Warning ("Usuario no autorizado para pagar facturas") 
        else:
            raise Warning ("No existe un cierre de caja.") 
            