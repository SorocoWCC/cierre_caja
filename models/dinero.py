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


class dinero(models.Model):
    _name = 'dinero'
    denominacion = fields.Selection([('1000','1000 (Mil)'), ('2000','2000 (Dos Mil)'), ('5000','5000 (Cinco Mil)'), ('10000','10000 (Diez Mil)'), ('20000','20000 (Veinte Mil)'), ('50000','50000 (Cincuenta Mil)'), ('1','Monedas'), ('500','500 (Quinientos)'), ('100','100 (Cien)'), ('50','50 (Cincuenta)'), ('25','25 (Veinticinco)'), ('10','10 (Diez)'), ('5','5 (Cinco)')], string='Denominacion', required=True)
    total = fields.Integer('Total', required=True)
    cierre_id = fields.Many2one(comodel_name='cierre', string='Cierre', delegate=True)
    cantidad = fields.Integer(compute='_retorno_dinero', store=True, string="Cantidad")
    cajero = fields.Char(string="Cajero", readonly=True, store=True )


	# Cantidad Dinero
    @api.one
    @api.depends('denominacion')
    def _retorno_dinero(self):
        total= 0
        if int(self.denominacion) > 0 :
            total = self.total / int(self.denominacion)
        self.cantidad= total
    
    @api.one
    @api.constrains('cierre_id')
    def _check_cajero(self): 
        if self.cierre_id.cajero != self.env['res.users'].browse(self.env.uid).name:
            raise Warning ("Error: Solo el cajero puede realizar ingresos de compras Ventana.") 
