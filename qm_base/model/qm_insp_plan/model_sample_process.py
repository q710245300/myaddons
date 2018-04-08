# -*- coding: utf-8 -*-
from openerp import models, fields, api


class qm_sample_process(models.Model):
    _name = "qm.sample_process"
    name = fields.Char(string=' 采样过程')
    sample_type = fields.Selection([('fixed_sample', '固定采样'),
                                    ('complete_inspection', '100%检验'),
                                    ('use_sample_scheme', '使用采样方案'),
                                    ('percentage_inspection', '百分率检验')],
                                   '采样类型')
    evaluation_mode = fields.Selection([('bad_num_evaluation', '按照不良数评估'),
                                        ('defect_evaluation', '按照缺陷评估'),
                                        ('manual_evaluation', '手工评估')],
                                       '评估模式')
    sample_quantity = fields.Integer(string='采样数量')
    sample_plan_id = fields.Many2one('qm.sample_plan', string='采样方案')
    sample_percentage = fields.Float(string='采样百分率')
    creater = fields.Many2one('res.users', string='创建人')
    create_time = fields.Datetime(string='创建时间', default=fields.Date.today())
