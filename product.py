from openerp.osv import fields, osv
from openerp import api
from openerp.tools.translate import _

class purchase_product(osv.osv):
    _inherit = "product.template"
    _description = "Adding Fields"
    
    def _customer_ids(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for id in ids:
            list = []
            cr.execute('''
            select distinct partner_id from sale_order_line 
            left join sale_order on sale_order_line.order_id = sale_order.id 
            where product_id = %s; 
             ''' %(id))
            for i in cr.fetchall():
                list.append(i[0])
            res.update({id:list})
        return res
   
    _columns = {
                'customer_id':fields.function(_customer_ids, method=True, type='many2many', relation='res.partner', string='Customers' ),
                }
 
class product_supplierinfo(osv.osv):
    _inherit = "product.supplierinfo"
    _description =  "product supllier info miz"

    _sql_constraints = [
        ('supplier_uniq', 'unique(name,product_tmpl_id)',
            'A product cannot have two same suplliers!'),
    ]
    
    def _get_last_price(self,cr,uid,ids,name,arg,context=None):
        res = {}
        for i in self.browse(cr,uid,ids,context):
            cr.execute(''' 
            select purchase_order_line.price_unit from purchase_order_line left join purchase_order on purchase_order_line.order_id = purchase_order.id where purchase_order_line.product_id = %s 
and  purchase_order.partner_id = %s and date_order = (select max(purchase_order.date_order) from purchase_order_line left join purchase_order on purchase_order_line.order_id = purchase_order.id where purchase_order_line.product_id = %s 
and  purchase_order.partner_id = %s)
            ''' %(i.product_tmpl_id.id,i.name.id,i.product_tmpl_id.id,i.name.id))
            for j in cr.fetchall():
                res.update({i.id:j[0]})
        return res
    _columns = {
                'last_transaction_price':fields.function(_get_last_price,string = "Latest Transaction Price",help = "Stores the latest transaction price of the product from the supplier")
                }
    