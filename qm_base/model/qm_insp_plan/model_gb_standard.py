# -*-coding:utf-8-*-
from openerp import models, api, fields
import requests
import json


class qm_gb_standard(models.Model):
    _name = 'qm.gb_standard'
    name = fields.Char(string='标准')
    gb_standard_ids = fields.One2many('qm.sample_check_type', 'gb_standard_id', string='抽样检验类型')


class qm_sample_check_type(models.Model):
    _name = 'qm.sample_check_type'
    name = fields.Char(string='抽样类型')
    sample_type_code = fields.Char(string='抽样类型字码')

    # sample_type_code = fields.Char(string='抽样类型字码')
    gb_standard_id = fields.Many2one('qm.gb_standard', string='国标', select=True, required=True, ondelete='cascade')
    sample_check_type_ids_first = fields.One2many('qm.check_level', 'sample_check_type_id', string='检验水平')
    sample_check_type_ids_second = fields.One2many('qm.check_degree', 'sample_check_type_id', string='检验严格性')
    sample_check_type_ids_third = fields.One2many('qm.accept_quality', 'sample_check_type_id', string='aql值')


class qm_check_level(models.Model):
    _name = 'qm.check_level'
    name = fields.Char(string='检验水平')
    sample_check_type_id = fields.Many2one('qm.sample_check_type', string='抽样检验类型')


class qm_check_degree(models.Model):
    _name = 'qm.check_degree'
    name = fields.Many2one('qm.check_degree_item', string='检验严格度')
    sample_check_type_id = fields.Many2one('qm.sample_check_type', string='检验严格度字码')


class qm_check_degree_item(models.Model):
    _name = 'qm.check_degree_item'
    name = fields.Char(string='检验严格度')
    check_degree_code = fields.Char(string='检验严格度字码')

class qm_accept_quality(models.Model):
    _name = 'qm.accept_quality'
    name = fields.Char( string='aql值')
    sample_check_type_id = fields.Many2one('qm.sample_check_type', string='抽样检验类型')
