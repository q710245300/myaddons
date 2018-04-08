# -*- coding: utf-8 -*-
from openerp import models, fields, api


class Usage(models.Model):
    _name = 'qm.usage'

    # 检验计划使用方法
    name = fields.Char('方法名称')
    use_center = fields.Char("摘要")
    describe = fields.Html('详情描述')


class Technology(models.Model):
    _name = 'qm.technology'

    # 检验计划-工艺
    name = fields.Char('工艺名称')
    center = fields.Char("摘要")
    describe = fields.Html('详情描述')


class QMStandard(models.Model):
    _name = 'qm.standard'

    # 检验计划-工序-质量标准
    name = fields.Char('质量标准')
    # describe = fields.Html('简述')


class WorkCenter(models.Model):
    _name = 'qm.work.center'

    # 检验计划-工艺
    name = fields.Char('工作中心')
    # describe = fields.Html('简述')
