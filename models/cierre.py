# -*- coding: utf-8 -*-
 
import pytz 
from openerp import fields
from datetime import datetime
from datetime import timedelta  
from pytz import timezone 
from openerp import fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp import models, fields, api
from openerp.exceptions import Warning
import time
import yaml
import json


class cierre(models.Model):


    @api.model
    def _get_name(self):
        return str(self.env['res.users'].browse(self.env.uid).name + " " + str(fields.Date.today()) )

    _inherit = 'mail.thread'
    _name = 'cierre'
    state = fields.Selection ([('nuevo','Nuevo'), ('en_proceso','En proceso'), ('esperando_revision','Esperando Revision'),('revisado','Revisado')], string='state', default='nuevo', readonly=True)
    name = fields.Char(string='Name', default=_get_name, readonly=True, copy=False)
    fecha = fields.Date(string='Fecha', readonly=True)
    tipo = fields.Selection ([('regular','Regular'), ('caja_chica','Caja Chica')], required=True, string='Tipo')
    mostrar_boton_facturar = fields.Boolean(string = "Mostrar Boton Facturar", default=False)
    cajero = fields.Char(string="Cajero", readonly=True, store=True )
    revisado = fields.Char(string="Revisado por :", readonly=True, store=True, default="Nadie")
    factura_ids = fields.One2many(comodel_name='purchase.order', inverse_name='cierre_id', string="Facturas", readonly=True)
    ingreso_ids = fields.One2many(comodel_name='ingreso', inverse_name='cierre_id', string="Ingresos de Dinero")
    salida_ids = fields.One2many(comodel_name='salida',inverse_name='cierre_id', string="Salidas de Dinero")
    compra_ids = fields.One2many(comodel_name='compra',inverse_name='cierre_id', string="Compras Ventana")
    inventario_ids = fields.One2many(comodel_name='inventario',inverse_name='cierre_id', string="Inventario")
    dinero_ids = fields.One2many(comodel_name='dinero',inverse_name='cierre_id', string="Dinero Retorno")
    total_dinero_ingreso = fields.Float(compute='action_dinero_ingreso', store=True, string="TOTAL")
    dinero_ingreso_caja = fields.Float(compute='action_dinero_ingreso', store=True, string="Dinero Caja")
    dinero_ingreso_bns = fields.Float(compute='action_dinero_ingreso', store=True, string="Dinero BNS")
    dinero_ingreso_ventas = fields.Float(compute='action_dinero_ingreso', store=True, string="Dinero Ventas")
    dinero_salida = fields.Float(compute='action_dinero_salida', store=True, string="Salidas")
    dinero_compra_ventana = fields.Float(compute='action_dinero_salida', store=True, string="Compra Ventana")
    dinero_compra_regular = fields.Float(compute='action_dinero_salida', store=True, string="Compra Sistema")
    dinero_retorno = fields.Float(compute='action_dinero_ingreso', store=True, string="Dinero Retorno")
    dinero_salida_total = fields.Float(compute='action_dinero_salida', store=True, string="TOTAL")
    dinero_balance = fields.Float(compute='action_dinero_balance', store=True, string="BALANCE")


    @api.one
    @api.constrains('name')
    def _check_cierre(self): 
        cierres_caja_chica=self.env['cierre'].search([['state', '=', 'en_proceso'], ['tipo', '=', 'caja_chica']])
        cierres_regular=self.env['cierre'].search([['state', '=', 'en_proceso'], ['tipo', '=', 'regular']])

        if self.tipo == "caja_chica" and len(cierres_caja_chica) > 0 :    
            raise Warning ("Error: Un nuevo cierre tipo caja chica no puede ser creado ya que existe uno en proceso")
        if self.tipo == "regular" and len(cierres_regular) > 0 :    
            raise Warning ("Error: Un nuevo cierre tipo regular no puede ser creado ya que existe uno en proceso") 
    
    @api.multi
    def action_abrir_caja(self):
        self.state="en_proceso"
        self.fecha = str(fields.Date.today())
        self.cajero = self.env['res.users'].browse(self.env.uid).name

        mensaje = "<p>Cierre de caja abierto por : " + str(self.env.user.name) + " - " + datetime.now(timezone('America/Costa_Rica')).strftime("%Y-%m-%d %H:%M:%S") + "</p>"
        self.message_post(body=mensaje, content_subtype='html')

    # Dinero Ingreso
    @api.one
    @api.depends('ingreso_ids', 'dinero_ids')
    def action_dinero_ingreso(self):  
        dinero_caja= 0
        dinero_bns= 0
        dinero_ventas=0
        total=0
        for ingreso in self.ingreso_ids:
            print(ingreso.tipo_ingreso)
            total += int(ingreso.monto_ingreso)
            if  ingreso.tipo_ingreso == 'caja':
                dinero_caja += int(ingreso.monto_ingreso)
            elif ingreso.tipo_ingreso == 'bns':
                print("Ingresando BNS")
                dinero_bns += int(ingreso.monto_ingreso)
            else:
                dinero_ventas += int(ingreso.monto_ingreso)
        self.dinero_ingreso_caja= dinero_caja
        self.dinero_ingreso_bns= dinero_bns
        self.dinero_ingreso_ventas= dinero_ventas
        self.total_dinero_ingreso= total

        # Dinero Retorno
        total_dinero_retorno= 0
        for dinero in self.dinero_ids:
            total_dinero_retorno += int(dinero.total)
        self.dinero_retorno= total_dinero_retorno

    # Dinero Salidas
    @api.one
    @api.depends('salida_ids', 'compra_ids', 'factura_ids.pago_caja' )
    def action_dinero_salida(self):
        total= 0
        for salida in self.salida_ids:
            total += int(salida.monto)
        self.dinero_salida= total

        total_compra_ventanta= 0
        for compra in self.compra_ids:
            total_compra_ventanta += int(compra.monto)
        self.dinero_compra_ventana= total_compra_ventanta

        total_compra_facturas = 0
        for factura in self.factura_ids:
            total_compra_facturas    += int(factura.amount_total)
        self.dinero_compra_regular = total_compra_facturas  

        self.dinero_salida_total = total + total_compra_ventanta + total_compra_facturas     


# Revisado Por y Generar Inventario
    @api.one
    def action_revisado(self):
        # Generar Inventario
        if self.tipo == "regular":
            # Valida si los productos ya fueron ingresados en la seccion de inventario
            for i in self.compra_ids :
                validacion = 0
                producto = i.product_id.name
                for b in self.inventario_ids:
                    if b.product_id.name == i.product_id.name :
                        validacion = 1
               # Ingresa los productos en la seccion de inventarios 
                if validacion == 0 :
                # Calcula la cantidad y precio promedio de producto comprado en la ventana
                    cantidad_producto_ventana = 0
                    inversion = 0
                    for prod in self.compra_ids :
                        if prod.product_id.name == i.product_id.name:
                            cantidad_producto_ventana += prod.cantidad
                            inversion +=prod.monto
                    self.inventario_ids.create({'cierre_id': self.id, 'product_id': i.product_id.id, 'cantidad': 0, 'cantidad_compra': cantidad_producto_ventana,
                    'precio_promedio': float(inversion / cantidad_producto_ventana)})
            # Mostar Boton Facturar
            self.mostrar_boton_facturar = True
        # Warning
        if str(self.cajero) == str(self.env.user.name):
            raise Warning ("El cierre de caja no puede ser revisado por el Cajero")
        # Marca el cierre de caja como revisado
        else:
            self.state = "revisado"
            self.revisado = str(self.env.user.name)

    # Generar Inventario y Enviar cierre de caja a revision        
    @api.one
    def action_listo_para_revisar(self):

        if self.state == "en_proceso":
            self.state = "esperando_revision"

        # Generar Inventario
        if self.tipo == "regular":
            # Valida si los productos ya fueron ingresados en la seccion de inventario
            for i in self.compra_ids :
                validacion = 0
                producto = i.product_id.name
                for b in self.inventario_ids:
                    if b.product_id.name == i.product_id.name :
                        validacion = 1
               # Ingresa los productos en la seccion de inventarios 
                if validacion == 0 :
                # Calcula la cantidad y precio promedio de producto comprado en la ventana
                    cantidad_producto_ventana = 0
                    inversion = 0
                    for prod in self.compra_ids :
                        if prod.product_id.name == i.product_id.name:
                            cantidad_producto_ventana += prod.cantidad
                            inversion +=prod.monto
                    self.inventario_ids.create({'cierre_id': self.id, 'product_id': i.product_id.id, 'cantidad': 0, 'cantidad_compra': cantidad_producto_ventana,
                    'precio_promedio': float(inversion / cantidad_producto_ventana)})

        mensaje = "<p>Cierre de caja listo para revisar : " + str(self.env.user.name) + " - " + datetime.now(timezone('America/Costa_Rica')).strftime("%Y-%m-%d %H:%M:%S") + "</p>"
        self.message_post(body=mensaje, content_subtype='html')


# Generar Factura de Varios
    @api.one
    def action_facturar(self):
        # Valida que exista el proveedor compra de la ventana
        proveedor = self.env['res.partner'].search([['name', '=', 'Compra de la Ventana']])

        if not proveedor:
            proveedor = self.env['res.partner'].create({'name': 'Compra de la Ventana', 'supplier': True})
        # Crea la orden de compra
        purchase_order = self.env['purchase.order'].create({'partner_id': proveedor.id , 'location_id': 12, 'pricelist_id': 1, 'tipo_pago': 'muy'})
        # Buscar la Orden de compra de la ventana
    
        for i in self.inventario_ids:
            purchase_order.order_line.create({'product_id': i.product_id.id, 'name': i.product_id.name, 'product_qty' : i.cantidad, 'price_unit': float(i.precio_promedio),
                                              'date_planned': str(fields.Date.today()), 'product_uom': i.product_id.uom_po_id.id, 'order_id': purchase_order.id})
    
        purchase_order.button_confirm()
        purchase_order.action_quotation_paid()
        mensaje = "<p>Factura creada por : " + str(self.env.user.name) + " - " + datetime.now(timezone('America/Costa_Rica')).strftime("%Y-%m-%d %H:%M:%S") + "</p>"
        self.message_post(body=mensaje, content_subtype='html')


# Dinero Balance
    @api.one
    @api.depends('dinero_salida_total', 'dinero_retorno', 'total_dinero_ingreso')
    def action_dinero_balance(self):
        total= 0
        total += (float(self.dinero_salida_total) + float(self.dinero_retorno)) - float(self.total_dinero_ingreso)
        self.dinero_balance= total


'''
# Dinero Compra Regular / Sistema
    @api.one
    @api.depends('factura_ids', 'factura_ids_caja_chica', 'factura_ids.state', 'factura_ids_caja_chica.state', 'factura_ids_caja_regular.state', 'factura_ids_caja_chica.pago_caja', 'factura_ids_caja_regular.pago_caja', 'factura_ids.pago_caja')
    def _dinero_compra_regular(self):
      total= 0
      if str(self.tipo) == "regular" :
        for factura in self.factura_ids:
          # Calculo de compra sistema para caja regular
          if str(factura.pago) == "regular" and str(factura.pago_caja) == "pagado":     
            total += float(factura.amount_total)        
      else:
        for factura in self.factura_ids_caja_chica:
          # Calculo de compra sistema para caja regular
          if str(factura.pago) == "caja_chica" and str(factura.pago_caja) == "pagado":     
            total += float(factura.amount_total) 
      self.dinero_compra_regular= total

# Dinero Compra Ventana
    @api.one
    @api.depends('compra_ids')
    def _dinero_compra_ventana(self):
        total= 0
        for compra in self.compra_ids:
            total += int(compra.monto)
        self.dinero_compra_ventana= total



# Dinero Salidas TOTAL
    @api.one
    @api.depends('dinero_compra_ventana', 'dinero_compra_regular', 'dinero_salida')
    def _dinero_salida_total(self):
        total= self.dinero_compra_ventana + self.dinero_compra_regular + self.dinero_salida
        self.dinero_salida_total= total

# Dinero Retorno
    @api.one
    @api.depends('dinero_ids')
    def _dinero_retorno(self):
        total= 0
        for dinero in self.dinero_ids:
            total += int(dinero.total)
        self.dinero_retorno= total


'''
# Validacion para la creacion de un objeto cierre
  
'''
# Generar Factura de Varios
    @api.one
    def action_facturar(self):
        # Valida que sea un cierre regular para crear la factura
        if self.tipo == 'regular' :
            # Valida si la factura ya fue creada
            if self.factura == "False" :
                # Crea la orden de compra
                proveedor = cierres_caja_chica=self.env['res.partner'].search([['name', '=', 'Compra de la ventana']])
                purchase_order = self.env['purchase.order']
                purchase_order.create({'partner_id': proveedor.id , 'location_id': 12, 'pricelist_id': 1, 'pago': 'muy'})
                # Buscar la Orden de compra de la ventana
                compra_ventana= self.env['purchase.order'].search([('partner_id', '=', proveedor.id), ('state', '=', 'draft')])[0]
                self.factura= compra_ventana.name
                for i in self.inventario_ids:
                    print("HERE ----> " + str(float(i.cantidad)) + str(i.product_id.name))
                    compra_ventana.order_line.create({'product_id': int(i.product_id), 'product_qty' : float(i.cantidad), 'price_unit': float(i.precio_promedio), 
                    'order_id' : compra_ventana.id, 'name': str("[" + i.product_id.default_code + '] '+ i.product_id.name), 'date_planned': str(fields.Date.today())})

            else:
                raise Warning ("Error: La factura ya fue creada " + str(self.factura)) 
        else:
            raise Warning ("Error: No es posible crear la factura de ventana para un cierre tipo caja chica")

# Calculo de Inventario
    @api.one
    @api.depends('state')
    def action_inventario(self):
        # Ingresa los productos en la seccion de inventario
        cierre= self.env['cierre'].search([('state', '=', 'assigned'), ('tipo', '=', 'regular')])
        for i in cierre.compra_ids :
            existencia_producto= self.inventario_ids.search([('product_id.name', '=', str(i.product_id.name))])
            if len(existencia_producto) == 0 :
                # Calcula la cantidad y precio promedio de producto comprado en la ventana
                cantidad_producto_ventana = 0
                inversion = 0
                for prod in self.compra_ids :
                    if prod.product_id.name == i.product_id.name:
                        cantidad_producto_ventana += prod.cantidad
                        inversion +=prod.monto

                self.inventario_ids.create({'cierre_id': self.id, 'product_id': i.product_id.id, 'cantidad': 0, 'cantidad_compra': cantidad_producto_ventana,
                'precio_promedio': float(inversion / cantidad_producto_ventana)})
'''
#--------------PURCHASE ORDER---------------
'''
class purchase_order(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    cierre_id= fields.Many2one(comodel_name='cierre', string='Cierre', readonly=True)
    cierre_id_caja_chica= fields.Many2one(comodel_name='cierre', string='Cierre Caja chica', readonly=True)
    cierre_id_caja_regular= fields.Many2one(comodel_name='cierre', string='Cierre Caja chica', readonly=True)

    _defaults = {
    'pago': 'regular',
      }
'''
#--------------FIN PURCHASE ORDER---------------

#--------------GASTO---------------
'''
class gasto(models.Model):
    _name = 'gasto'
    _inherit = 'gasto'
    cierre_id = fields.Many2one(comodel_name='cierre', string='Reporte Diario', delegate=True )
'''

#-------------- Empleado Amortizable ---------------
'''
class empleado_allowance(models.Model):
    _name = 'empleado.allowance'
    _inherit = 'empleado.allowance'
    cierre_id = fields.Many2one(comodel_name='cierre', readonly=True, string='Reporte Diario' )
'''

#-------------- Cliente Allowance ---------------
'''
class cliente_allowance(models.Model):
    _name = 'cliente.allowance'
    _inherit = 'cliente.allowance'
cierre_id = fields.Many2one(comodel_name='cierre', readonly=True, string='Reporte Diario')
'''