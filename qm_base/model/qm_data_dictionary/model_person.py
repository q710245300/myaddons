# -*- coding: utf-8 -*-
from openerp import models, fields, api


class PlanPersonGroup(models.Model):
    _name = 'qm.plan.person.group'
    # 检验计划使用方法
    name = fields.Char('计划者组')


class CheckGroup(models.Model):
    _name = 'qm.process.check.group'
    # 检验计划使用方法
    name = fields.Char('班次')
