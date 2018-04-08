# -*- coding: utf-8 -*-
from __future__ import division
from openerp import models, fields, api


class TransCheckDegreeRule(models.Model):
    _name = 'qm.check.degree.trans.rule'

    # 定义字段
    name = fields.Char("转移规则编号")
    rule_name = fields.Many2one('qm.trans.rule', string="转移规则名称")
    is_certificate = fields.Boolean(string="需要资格验证")
    method_trans = fields.Boolean(string="s法与σ法的转换")

    condition_list_ids = fields.One2many('qm.check.degree.trans.list', 'trans_rule_id', '转换条件')


class TransCheckDegreeList(models.Model):
    _name = 'qm.check.degree.trans.list'

    def compute_trans_rule_name(self, cr, uid, context=None):
        print '----------------------------------------------------------', context
        if context is None:
            context = {}
        return context.get('trans_rule_name', False)

    trans_rule_id = fields.Many2one("qm.check.degree.trans.rule", string="调整规则")

    AND_OR = [
        ('and', 'and'),
        ('or', 'or')
    ]
    name = fields.Char(string="检验条件")

    trans_rule_name = fields.Many2one('qm.trans.rule', string="转移规则名称")
    trans_rule_type = fields.Many2one('qm.trans.level.type', string="动态转移类型")
    and_or_one = fields.Selection(AND_OR, string="and/or")
    condition_one = fields.Many2one('qm.trans.level.condition', string="转换条件1")
    condition_two = fields.Many2one('qm.trans.level.condition', string="转换条件2")
    condition_three = fields.Many2one('qm.trans.level.condition', string="转换条件3")
    condition_four = fields.Many2one('qm.trans.level.condition', string="转换条件4")
    approve = fields.Boolean(string="负责部门审批")
    touch_qm_notify = fields.Boolean(string="触发质量通知")
    _defaults = {
        'trans_rule_name': compute_trans_rule_name,
    }