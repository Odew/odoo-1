from openerp.osv import fields, osv

class product_config_settings(osv.osv_memory):
    _inherit = 'base.config.settings'
    _columns = {
        'group_product_variant': fields.boolean('Manage Product Variants', 
            help='Work with product variant allows you to define some variant of the same products, an ease the product management in the ecommerce for example',
            implied_group='product.group_product_variant'),
    }
