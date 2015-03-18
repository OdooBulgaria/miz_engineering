from openerp import http
from openerp.http import request
from openerp import SUPERUSER_ID, workflow


class miz(http.Controller):
    @http.route('/get_param', auth='public', methods = ['post'],website=True)
    def test_controller(self,**kw):
        print"==============================",kw
        print"==============================",kw["name"]
#         body="Name-:"+kw["name"]+"\n"+"Company-:"+kw["company"]+"\n"+"Email-:"+kw["email"]+"\n"+"Department-:"+kw["department"]+"\n"+"Phone-:"+kw["phone"]+"\n"+"Source-:"+kw["here"]+"\n"+"Comment-:"+kw["Comment"]
        body = '''
        <p>Name-: %s</p>
        <p>Company-: %s</p>
        <p>Email-: %s</p>
        <p>Department-: %s</p>
        <p>Phone-: %s</p>
        <p>Source-: %s</p>
         <p>Comment-: %s</p>
        ''' %(kw['name'],kw["company"],kw["email"],kw["department"],kw["phone"],kw["here"],kw["Comment"])
        print"==================bbbbbbbbbbbbb",body
        obj_browse=request.env['res.users'].browse(SUPERUSER_ID).partner_id
        print"===================obj",obj_browse
        for j in obj_browse:
            partner=j.id
            print"email==================",partner
        print"===============================",partner
        obj = request.env['crm.lead'].create({'contact_name':kw["name"],'partner_name':kw["company"],'email_from':kw["email"],'mobile':kw["phone"],'referred':kw["here"],'description':kw["Comment"],'name':"Query from Website",'department':kw["department"]})
        obj_mail = request.env['mail.message'].create({'body':body,'subject':"Query from Website",'partner_ids':[(6,0,[partner])],'author_id':False})
        obj_mail = request.env['mail.message'].create({'body':"trial mail",'subject':"Query from Website",'partner_ids':[(6,0,[partner])]})
        print"=============================ddddddddddddddddddddd"
        return request.website.render("miz_engineering.confirm_page",{})
    
    