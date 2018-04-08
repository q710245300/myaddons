# -*- coding: utf-8 -*-
from openerp import models, fields, api


class Defects(models.Model):
    _name = 'qm.defects'

    name = fields.Char('缺陷类型')

    type = fields.Many2one('defects.type', string="缺陷分类")
    level = fields.Many2one('defects.level', string="缺陷等级")


class DefectType(models.Model):
    _name = 'defects.type'

    name = fields.Char('缺陷分类')


class DefectLevel(models.Model):
    _name = 'defects.level'

    name = fields.Char('缺陷等级')
    #TODO：zhaoli
    leval= fields.Integer('缺陷优先级')

    _sql_constraints = [('specialty_leval_unique', 'UNIQUE (leval)', '缺陷优先级必须唯一')]
