# -*- coding: utf-8 -*-
from openerp import models, fields, api


class ExtendResPartner(models.Model):
    _inherit = "res.partner"

    product_list = fields.One2many('qm.product.list', 'product_id', "产品列表")


LEVEL = [
    ('stepped', '加强'),
    ('normal', '正常'),
    ('relax', '放宽'),
    ('stop', '暂停'),
]


class ProductList(models.Model):
    _name = "qm.product.list"
    product_id = fields.Many2one('res.partner')
    # 产品关联信息
    product_name = fields.Many2one('product.template', "产品名称", required=True)
    product_num = fields.Char(related='product_name.product_num', string='产品编号')
    importance_category = fields.Selection(related='product_name.importance_category', string='重要度')
    # 自定义信息
    test_mode = fields.Selection(LEVEL, string="检验严格度")
    trans_score = fields.Integer(string="转移得分")
    ac_score = fields.Integer(string="接收得分")


class ResPartnerKid(models.Model):
    _name = "res.partner.kid"

    name = fields.Integer("id")
    test = fields.Char("测试")
    test2 = fields.Char("测试2")
