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


class ingreso(models.Model):
    _name = 'ingreso'
    detalle = fields.Char(string='Detalle/Entregado Por:', required=True)
    tipo_ingreso = fields.Selection([('caja','Caja'), ('bns','BNS'),('ventas','Ventas')], string='Tipo',required=True)
    monto_ingreso = fields.Integer('Monto:', required=True, type='integer')
    cierre_id = fields.Many2one(comodel_name='cierre', string='Cierre', delegate=True)
    cajero = fields.Char(string="Cajero", readonly=True, store=True )


    @api.one
    @api.constrains('cierre_id')
    def _check_cajero(self): 
        if self.cierre_id.cajero != self.env['res.users'].browse(self.env.uid).name:
            raise Warning ("Error: Solo el cajero puede realizar ingresos de dinero.")