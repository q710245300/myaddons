# -*- coding: utf-8 -*-
from openerp import models, fields, api


# 特征属性
class Attributes(models.Model):
    _name = 'qm.attributes'

    name = fields.Char("特征属性")
    type = fields.Many2one('attributes.type', string='特征分类')
    values_list = fields.One2many('attributes.values', 'attributes_id', string='特征值列表')


# 特征分类
class AttributesType(models.Model):
    _name = 'attributes.type'
    name = fields.Char("特征分类定义")


# 特征值
class AttributesValues(models.Model):
    _name = 'attributes.values'
    attributes_id = fields.Many2one('qm.attributes', string='特征分类')

    name = fields.Char("特征值")
    assess = fields.Selection([('assess_1', '已接受（合格）'), ('assess_2', '已拒绝(不合格)')], "评估")
    defects = fields.Many2one('qm.defects', string="缺陷类型")
