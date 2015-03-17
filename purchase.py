from openerp.osv import fields, osv
from openerp import api
from openerp.tools.translate import _
from openerp.tools.float_utils import float_compare
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from datetime import datetime
class purchase_order(osv.osv):
    _inherit = "purchase.order"
    _description = "Purchase Order"
    
    def confirm_rfq_mod(self,cr,uid,ids,context=None):
        
        pricelist_partnerinfo = self.pool.get('pricelist.partnerinfo')
        product_supplierinfo = self.pool.get('product.supplierinfo')
        product_pricelist_item = self.pool.get('product.pricelist.item')
        supplier = self.pool.get('res.partner')
        for purchase_order in self.browse(cr,uid,ids,context):
            for order_line in purchase_order.order_line:
                cr.execute('''
                    select name,id from product_supplierinfo where product_tmpl_id = %s
                ''' %(order_line.product_id.id))

                for supplier in cr.fetchall():
                    if supplier[0] == purchase_order.partner_id.id:
                        if order_line.refresh_prices:
                            product_supplierinfo.write(cr,uid,supplier[1],{'min_qty':order_line.product_qty},context)
                            cr.execute('''
                            delete from pricelist_partnerinfo where suppinfo_id = %s
                            ''' %(supplier[1]))
                            
                            pricelist_partnerinfo.create(cr,uid,{
                                                                 'suppinfo_id':supplier[1],
                                                                 'min_quantity':order_line.product_qty,
                                                                 'price':order_line.price_unit,
                                                                 },context)
 
                        else:
                            pricelist_partnerinfo.create(cr,uid,{
                                                                 'suppinfo_id':supplier[1],
                                                                 'min_quantity':order_line.product_qty,
                                                                 'price':order_line.price_unit,
                                                                 },context)
                    # Also update the pricelist
                    for version in purchase_order.pricelist_id.version_id:
                        if version.active:
                            if version.items_id:
                                flag = 0
                                for item in version.items_id:
                                    if item.product_id == order_line.product_id:
                                        flag = 1
                                        break
                            if not version.items_id or flag == 0:
                                product_pricelist_item.create(cr,uid,{
                                                                         'product_id':order_line.product_id.id,
                                                                         'base':-2,
                                                                         'price_version_id':version.id
                                                                         },context)
        return True
    
    def _is_quotation_check(self,cr,uid,context):
        if context.get('is_quotation',False):
            return True
        else :
            return False

    @api.multi
    def _check_approval(self):
        for record in self:
            if self.manager_approval:
                return False
        return True

    _constraints = [
        (_check_approval, 'Cannot update an official document', ['incoterm_id','bid_validity',
                                                                 'minimum_planned_date','payment_term_id',
                                                                 'fiscal_position','partner_id','partner_ref',
 'pricelist_id','picking_type_id','date_order','order_line','location_id','requisition_id','invoice_method',]),
    ]
    
    def manager_approval_change(self,cr,uid,id,context):
        for i in id:
            approval = self.read(cr,uid,i,['manager_approval'],context).get('manager_approval',False)
            self.write(cr,uid,i,{'manager_approval':not approval},context)
        return True
    
    def create(self,cr,uid,vals,context):
        if context is None:
            context = {}
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order') or '/'
        if context.get('is_quotation',False):
            vals['name'] = vals['name'].replace("PO","RFQ")
            vals.update({'is_quotation':True})
        return super(purchase_order,self).create(cr,uid,vals,context)
    
    _defaults = {
                 'is_quotation':_is_quotation_check,
                 'manager_approval':False,
                 }
                
    _columns = {
                'is_quotation':fields.boolean('Is it a quotation',help="True if the document is a quotation"),
                'manager_approval':fields.boolean('Manger Approval',help="True if the document has been approved. In the true state the document will be called oficial"),
                }
class purchase_order_line(osv.osv):
    _inherit = "purchase.order.line"
    _defaults = {
                 'delay_time':0.0,
                 }
    _columns = {
                'delay_time':fields.float('Delivery Lead Time',help = "The product.supplierinfo will pick the latest value"),
                'min_qty':fields.float('Minimum Quantity'),
                }    

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', context=None):
        """
        onchange handler of product_id.Adding last transaction price functionality
        """
        if context is None:
            context = {}
 
        res = {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        if not product_id:
            return res
        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')
        res_partner = self.pool.get('res.partner')
        product_pricelist = self.pool.get('product.pricelist')
        account_fiscal_position = self.pool.get('account.fiscal.position')
        account_tax = self.pool.get('account.tax')
 
        # - check for the presence of partner_id and pricelist_id
        #if not partner_id:
        #    raise osv.except_osv(_('No Partner!'), _('Select a partner in purchase order to choose a product.'))
        #if not pricelist_id:
        #    raise osv.except_osv(_('No Pricelist !'), _('Select a price list in the purchase order form before choosing a product.'))
 
        # - determine name and notes based on product in partner lang.
        context_partner = context.copy()
        if partner_id:
            lang = res_partner.browse(cr, uid, partner_id).lang
            context_partner.update( {'lang': lang, 'partner_id': partner_id} )
        product = product_product.browse(cr, uid, product_id, context=context_partner)
        #call name_get() with partner in the context to eventually match name and description in the seller_ids field
        dummy, name = product_product.name_get(cr, uid, product_id, context=context_partner)[0]
        if product.description_purchase:
            name += '\n' + product.description_purchase
        res['value'].update({'name': name})
 
        # - set a domain on product_uom
        res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}
 
        # - check that uom and product uom belong to the same category
        product_uom_po_id = product.uom_po_id.id
        if not uom_id:
            uom_id = product_uom_po_id
 
        if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
            if context.get('purchase_uom_check') and self._check_product_uom_group(cr, uid, context=context):
                res['warning'] = {'title': _('Warning!'), 'message': _('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
            uom_id = product_uom_po_id
 
        res['value'].update({'product_uom': uom_id})
 
        # - determine product_qty and date_planned based on seller info
        if not date_order:
            date_order = fields.datetime.now()
 
        supplierinfo = False
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
        for supplier in product.seller_ids:
            if partner_id and (supplier.name.id == partner_id):
                supplierinfo = supplier
                if supplierinfo.product_uom.id != uom_id:
                    res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
                min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
                if float_compare(min_qty , qty, precision_digits=precision) == 1: # If the supplier quantity is greater than entered from user, set minimal.
                    if qty:
                        res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                    qty = min_qty
        dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        qty = qty or 1.0
        res['value'].update({'date_planned': date_planned or dt})
        if qty:
            res['value'].update({'product_qty': qty})
 
        price = price_unit
        # - determine price_unit and taxes_id
        if pricelist_id:
            cr.execute('''
            select product_pricelist_version.date_start,product_pricelist_version.date_end,product_pricelist_item.base from product_pricelist right join product_pricelist_version on product_pricelist.id=product_pricelist_version.pricelist_id right join product_pricelist_item 
            on product_pricelist_version.id = product_pricelist_item.price_version_id 
            where product_pricelist.id = %s and product_pricelist_version.active = True 
            and product_pricelist_item.product_id = %s
            '''%(pricelist_id,product_id))
            
            for j in cr.fetchall():
                if j[0] and j[1]:
                    if datetime.now() >= datetime.strptime(j[0],'%Y-%m-%d') and datetime.now() <= datetime.strptime(j[1],'%Y-%m-%d'):
                        if j[2] == -3:
                            cr.execute('''
                            select id from product_supplierinfo where product_tmpl_id=%s and name=%s
                            ''',(product_id,partner_id))
                            for l in cr.fetchall():
                                price = self.pool.get('product.supplierinfo').browse(cr,uid,l[0],context).last_transaction_price
                        else:
                            date_order_str = datetime.strptime(date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
                            price = product_pricelist.price_get(cr, uid, [pricelist_id],
                                    product.id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order_str})[pricelist_id]
        else:
            price = product.standard_price
        
        taxes = account_tax.browse(cr, uid, map(lambda x: x.id, product.supplier_taxes_id))
        fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
        taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
        res['value'].update({'price_unit': price, 'taxes_id': taxes_ids})
 
        return res

    
    @api.model
    def create(self,vals):
        obj_purchase = self.pool.get('purchase.order').browse(self._cr,self._uid,vals.get('order_id',False),self._context) 
        if obj_purchase.is_quotation:
            obj = self.pool['product.supplierinfo']
            partner_id = obj_purchase.partner_id.id
            result = obj.search(self._cr,self._uid,[('product_tmpl_id','=',vals.get('product_id',False)),('name','=',partner_id)],context=self._context)
            if not result:
                obj.create(self._cr,self._uid,{
                            'name':partner_id,
                            'product_name':vals.get('name',''),
                            'product_tmpl_id':vals.get('product_id',False)
                            },self._context)
        return super(purchase_order_line,self).create(vals)
    
class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    _description = "Pricelist"
    
    _defaults = {
                 'refresh_prices':False
                 }
    
    _columns = {
           'refresh_prices':fields.boolean('Overwrite the existing prices'),                
                }
class product_pricelist_item(osv.osv):
    _inherit = 'product.pricelist.item'
    _description = 'Adding Options to base'

    def _price_field_get(self, cr, uid, context=None):
        pt = self.pool.get('product.price.type')
        ids = pt.search(cr, uid, [], context=context)
        result = []
        for line in pt.browse(cr, uid, ids, context=context):
            result.append((line.id, line.name))

        result.append((-1, _('Other Pricelist')))
        result.append((-2, _('Supplier Prices on the product form')))
        result.append((-3, _('Last Transaction Price')))
        return result
    
 

    _columns= {
               'base':fields.selection(_price_field_get, 'Based on', required=True, size=-1, help="Base price for computation."),
               }
