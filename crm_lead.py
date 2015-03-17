from openerp.osv import fields, osv 

class crm_lead(osv.osv):
    _inherit="crm.lead"
    _description="miz module"
    _defaults={}
    _columns={
              "department":fields.char("Department"),
              } 