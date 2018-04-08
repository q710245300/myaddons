# -*- coding: utf-8 -*-
from openerp import models, fields, api


# 工厂
class Factory(models.Model):
    _name = 'qm.factory'

    name = fields.Char("工厂名称")
    code = fields.Char("工厂代码")


# 生产线
class ProductLine(models.Model):
    _name = 'qm.pro.line'

    name = fields.Char("生产线")
    num = fields.Char(string="生产线编号")
    belong_factory = fields.Many2one('qm.factory', string="所属工厂")


# 子生产线
class ProductLineKid(models.Model):
    _name = 'qm.pro.line.kid'

    name = fields.Char("子生产线")
    belong_pro_line = fields.Many2one('qm.pro.line', string="所属生产线")
    belong_factory = fields.Many2one(related='belong_pro_line.belong_factory', string="所属工厂")


