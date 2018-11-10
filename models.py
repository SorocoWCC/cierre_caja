# -*- coding: utf-8 -*-
 
import pytz 
from openerp import fields
from datetime import date
from openerp import fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp import models, fields, api
from openerp.exceptions import Warning
import time
import yaml
import json


class compra(models.Model):
    _name = "compra"
    _description = "Compra Diaria"
    tipo = fields.Selection([('ventana','Compra Ventana')], string='Tipo de Compra', required=True)
    monto = fields.Integer('Monto:', required=True)
    notas = fields.Text('Observaciones')
    cierre_id = fields.Many2one(comodel_name='cierre', string='Cierre', delegate=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Producto', delegate=True)
    cantidad = fields.Float('Cantidad:', required=True)
    consecutivo = fields.Char('Consecutivo:')
    cajero = fields.Char(string="Cajero", readonly=True, store=True )
    _defaults = {
    'tipo': 'ventana',
    'cajero':  lambda self,cr,uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).name
    }   


class inventario(models.Model):
    _name = "inventario"
    _description = "Inventario Ventana"
    name = fields.Char(string="Name", default="Naide")
    cierre_id = fields.Many2one(comodel_name='cierre', string='Cierre', delegate=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Producto', delegate=True, readonly=True)
    cantidad = fields.Float('Cantidad Inventario:', required=True)
    diferencia = fields.Float(compute='action_diferencia', string="Diferencia", readonly=True, store=True )
    cantidad_compra = fields.Float('Cantidad Compras:', readonly=True)
    precio_promedio = fields.Float(string="Precio Promedio", readonly=True, store=True)
    cajero = fields.Char(string="Cajero", readonly=True, store=True )
    _defaults = {
    'tipo': 'ventana',
    'cajero':  lambda self,cr,uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).name
    }   


# Calculo de diferencia entre la compra y el inventario
    @api.one
    @api.depends('cantidad')
    def action_diferencia(self):
        self.diferencia = self.cantidad - self.cantidad_compra


class salida(models.Model):
    _name = "salida"
    detalle = fields.Char('Detalle:', size=70, required=True)
    monto = fields.Integer('Monto:', required=True)
    notas = fields.Text('Observaciones')
    cierre_id= fields.Many2one(comodel_name='cierre', string='Cierre', delegate=True)
    cajero = fields.Char(string="Cajero", readonly=True, store=True )
    _defaults = {
    'cajero':  lambda self,cr,uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).name
    }


class ingreso(models.Model):
    _name = 'ingreso'
    detalle = fields.Char(string='Detalle/Entregado Por:', required=True)
    tipo_ingreso = fields.Selection([('caja','Caja'), ('bns','BNS'),('ventas','Ventas')], string='Tipo',required=True)
    monto_ingreso = fields.Integer('Monto:', required=True, type='integer')
    cierre_id = fields.Many2one(comodel_name='cierre', string='Cierre', delegate=True)
    cajero = fields.Char(string="Cajero", readonly=True, store=True )
    _defaults = {
    'cajero':  lambda self,cr,uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).name
    }   

class dinero(models.Model):
    _name = 'dinero'
    denominacion = fields.Selection([('1000','1000 (Mil)'), ('2000','2000 (Dos Mil)'), ('5000','5000 (Cinco Mil)'), ('10000','10000 (Diez Mil)'), ('20000','20000 (Veinte Mil)'), ('50000','50000 (Cincuenta Mil)'), ('1','Monedas'), ('500','500 (Quinientos)'), ('100','100 (Cien)'), ('50','50 (Cincuenta)'), ('25','25 (Veinticinco)'), ('10','10 (Diez)'), ('5','5 (Cinco)')], string='Denominacion', required=True)
    total = fields.Integer('Total', required=True)
    cierre_id = fields.Many2one(comodel_name='cierre', string='Cierre', delegate=True)
    cantidad = fields.Integer(compute='_retorno_dinero', store=True, string="Cantidad")
    cajero = fields.Char(string="Cajero", readonly=True, store=True )
    _defaults = {
    'cajero':  lambda self,cr,uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).name
    }   

# Cantidad Dinero
    @api.one
    @api.depends('denominacion')
    def _retorno_dinero(self):
        total= 0
        if int(self.denominacion) > 0 :
            total = self.total / int(self.denominacion)
        self.cantidad= total

class cierre(models.Model):
    _name = 'cierre'
    state = fields.Selection ([('inicio', 'Nuevo'), ('new','En proceso'), ('assigned','Esperando Revision'),('lost','Revisado')], string='state', readonly=True)
    name = fields.Char(string='Name')
    fecha = fields.Date(string='Fecha', readonly=True)
    tipo = fields.Selection ([('regular','Regular'), ('caja_chica','Caja Chica')], string='Tipo', default='regular', required=True)
    # Convierte a reaonly el tipo de caja para evitar varios cierres abiertos al mismo tiempo
    bloqueo_tipo_cierre = fields.Char(compute='_action_bloqueo', readonly=True, string="Bloqueo")
    cajero = fields.Char(string="Cajero", readonly=True, store=True )
    revisado = fields.Char(string="Revisado por :", readonly=True, store=True, default="Nadie")
    # Agrupa todas las facturas para el reporte diario
    factura_ids = fields.One2many(comodel_name='purchase.order', inverse_name='cierre_id', string="Facturas", readonly=True)
    # Agrupa todas las facturas para el reporte diario
    factura_ids_caja_regular = fields.One2many(comodel_name='purchase.order', inverse_name='cierre_id', string="Facturas",  domain=[('pago', '=', 'regular')], readonly=True)
    # Agrupa solamente facturas de caja chica
    factura_ids_caja_chica = fields.One2many(comodel_name='purchase.order', inverse_name='cierre_id_caja_chica', string="Facturas", domain=[('pago', '=', 'caja_chica')], readonly=True)
    ingreso_ids = fields.One2many(comodel_name='ingreso', inverse_name='cierre_id', string="Ingresos de Dinero")
    salida_ids = fields.One2many(comodel_name='salida',inverse_name='cierre_id', string="Salidas de Dinero")
    gasto_id = fields.One2many(comodel_name='gasto',inverse_name='cierre_id', string="Gastos")
    empleado_allowance_id = fields.One2many(comodel_name='empleado.allowance',inverse_name='cierre_id', string="Prestamos Empleados")
    cliente_amortizable_id = fields.One2many(comodel_name='cliente.amortizable',inverse_name='cierre_id', string="Prestamos Clientes")
    compra_ids = fields.One2many(comodel_name='compra',inverse_name='cierre_id', string="Compras Diarias")
    inventario_ids = fields.One2many(comodel_name='inventario',inverse_name='cierre_id', string="Inventario")
    dinero_ids = fields.One2many(comodel_name='dinero',inverse_name='cierre_id', string="Dinero Retorno")
    dinero_ingreso = fields.Float(compute='_dinero_ingreso', store=True, string="TOTAL")
    dinero_ingreso_caja = fields.Float(compute='_dinero_ingreso_caja', store=True, string="Dinero Caja")
    dinero_ingreso_bns = fields.Float(compute='_dinero_ingreso_bns', store=True, string="Dinero BNS")
    dinero_ingreso_ventas = fields.Float(compute='_dinero_ingreso_ventas', store=True, string="Dinero Ventas")
    dinero_salida = fields.Float(compute='_dinero_salida', store=True, string="Salidas/Vales")
    dinero_compra_ventana = fields.Float(compute='_dinero_compra_ventana', store=True, string="Compra Ventana")
    dinero_compra_regular = fields.Float(compute='_dinero_compra_regular', store=True, string="Compra Sistema")
    dinero_retorno = fields.Float(compute='_dinero_retorno', store=True, string="Dinero Retorno")
    dinero_salida_total = fields.Float(compute='_dinero_salida_total', store=True, string="TOTAL")
    dinero_balance = fields.Float(compute='_dinero_balance', store=True, string="BALANCE")
    # Indica si la factura de ventana fue creada
    factura = fields.Char( string="Factura", readonly=True, store=True, default='False' ) 
    _defaults = {
    'state': 'new',
    'name': fields.Date.today(),
    'fecha': fields.Date.today(), 
    'cajero':  lambda self,cr,uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).name
        }

    # Bloqueo campo tipo cierre
    @api.one
    @api.depends('ingreso_ids')
    def _action_bloqueo(self):
        if self.dinero_ingreso > 0 :
            self.bloqueo_tipo_cierre = "bloqueado"

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

# Dinero Ingreso Total
    @api.one
    @api.depends('ingreso_ids')
    def _dinero_ingreso(self):
        total= 0
        for ingreso in self.ingreso_ids:            
            total += int(ingreso.monto_ingreso)
        self.dinero_ingreso= total

# Dinero Ingreso Caja
    @api.one
    @api.depends('ingreso_ids')
    def _dinero_ingreso_caja(self):        
      total= 0
      for ingreso in self.ingreso_ids:
        if  ingreso.tipo_ingreso == 'caja':
          total += int(ingreso.monto_ingreso)
      self.dinero_ingreso_caja= total

# Dinero Ingreso BNS
    @api.one
    @api.depends('ingreso_ids')
    def _dinero_ingreso_bns(self):
        total= 0
        for ingreso in self.ingreso_ids:
                if  ingreso.tipo_ingreso == 'bns':
                    total += int(ingreso.monto_ingreso)
        self.dinero_ingreso_bns= total

# Dinero Ingreso Ventas
    @api.one
    @api.depends('ingreso_ids')
    def _dinero_ingreso_ventas(self):
        total= 0
        for ingreso in self.ingreso_ids:
                if  ingreso.tipo_ingreso == 'ventas':
                    total += int(ingreso.monto_ingreso)
        self.dinero_ingreso_ventas= total

# Dinero Compra Ventana
    @api.one
    @api.depends('compra_ids')
    def _dinero_compra_ventana(self):
        total= 0
        for compra in self.compra_ids:
            total += int(compra.monto)
        self.dinero_compra_ventana= total

# Dinero Salidas
    @api.one
    @api.depends('salida_ids')
    def _dinero_salida(self):
        total= 0
        for salida in self.salida_ids:
            total += int(salida.monto)
        self.dinero_salida= total

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

# Dinero Balance
    @api.one
    @api.depends('dinero_salida_total', 'dinero_retorno', 'dinero_ingreso')
    def _dinero_balance(self):
        total= 0
        total += (float(self.dinero_salida_total) + float(self.dinero_retorno)) - float(self.dinero_ingreso)
        self.dinero_balance= total

# Validacion para la creacion de un objeto cierre
    @api.one
    @api.constrains('name')
    def _check_cierre(self): 
        cierres_caja_chica=self.env['cierre'].search([['state', '=', 'new'], ['tipo', '=', 'caja_chica']])
        cierres_regular=self.env['cierre'].search([['state', '=', 'new'], ['tipo', '=', 'regular']])

        if len(cierres_caja_chica) > 1 :    
            raise Warning ("Error: Un nuevo cierre tipo caja chica no puede ser creado ya que existe uno en proceso")
        if len(cierres_regular) > 1 :    
            raise Warning ("Error: Un nuevo cierre tipo regular no puede ser creado ya que existe uno en proceso")

# Revisado Por y Generar Inventario
    @api.one
    @api.depends('state')
    def action_revisado(self):
        if str(self.state) == "new" :
            self.state = "assigned"
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
            return  
        # Warning
        if str(self.cajero) == str(self.env.user.name) and str(self.state) == "assigned" :
            raise Warning ("El cierre de caja no puede ser revisado por el Cajero")
        # Marca el cierre de caja como revisado
        else:
            self.state = "lost"
            self.revisado = str(self.env.user.name)  

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
                    print "HERE ----> " + str(float(i.cantidad)) + str(i.product_id.name)
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

#--------------PURCHASE ORDER---------------

class purchase_order(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    cierre_id= fields.Many2one(comodel_name='cierre', string='Cierre', readonly=True)
    cierre_id_caja_chica= fields.Many2one(comodel_name='cierre', string='Cierre Caja chica', readonly=True)
    cierre_id_caja_regular= fields.Many2one(comodel_name='cierre', string='Cierre Caja chica', readonly=True)

    _defaults = {
    'pago': 'regular',
      }

#--------------FIN PURCHASE ORDER---------------

#--------------GASTO---------------
class gasto(models.Model):
    _name = 'gasto'
    _inherit = 'gasto'
    cierre_id = fields.Many2one(comodel_name='cierre', string='Reporte Diario', delegate=True )


#-------------- Empleado Amortizable ---------------
class empleado_allowance(models.Model):
    _name = 'empleado.allowance'
    _inherit = 'empleado.allowance'
    cierre_id = fields.Many2one(comodel_name='cierre', readonly=True, string='Reporte Diario' )


#-------------- Cliente Allowance ---------------
class cliente_allowance(models.Model):
    _name = 'cliente.allowance'
    _inherit = 'cliente.allowance'
    cierre_id = fields.Many2one(comodel_name='cierre', readonly=True, string='Reporte Diario')
 
