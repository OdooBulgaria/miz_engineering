from openerp.osv import fields, osv
from openerp import api
from openerp.tools.translate import _
from openerp.addons.base.res import res_partner

class res_partner(osv.osv,res_partner.format_address):
    _inherit = "res.partner"
    _description = "Partner MIZ"

    def create(self,cr,uid,vals ,context):
        pricelist_vals = {
                          'name':vals.get('name','Pricelist'),
                          'active':True,
                          'version_id':[(0,0,{'name':'Version1'})]
                          }
        
        if vals.get('customer',False):
            pricelist_vals.update({'type':'sale'})
            pricelist_id = self.pool.get('product.pricelist').create(cr,uid,pricelist_vals,context)
            vals.update({'property_product_pricelist':pricelist_id})
            
        if vals.get('supplier',False):
            pricelist_vals.update({'type':'purchase'})
            pricelist_id = self.pool.get('product.pricelist').create(cr,uid,pricelist_vals,context)
            vals.update({'property_product_pricelist_purchase':pricelist_id})
        
        return super(res_partner,self).create(cr,uid,vals,context)
    
    def _get_line_ids(self, cr, uid, ids, name, arg, context=None):
        res = {}
        list = []
        if context.get('product_id',False):
            for id in ids:
                cr.execute('''
                select sale_order_line.id from sale_order_line 
                left join sale_order on sale_order_line.order_id = sale_order.id 
                where sale_order_line.product_id = %s and sale_order.partner_id = %s; 
                 ''' %(context.get('product_id',False),id))
                for i in cr.fetchall():
                    list.append(i[0])
                res.update({id:list})
                list = []   
        return res
    
    
    def _get_invoice_line_ids(self,cr, uid, ids, name, arg, context=None):
        res = {}
        list = []
        if context.get('product_id',False):
            for id in ids:
                cr.execute('''
                select account_invoice_line.id from account_invoice_line 
                left join account_invoice on account_invoice_line.invoice_id = account_invoice.id 
                where account_invoice_line.product_id = %s and account_invoice.partner_id = %s; 
                 ''' %(context.get('product_id',False),id))
                for i in cr.fetchall():
                    list.append(i[0])
                res.update({id:list})
                list = []   
        return res    
    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context.get('miz_engineering',False):
            view_id = self.pool['ir.model.data'].get_object_reference(cr, user, 'miz_engineering', 'view_partner_simple_form_one2many')[1]
        res = super(res_partner,self).fields_view_get(cr, user, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        return res
    
    _columns = {
                'sale_order_line_ids':fields.function(_get_line_ids, method=True, type='many2many', relation='sale.order.line', string='Sale Order Lines'),
                'invoice_lines':fields.function(_get_invoice_line_ids, method=True, type='many2many', relation='account.invoice.line', string='Invoice Lines'),
                }

    