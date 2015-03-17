from openerp.osv import fields, osv
from openerp import api
from openerp.tools.translate import _

class sale_order(osv.osv):
    _inherit = "sale.order"
    _description = "Sale Order"

    def _is_quotation_check(self,cr,uid,context):
        if context.get('is_quotation',False):
            return True
        else :
            return False
        
    _defaults = {
                 'is_quotation':_is_quotation_check,
                 'manager_approval':False,
                 }
    @api.multi
    def _check_approval(self):
        for record in self:
            if self.manager_approval:
                return False
        return True

    _constraints = [
        (_check_approval, 'Cannot update an official document', ['warehouse_id','shop_id','incoterm','picking_policy','order_policy',]),
    ]

    def manager_approval_change(self,cr,uid,id,context):
        for i in id:
            approval = self.read(cr,uid,i,['manager_approval'],context).get('manager_approval',False)
            self.write(cr,uid,i,{'manager_approval':not approval},context)
        return True
    
    _columns = {
                'is_quotation':fields.boolean("Is Quotation",help = "If true then it is a quotation"),
                'manager_approval':fields.boolean("Manager Approval",help = "If true then the document has been approved by the manager"),
                'state': fields.selection([
                ('draft', 'Draft Order'),
                ('sent', 'Order Sent'),
                ('cancel', 'Cancelled'),
                ('waiting_date', 'Waiting Schedule'),
                ('progress', 'Sales Order'),
                ('manual', 'Sale to Invoice'),
                ('shipping_except', 'Shipping Exception'),
                ('invoice_except', 'Invoice Exception'),
                ('done', 'Done'),
                ], 'Status', readonly=True, copy=False, help="Gives the status of the quotation or sales order.\
                  \nThe exception status is automatically set when a cancel operation occurs \
                  in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
                   but waiting for the scheduler to run on the order date.", select=True),

                }
    
    def copy_quotation(self, cr, uid, ids, context=None):
        id = self.copy(cr, uid, ids[0], context=context)
        if context.get('is_quotation',False):
            view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'miz_engineering', 'view_order_form_rfq')
        else:
            view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'miz_engineering', 'view_saleorder_form')
        view_id = view_ref and view_ref[1] or False,
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'res_id': id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
        }
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'sale.order') or '/'
        if context.get('is_quotation',False):
            vals['name'] = vals['name'].replace("SO","SQ")
            vals.update({'is_quotation':True})
        if vals.get('partner_id') and any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id', 'fiscal_position']):
            defaults = self.onchange_partner_id(cr, uid, [], vals['partner_id'], context=context)['value']
            if not vals.get('fiscal_position') and vals.get('partner_shipping_id'):
                delivery_onchange = self.onchange_delivery_id(cr, uid, [], vals.get('company_id'), None, vals['partner_id'], vals.get('partner_shipping_id'), context=context)
                defaults.update(delivery_onchange['value'])
            vals = dict(defaults, **vals)
        ctx = dict(context or {}, mail_create_nolog=True)
        new_id = super(sale_order, self).create(cr, uid, vals, context=ctx)
        self.message_post(cr, uid, [new_id], body=_("Quotation created"), context=ctx)
        return new_id