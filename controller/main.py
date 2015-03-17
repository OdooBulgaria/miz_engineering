from openerp import http
from openerp.http import request
from openerp import SUPERUSER_ID, workflow


class miz(http.Controller):
    @http.route('/get_param', auth='public', methods = ['post'],website=True)
    def test_controller(self,**kw):
        print"==============================",kw
        print"==============================",kw["name"]
        obj_browse=request.env['res.users'].browse(SUPERUSER_ID).partner_id
        print"===================obj",obj_browse
        for j in obj_browse:
            partner=j.id
            print"email==================",partner
        print"===============================",partner
        obj = request.env['crm.lead'].create({'contact_name':kw["name"],'partner_name':kw["company"],'email_from':kw["email"],'mobile':kw["phone"],'referred':kw["here"],'description':kw["Comment"],'name':"Query from Website",'department':kw["department"]})
        obj_mail = request.env['mail.message'].create({'body':"trial mail",'subject':"Query from Website",'partner_ids':[(6,0,[partner])]})
        print"=============================ddddddddddddddddddddd"
        return request.website.render("miz_engineering.confirm_page",{})
    
    