# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp.exceptions import ValidationError
import requests
import json

class res_users_extend(osv.osv):
    _inherit = 'res.users'

    #TODO:2016-10-14 09:23:06 zhaoli 目的：使pwd也能存储，方便小泥人调用
    def _set_password(self, cr, uid, id, password, context=None):
        """ Encrypts then stores the provided plaintext password for the user
        ``id``
        """
        encrypted = self._crypt_context(cr, uid, id, context=context).encrypt(password)
        self._set_encrypted_password(cr, uid, id,password, encrypted, context=context)

    def _set_encrypted_password(self, cr, uid, id,password, encrypted, context=None):
        """ Store the provided encrypted password to the database, and clears
        any plaintext password

        :param uid: id of the current user
        :param id: id of the user on which the password should be set
        """
        cr.execute(
            "UPDATE res_users SET password=%s, password_crypt=%s WHERE id=%s",
            (password,encrypted, id))

    def create(self, cr, uid, vals, context=None):
        user_id = super(res_users_extend, self).create(cr, uid, vals, context=context)
        user = self.browse(cr, uid, user_id, context=context)
        user.partner_id.active = user.active
        if user.partner_id.company_id:
            user.partner_id.write({'company_id': user.company_id.id})
        #TODO：保存到其他服务器
        url='http://114.215.102.95:8093/Account/Register'
        paras={
            'dbname':cr.dbname,
            'name':user.login,
            'pwd':''
        }
        headers = {'content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(paras), headers=headers)
        jsonData = response.json()
        if not jsonData['isSuccess']:
            raise ValidationError(jsonData['tip'])
        #end
        return user_id

    #TODO:ModifyPwdToOdoo(string dbName, string loginName, string pwd)