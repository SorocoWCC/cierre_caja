# -*- coding: utf-8 -*-
 
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
    cajero_id= fields.Many2one(comodel_name='res.users', string='Cajero', delegate=True, readonly=True)
    _defaults = {
    'tipo': 'ventana',
    'cajero_id': lambda self, cr, uid, ctx=None: uid
    }	

class salida(models.Model):
    _name = "salida"
    detalle = fields.Char('Detalle:', size=70, required=True)
    monto = fields.Integer('Monto:', required=True)
    notas = fields.Text('Observaciones')
    cierre_id= fields.Many2one(comodel_name='cierre', string='Cierre', delegate=True)
    cajero_id= fields.Many2one(comodel_name='res.users', string='Cajero', delegate=True, readonly=True)
    _defaults = {
    'cajero_id': lambda self, cr, uid, ctx=None: uid
    }

class ingreso(models.Model):
    _name = 'ingreso'
    detalle = fields.Char(string='Detalle/Entregado Por:', required=True)
    tipo_ingreso = fields.Selection([('caja','Caja'), ('bns','BNS'),('ventas','Ventas')], string='Tipo',required=True)
    monto_ingreso = fields.Integer('Monto:', required=True, type='integer')
    cierre_id = fields.Many2one(comodel_name='cierre', string='Cierre', delegate=True)
    cajero_id= fields.Many2one(comodel_name='res.users', string='Cajero', delegate=True, readonly=True)
    _defaults = {
    'cajero_id': lambda self, cr, uid, ctx=None: uid
    }	

#------------Clase Dinero------------

class dinero(models.Model):
    _name = 'dinero'
    denominacion = fields.Selection([('1000','1000 (Mil)'), ('2000','2000 (Dos Mil)'), ('5000','5000 (Cinco Mil)'), ('10000','10000 (Diez Mil)'), ('20000','20000 (Veinte Mil)'), ('50000','50000 (Cincuenta Mil)'), ('1','Monedas'), ('500','500 (Quinientos)'), ('100','100 (Cien)'), ('50','50 (Cincuenta)'), ('25','25 (Veinticinco)'), ('10','10 (Diez)'), ('5','5 (Cinco)')], string='Denominacion', required=True)
    total = fields.Integer('Total', required=True)
    cierre_id = fields.Many2one(comodel_name='cierre', string='Cierre', delegate=True)
    cantidad = fields.Integer(compute='_retorno_dinero', store=True, string="Cantidad")
    cajero_id= fields.Many2one(comodel_name='res.users', string='Cajero', delegate=True, readonly=True)
    _defaults = {
    'cajero_id': lambda self, cr, uid, ctx=None: uid
    }	

# Cantidad Dinero
    @api.one
    @api.depends('denominacion')
    def _retorno_dinero(self):
	total= 0
	if int(self.denominacion) > 0 :
		total = self.total / int(self.denominacion)
	self.cantidad= total


#------------Fin de la Clase Dinero------------

class cierre(models.Model):
    _name = 'cierre'
    state = fields.Selection ([('new','En proceso'), ('assigned','Esperando Revision'),('lost','Revisado')], string='state', readonly=True)
    name = fields.Char(string='Name')
    fecha = fields.Char(string='Fecha', readonly=True)
    cajero = fields.Char(compute='_action_cajero', string="Cajero", readonly=True, store=True )
    cajero_id= fields.Many2one(comodel_name='res.users', string='Nuevo Cajero', delegate=True, readonly=True)
    revisado = fields.Char(string="Revisado por :", readonly=True, store=True, default="Nadie")
    factura_ids = fields.One2many(comodel_name='purchase.order', inverse_name='cierre_id', string="Facturas")
    ingreso_ids = fields.One2many(comodel_name='ingreso', inverse_name='cierre_id', string="Ingresos de Dinero")
    salida_ids = fields.One2many(comodel_name='salida',inverse_name='cierre_id', string="Salidas de Dinero")
    gasto_id = fields.One2many(comodel_name='gasto',inverse_name='cierre_id', string="Gastos")
    empleado_allowance_id = fields.One2many(comodel_name='empleado.allowance',inverse_name='cierre_id', string="Prestamos Empleados")
    cliente_amortizable_id = fields.One2many(comodel_name='cliente.amortizable',inverse_name='cierre_id', string="Prestamos Clientes")
    compra_ids = fields.One2many(comodel_name='compra',inverse_name='cierre_id', string="Compras Diarias")
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
    _defaults = {
    'state': 'new',
    'name': fields.Date.today(),
    'fecha': fields.Date.today(),
    'cajero_id': lambda self, cr, uid, ctx=None: uid	

	    }

# Nombre del cajero
    @api.one
    @api.depends('name')
    def _action_cajero(self):
	self.cajero = str(self.env.user.name)

# Dinero Compra Regular / Sistema
    @api.one
    @api.depends('factura_ids', 'factura_ids.state')
    def _dinero_compra_regular(self):
	total= 0
	for factura in self.factura_ids:
		if str(factura.pago) == "regular" and str(factura.state) == "done":	  
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
    	if len(self.env['cierre'].search([('state', '=', 'new')])) > 1 :
    		raise Warning ("Un nuevo cierre no puede ser creado ya que existe uno en proceso")

	
# Revisado Por
    @api.one
    @api.depends('state')
    def action_revisado(self):
	if str(self.state) == "new" :
		self.state = "assigned"
		return	
#    	self.revisado = str(self.env.user.name)
	if str(self.cajero) == str(self.env.user.name) and str(self.state) == "assigned" :
    		raise Warning ("El cierre de caja no puede ser revisado por el Cajero")
	else:
		self.state = "lost"
		self.revisado = str(self.env.user.name)


#--------------PURCHASE ORDER---------------

class purchase_order(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    cierre_id= fields.Many2one(comodel_name='cierre', string='Cierre', delegate=True, readonly=True)
    activator = fields.Char(compute='_action_cierre', string="Action cierre" )

# Default Cierre (Complete automaticamente el campo cierre)
    def _action_cierre(self, cr, uid, context=None):
	res = self.pool.get('cierre').search(cr, uid, [('state','=','new')], context=context)
	if len(res) > 0:
		return res[0]
	else:
    		raise Warning ("Por favor proceda a crear un cierre de caja")
    _defaults = {
    'cierre_id': _action_cierre,
    'pago': 'regular',
	    }


# Revisado Por
    @api.one
    def action_chapi(self):
	self.order_line.create({'product_id': '1', 'price_unit':'5', 'order_id' : self.id, 'name': 'Chatarra', 'date_planned': '05/06/2015'})
#--------------FIN PURCHASE ORDER---------------

#--------------GASTO---------------
class gasto(models.Model):
    _name = 'gasto'
    _inherit = 'gasto'
    cierre_id = fields.Many2one(comodel_name='cierre', readonly=True, string='Reporte Diario', delegate=True )

# Default Cierre (Complete automaticamente el campo cierre)
    def _action_cierre_gasto(self, cr, uid, context=None):
	res = self.pool.get('cierre').search(cr, uid, [('state','=','new')], context=context)
	if len(res) > 0:
		return res[0]
	else:
    		raise Warning ("Por favor proceda a crear un cierre de caja")

    _defaults = {
    'cierre_id': _action_cierre_gasto,
    }	


#-------------- Empleado Amortizable ---------------
class empleado_allowance(models.Model):
    _name = 'empleado.allowance'
    _inherit = 'empleado.allowance'
    cierre_id = fields.Many2one(comodel_name='cierre', readonly=True, string='Reporte Diario', delegate=True )

# Default Cierre (Complete automaticamente el campo cierre)
    def _action_cierre_empleado_allowance(self, cr, uid, context=None):
        res = self.pool.get('cierre').search(cr, uid, [('state','=','new')], context=context)
        if len(res) > 0:
            return res[0]
        else:
            raise Warning ("Por favor proceda a crear un cierre de caja")

    _defaults = {
    'cierre_id': _action_cierre_empleado_allowance,
    }   

#-------------- Cliente Allowance ---------------
class cliente_allowance(models.Model):
    _name = 'cliente.allowance'
    _inherit = 'cliente.allowance'
    cierre_id = fields.Many2one(comodel_name='cierre', readonly=True, string='Reporte Diario', delegate=True )

# Default Cierre (Complete automaticamente el campo cierre)
    def _action_cierre_cliente_allowance(self, cr, uid, context=None):
        res = self.pool.get('cierre').search(cr, uid, [('state','=','new')], context=context)
        if len(res) > 0:
            return res[0]
        else:
            raise Warning ("Por favor proceda a crear un cierre de caja")

    _defaults = {
    'cierre_id': _action_cierre_cliente_allowance,
    }   





