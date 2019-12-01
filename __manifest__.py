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
    'depends': ['base','purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/cierre.xml',
        #'views/templates.xml',
        #'views/purchase_order.xml',
        #'views/product.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}