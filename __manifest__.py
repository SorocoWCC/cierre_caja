# -*- coding: utf-8 -*-
{
    'name': "San Miguel - Cierre de Caja",

    'summary': """
        Cierre de Caja""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Recicladora San Miguel",
    'website': "https://www.recicladorasanmiguel.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase', 'purchase_order_modifications'],

    # always loaded
    'data': [
        'views/cierre.xml',
        'views/purchase_order.xml',
        'cierre_caja_report.xml',
        'views/report_cierre_caja.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}