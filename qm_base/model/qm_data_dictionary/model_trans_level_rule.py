# -*- coding: utf-8 -*-
from __future__ import division
from openerp import models, fields, api


class TransRule(models.Model):
    _name = 'qm.trans.rule'

    # 定义字段
    name = fields.Char("动态转移规则名称")
    condition_list_ids = fields.One2many('qm.trans.level.type', 'trans_rule_id', '转移类型')


class ConditionList(models.Model):
    _name = 'qm.trans.level.type'

    trans_rule_id = fields.Many2one('qm.trans.rule', string="动态转移规则名称")
    name = fields.Char(string="动态转移类型")
    trans_level_condition_ids = fields.One2many('qm.trans.level.condition', 'trans_level_type_id', string='转移条件')


class TransLevelCondition(models.Model):
    _name = 'qm.trans.level.condition'
    name = fields.Char(string="转移条件")
    trans_level_type_id = fields.Many2one('qm.trans.level.type', string='动态转移类型')

