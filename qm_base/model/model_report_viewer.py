# -*- coding: utf-8 -*-
from openerp import models, fields, api

class report_viewer(models.Model):
    _name = "report.viewer"
    _description = u"小泥人报表"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ Changes the view dynamically
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param context: A standard dictionary
        @return: New arch of view.
        """
        res = super(report_viewer, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        user = self.env.user
        #src = ('http://192.168.4.30:8055/Home/OdooIndex?userName=%s&amp;pwd=%s&amp;dbname=%s') %(user.login,user.password,self.env.cr.dbname)
        res['arch'] =( '''
            <form string="报表系统">
                     <script src="http://localhost:8069/web/static/src/js/echarts.min.js"></script>
                     <div id="mainChart" style="width: 600px;height:400px;"></div>
                     <div id="subChart" style="width: 600px;height:400px;"></div>
                     <script src="http://localhost:8069/web/static/src/js/spc.js"></script>
            </form>
        ''')
        return res