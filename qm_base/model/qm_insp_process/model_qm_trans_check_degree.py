# -*- coding: utf-8 -*-
from __future__ import division
from openerp import models, fields, api


class InspectionLevel(models.Model):
    _name = 'qm.trans.check.degree'

    LEVEL = [
        ('relax', '放宽'),
        ('normal', '正常'),
        ('stepped', '加强'),
        ('stop', '暂停'),

    ]
    TRANS_STATE = [
        ('draft', '草稿'),
        ('commit', '检验员提交'),
        ('confirm', '主管确认'),
        ('approve', '质量总监审批'),
        ('refuse', '拒绝'),
        ('cancel', '取消')
    ]

    # 定义字段
    # 记录相关定量
    state = fields.Selection(TRANS_STATE, readonly=True, select=True, copy=False, string="审批状态")
    name = fields.Char("检验严格度转移确认单")

    product_name = fields.Many2one('product.template', "产品名称")
    product_num = fields.Char(related='product_name.product_num', string="产品编号")
    importance_degree = fields.Selection(related='product_name.importance_category', string="重要度")

    trans_score = fields.Integer(string="当前转移得分")
    check_degree = fields.Selection(LEVEL,string="当前检验严格度")
    inspection_order = fields.Many2one('qm.inspection.order', '关联质检单号')

    suggest_check_degree = fields.Selection(LEVEL, string="系统建议调整检验级别为（可手动调整）")
    inspector_sign = fields.Char("检验员签字：")
    inspector_time = fields.Date("签字日期：")
    charge_sign = fields.Char("主管签字：")
    charge_time = fields.Date("签字日期：")
    chief_sign = fields.Char("质量总监签字：")
    chief_time = fields.Date("签字日期：")

    # 默认值
    _defaults = {'state': lambda *args: 'draft',
                 'name': lambda self, cr, uid, context: self.pool['ir.sequence'].next_by_code(cr, uid,
                                                                                              'qm.trans.check.degree.name',
                                                                                              context=context)}
