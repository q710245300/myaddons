# -*- coding: utf-8 -*-
from openerp import models, fields, api


class qm_insp_method_def(models.Model):
    _name = "qm.insp_method_def"

    name = fields.Char(string='检验方法', required=True)
    belong_to_plant = fields.Many2one('qm.factory', string='工厂')
    insp_qualification = fields.Many2one('res.users', string='检验资格')
    brief_description = fields.Char(string='简要描述')
    refer_insp_inst = fields.Char(string='参考检验指导书')
    inspect_equipment = fields.Many2one('hr.equipment', string='检验设备')
    valid_start = fields.Boolean(string='有效')
    valid_start_date = fields.Datetime(string='有效起始日期', default=fields.Date.today())
    detailed_description = fields.Html(string='详细说明')
