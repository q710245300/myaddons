# -*- coding: utf-8 -*-
from __future__ import division
from openerp import models, fields, api
from openerp.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_num = fields.Char('产品编号')
    product_chart = fields.Char('产品图号')
    product_version = fields.Char("产品型号")
    importance_category = fields.Selection([('class_a', 'A(关键)'), ('class_b', 'B(重要)'), ('class_c', 'C(一般)')],
                                           '产品重要度分类', required=True)

    factory_id = fields.Many2one('qm.factory', '工厂')
    storage_location =fields.Many2one('station.product.location', string="库位")
    godown_origin = fields.Char(string="源单据（入库单）")
