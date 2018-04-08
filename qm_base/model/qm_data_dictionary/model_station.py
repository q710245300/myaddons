# -*- coding: utf-8 -*-
from openerp import models, fields, api


class StorageLocation(models.Model):
    _name = 'station.product.location'

    name = fields.Char('库位',  required=True)
    num = fields.Char("编号")
    factory_id = fields.Many2one('station.factory', string='所属工厂')


class ProductLine(models.Model):
    _name = 'station.product.line'

    name = fields.Char(string="生产线")
    num = fields.Char(string="编码")
    factory_id = fields.Many2one('station.factory', string='所属工厂')


class CheckPoint(models.Model):
    _name = 'station.check.point'

    name = fields.Char('检验点', required=True)
    num = fields.Char("编号")
    factory_id = fields.Many2one('station.factory', string='所属工厂')
