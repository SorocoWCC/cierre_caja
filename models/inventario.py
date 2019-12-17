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


# Calculo de diferencia entre la compra y el inventario
    @api.one
    @api.depends('cantidad')
    def action_diferencia(self):
        self.diferencia = self.cantidad - self.cantidad_compra
