# -*- coding: utf-8 -*-
import requests, json
from openerp import models, fields, api
from openerp.exceptions import ValidationError

class qm_sample_plan(models.Model):
    _name = "qm.sample_plan"

    name = fields.Char(string='采样方案', required=True)
    sampling_standard = fields.Selection([('fixed_sample', '固定采样'),
                                          ('complete_inspection', '100%检验'),
                                          ('use_sample_scheme', '使用采样方案'),
                                          ('percentage_inspection', '百分率检验')],
                                         '采样类型', required=True)

    gb_standard_id = fields.Many2one('qm.gb_standard', string='标准')
    gb_standard_name = fields.Char(related='gb_standard_id.name', string='标准')
    sample_check_type_id = fields.Many2one('qm.sample_check_type', string='抽样检验类型')
    sample_type_code = fields.Char(related='sample_check_type_id.sample_type_code', string='抽样检验类型')
    check_level_id = fields.Many2one('qm.check_level', string='检验水平')
    check_level_name = fields.Char(related='check_level_id.name', string='检验水平')
    check_degree_id = fields.Many2one('qm.check_degree', string='检验严格度')
    check_degree_name = fields.Many2one(related='check_degree_id.name', string='检验严格度')
    aql_id = fields.Many2one('qm.accept_quality', string='aql值')
    aql_name = fields.Char(related='aql_id.name', string='aql值')
    sample_percentage = fields.Float(string='采样百分率')
    creater = fields.Many2one('res.users', string=u'创建人', default=lambda self: self.env.uid)
    create_time = fields.Datetime(string=u'创建时间', default=fields.Date.today())
    evaluation_mode = fields.Selection([('bad_num_evaluation', '按照不良数评估'),
                                        ('defect_evaluation', '按照缺陷评估'),
                                        ('manual_evaluation', '手工评估')],
                                       '评估模式')
    only_attr_check = fields.Boolean(string='仅用于属性检验')
    fixed_sample_num = fields.Integer(string='固定采样量')
    sample_plan_ids = fields.One2many('qm.sample_table', 'sample_plan_id', string='采样方案表')
    sample_plan_ids_sec = fields.One2many('qm.sample_table', 'sample_plan_id', string='采样方案表')

    #控制计量 查询采样方案表
    measurement_table_one_ids = fields.One2many('qm.measurement_sample_table', 'sample_plan_id', string='采样方案表')
    measurement_table_two_ids = fields.One2many('qm.measurement_sample_table', 'sample_plan_id', string='采样方案表')
    measurement_table_three_ids = fields.One2many('qm.measurement_sample_table', 'sample_plan_id', string='采样方案表')



    '''
        根据 检验水平  和  aql 值 创建， 采样方案表
    '''

    # 只存储本表中一组数据，创建新查询数据时，对于已存在的数据进行删除
    def clear_old_result(self):
        if self.gb_standard_name == 'GB/T2828.1-2012':
            old_records_result = self.env['qm.sample_table'].search([('sample_plan_id', '=', self.id)])
        elif self.gb_standard_name == 'GB/T6378.1-2008':
            old_records_result = self.env['qm.measurement_sample_table'].search([('sample_plan_id', '=', self.id)])
        old_records_result.unlink()

    # 计数创建 样本查询表
    def create_count_sample_table(self, param, lot_size_desc):

        url = 'http://127.0.0.1:5000/GBT2828.1-2012/read_sample_table'
        headers = {'content-type': 'application/json'}
        response=None
        try:
            response = requests.post(url, data=json.dumps(param), headers=headers)
        except Exception as e:
            print '----Error in method model_sample_plan.create_count_sample_table: the request failed'
            raise ValidationError('请求服务失败或服务器未开启')
        if response :
            # 请求返回的数据
            response_data = response.json()
            if response_data['success']:
                request_data = response_data['result']['lines']
                if request_data is not None:
                    lot_size_desc_len=len(lot_size_desc)
                    lines=list()
                    if self.sample_type_code in ['Integer_one_sample', 'Fraction_one_sample_fixed',
                                                 'Fraction_one_sample_unfixed']:
                        for index in range(lot_size_desc_len):
                            line = {
                                'lot_size': lot_size_desc[index],
                                'sample_code': request_data[index][3],
                                'normal_sample_size': request_data[index][0][2],
                                'normal_ac': request_data[index][0][0],
                                'normal_re': request_data[index][0][1],
                                'tightened_sample_size': request_data[index][1][2],
                                'tightened_ac': request_data[index][1][0],
                                'tightened_re': request_data[index][1][1],
                                'reduced_sample_size': request_data[index][2][2],
                                'reduced_ac': request_data[index][2][0],
                                'reduced_re': request_data[index][2][1],
                            }
                            lines.append(line)
                        self.update({'sample_plan_ids': lines})

                    elif self.sample_type_code == 'Integer_two_sample':
                        for index in range(lot_size_desc_len):
                            # 如果读取的 * ，就显示*，
                            line1 = dict()
                            line2 = dict()
                            line1['lot_size'] = lot_size_desc[index]
                            line1['sample_code'] = request_data[index][3]
                            line1['sample_time'] = '第一'
                            line2['sample_time'] = '第二'
                            line2['lot_size'] = False
                            # r如果要返回样本量和累积样本量，需要重写 查表方法
                            if request_data[index][0][0] == '*':
                                line1['normal_sample_size'] = False
                                line1['normal_cumulative_sample_size'] = False
                                line1['normal_ac'] = '*'
                                line1['normal_re'] = '*'
                                line2['normal_sample_size'] = False
                                line2['normal_cumulative_sample_size'] = False
                                line2['normal_ac'] = '*'
                                line2['normal_re'] = '*'
                            else:
                                line1['normal_sample_size'] = request_data[index][0][4]
                                line1['normal_cumulative_sample_size'] = int(request_data[index][0][4])
                                line1['normal_ac'] = request_data[index][0][0]
                                line1['normal_re'] = request_data[index][0][1]
                                line2['normal_sample_size'] = request_data[index][0][4]
                                line2['normal_cumulative_sample_size'] = int(request_data[index][0][4]) * 2
                                line2['normal_ac'] = request_data[index][0][2]
                                line2['normal_re'] = request_data[index][0][3]
                            if request_data[index][1][0] == '*':
                                line1['tightened_sample_size'] = False
                                line1['tighted_cumulative_sample_size'] = False
                                line1['tightened_ac'] = '*'
                                line1['tightened_re'] = '*'
                                line2['tightened_sample_size'] = False
                                line2['tighted_cumulative_sample_size'] = False
                                line2['tightened_ac'] = '*'
                                line2['tightened_re'] = '*'
                            else:
                                line1['tightened_sample_size'] = request_data[index][1][4]
                                line1['tighted_cumulative_sample_size'] = int(request_data[index][1][4])
                                line1['tightened_ac'] = request_data[index][1][0]
                                line1['tightened_re'] = request_data[index][1][1]
                                line2['tightened_sample_size'] = request_data[index][1][4]
                                line2['tighted_cumulative_sample_size'] = int(request_data[index][1][4]) * 2
                                line2['tightened_ac'] = request_data[index][1][2]
                                line2['tightened_re'] = request_data[index][1][3]
                            if request_data[index][2][0] == '*':
                                line1['reduced_sample_size'] = False
                                line2['reduced_cumulative_sample_size'] = False
                                line1['reduced_ac'] = '*'
                                line1['reduced_re'] = '*'
                                line2['reduced_sample_size'] = False
                                line2['tighted_cumulative_sample_size'] = False
                                line2['reduced_ac'] = '*'
                                line2['reduced_re'] = '*'
                            else:
                                line1['reduced_sample_size'] = request_data[index][2][4]
                                line2['reduced_cumulative_sample_size'] = int(request_data[index][2][4])
                                line1['reduced_ac'] = request_data[index][2][0]
                                line1['reduced_re'] = request_data[index][2][1]
                                line2['reduced_sample_size'] = request_data[index][2][4]
                                line2['tighted_cumulative_sample_size'] = int(request_data[index][2][4]) * 2
                                line2['reduced_ac'] = request_data[index][2][2]
                                line2['reduced_re'] = request_data[index][2][3]
                            lines.append(line1)
                            lines.append(line2)
                        self.update({'sample_plan_ids': lines})

                    elif self.sample_type_code == 'Integer_many_sample':
                        for index in range(lot_size_desc_len):
                            # 如果读取的 * ，就显示*，
                            line1 = dict()
                            line2 = dict()
                            line3 = dict()
                            line4 = dict()
                            line5 = dict()
                            line1['lot_size'] = lot_size_desc[index]
                            line2['lot_size'] = False
                            line3['lot_size'] = False
                            line4['lot_size'] = False
                            line5['lot_size'] = False
                            line1['sample_code'] = request_data[index][3]
                            line1['sample_time'] = '第一'
                            line2['sample_time'] = '第二'
                            line3['sample_time'] = '第三'
                            line4['sample_time'] = '第四'
                            line5['sample_time'] = '第五'

                            if request_data[index][0][0] == '*':
                                line1['normal_sample_size'] = False
                                line1['normal_cumulative_sample_size'] = False
                                line1['normal_ac'] = '*'
                                line1['normal_re'] = '*'
                                line2['normal_sample_size'] = False
                                line2['normal_cumulative_sample_size'] = False
                                line2['normal_ac'] = '*'
                                line2['normal_re'] = '*'
                                line3['normal_sample_size'] = False
                                line3['normal_cumulative_sample_size'] = False
                                line3['normal_ac'] = '*'
                                line3['normal_re'] = '*'
                                line3['normal_cumulative_sample_size'] = False
                                line4['normal_sample_size'] = False
                                line4['normal_cumulative_sample_size'] = False
                                line4['normal_ac'] = '*'
                                line4['normal_re'] = '*'
                                line5['normal_sample_size'] = False
                                line5['normal_cumulative_sample_size'] = False
                                line5['normal_ac'] = '*'
                                line5['normal_re'] = '*'
                            elif request_data[index][0][0] == '++':
                                line1['normal_sample_size'] = False
                                line1['normal_cumulative_sample_size'] = False
                                line1['normal_ac'] = '++'
                                line1['normal_re'] = '++'
                                line2['normal_sample_size'] = False
                                line2['normal_cumulative_sample_size'] = False
                                line2['normal_ac'] = '++'
                                line2['normal_re'] = '++'
                                line3['normal_sample_size'] = False
                                line3['normal_cumulative_sample_size'] = False
                                line3['normal_ac'] = '++'
                                line3['normal_re'] = '++'
                                line4['normal_sample_size'] = False
                                line4['normal_cumulative_sample_size'] = False
                                line4['normal_ac'] = '++'
                                line4['normal_re'] = '++'
                                line5['normal_sample_size'] = False
                                line5['normal_cumulative_sample_size'] = False
                                line5['normal_ac'] = '++'
                                line5['normal_re'] = '++'
                            else:
                                line1['normal_sample_size'] = request_data[index][0][10]
                                line1['normal_cumulative_sample_size'] = int(request_data[index][0][10]) * 1

                                line1['normal_ac'] = '#' if request_data[index][0][0] == -1 else \
                                request_data[index][0][
                                    0]
                                line1['normal_re'] = request_data[index][0][1]
                                line2['normal_sample_size'] = request_data[index][0][10]
                                line2['normal_cumulative_sample_size'] = int(request_data[index][0][10]) * 2
                                line2['normal_ac'] = request_data[index][0][2]
                                line2['normal_re'] = request_data[index][0][3]
                                line3['normal_sample_size'] = request_data[index][0][10]
                                line3['normal_cumulative_sample_size'] = int(request_data[index][0][10]) * 3
                                line3['normal_ac'] = request_data[index][0][4]
                                line3['normal_re'] = request_data[index][0][5]
                                line4['normal_sample_size'] = request_data[index][0][10]
                                line4['normal_cumulative_sample_size'] = int(request_data[index][0][10]) * 4
                                line4['normal_ac'] = request_data[index][0][6]
                                line4['normal_re'] = request_data[index][0][7]
                                line5['normal_sample_size'] = request_data[index][0][10]
                                line5['normal_cumulative_sample_size'] = int(request_data[index][0][10]) * 5
                                line5['normal_ac'] = request_data[index][0][8]
                                line5['normal_re'] = request_data[index][0][9]

                            if request_data[index][1][0] == '*':
                                line1['tightened_sample_size'] = False
                                line1['tighted_cumulative_sample_size'] = False
                                line1['tightened_ac'] = '*'
                                line1['tightened_re'] = '*'
                                line2['tightened_sample_size'] = False
                                line2['tighted_cumulative_sample_size'] = False
                                line2['tightened_ac'] = '*'
                                line2['tightened_re'] = '*'
                                line3['tightened_sample_size'] = False
                                line3['tighted_cumulative_sample_size'] = False
                                line3['tightened_ac'] = '*'
                                line3['tightened_re'] = '*'
                                line4['tightened_sample_size'] = False
                                line4['tighted_cumulative_sample_size'] = False
                                line4['tightened_ac'] = '*'
                                line4['tightened_re'] = '*'
                                line5['tightened_sample_size'] = False
                                line5['tighted_cumulative_sample_size'] = False
                                line5['tightened_ac'] = '*'
                                line5['tightened_re'] = '*'
                            elif request_data[index][1][0] == '++':
                                line1['tightened_sample_size'] = False
                                line1['tighted_cumulative_sample_size'] = False
                                line1['tightened_ac'] = '++'
                                line1['tightened_re'] = '++'
                                line2['tightened_sample_size'] = False
                                line2['tighted_cumulative_sample_size'] = False
                                line2['tightened_ac'] = '++'
                                line2['tightened_re'] = '++'
                                line3['tightened_sample_size'] = False
                                line3['tighted_cumulative_sample_size'] = False
                                line3['tightened_ac'] = '++'
                                line3['tightened_re'] = '++'
                                line4['tightened_sample_size'] = False
                                line4['tighted_cumulative_sample_size'] = False
                                line4['tightened_ac'] = '++'
                                line4['tightened_re'] = '++'
                                line5['tightened_sample_size'] = False
                                line5['tighted_cumulative_sample_size'] = False
                                line5['tightened_ac'] = '++'
                                line5['tightened_re'] = '++'
                            else:
                                line1['tightened_sample_size'] = request_data[index][1][10]
                                line1['tighted_cumulative_sample_size'] = int(request_data[index][1][10]) * 1
                                line1['tightened_ac'] = '#' if request_data[index][1][0] == -1 else \
                                request_data[index][1][0]
                                line1['tightened_re'] = request_data[index][1][1]
                                line2['tightened_sample_size'] = request_data[index][1][10]
                                line2['tighted_cumulative_sample_size'] = int(request_data[index][1][10]) * 2
                                line2['tightened_ac'] = request_data[index][1][2]
                                line2['tightened_re'] = request_data[index][1][3]
                                line3['tightened_sample_size'] = request_data[index][1][10]
                                line3['tighted_cumulative_sample_size'] = int(request_data[index][1][10]) * 3
                                line3['tightened_ac'] = request_data[index][1][4]
                                line3['tightened_re'] = request_data[index][1][5]
                                line4['tightened_sample_size'] = request_data[index][1][10]
                                line4['tighted_cumulative_sample_size'] = int(request_data[index][1][10]) * 4
                                line4['tightened_ac'] = request_data[index][1][6]
                                line4['tightened_re'] = request_data[index][1][7]
                                line5['tightened_sample_size'] = request_data[index][1][10]
                                line5['tighted_cumulative_sample_size'] = int(request_data[index][1][10]) * 5
                                line5['tightened_ac'] = request_data[index][1][8]
                                line5['tightened_re'] = request_data[index][1][9]
                            if request_data[index][2][0] == '*':
                                line1['reduced_sample_size'] = False
                                line1['reduced_cumulative_sample_size'] = False
                                line1['reduced_ac'] = '*'
                                line1['reduced_re'] = '*'
                                line2['reduced_sample_size'] = False
                                line2['reduced_cumulative_sample_size'] = False
                                line2['reduced_ac'] = '*'
                                line2['reduced_re'] = '*'
                                line3['reduced_sample_size'] = False
                                line3['reduced_cumulative_sample_size'] = False
                                line3['reduced_ac'] = '*'
                                line3['reduced_re'] = '*'
                                line4['reduced_sample_size'] = False
                                line4['reduced_cumulative_sample_size'] = False
                                line4['reduced_ac'] = '*'
                                line4['reduced_re'] = '*'
                                line5['reduced_sample_size'] = False
                                line5['reduced_cumulative_sample_size'] = False
                                line5['reduced_ac'] = '*'
                                line5['reduced_re'] = '*'
                            elif request_data[index][2][0] == '++':
                                line1['reduced_sample_size'] = False
                                line1['reduced_cumulative_sample_size'] = False
                                line1['reduced_ac'] = '++'
                                line1['reduced_re'] = '++'
                                line2['reduced_sample_size'] = False
                                line2['reduced_cumulative_sample_size'] = False
                                line2['reduced_ac'] = '++'
                                line2['reduced_re'] = '++'
                                line3['reduced_sample_size'] = False
                                line3['reduced_cumulative_sample_size'] = False
                                line3['reduced_ac'] = '++'
                                line3['reduced_re'] = '++'
                                line4['reduced_sample_size'] = False
                                line4['reduced_cumulative_sample_size'] = False
                                line4['reduced_ac'] = '++'
                                line4['reduced_re'] = '++'
                                line5['reduced_sample_size'] = False
                                line5['reduced_cumulative_sample_size'] = False
                                line5['reduced_ac'] = '++'
                                line5['reduced_re'] = '++'
                            else:
                                line1['reduced_sample_size'] = request_data[index][2][10]
                                line1['reduced_cumulative_sample_size'] = int(request_data[index][2][10]) * 1
                                line1['reduced_ac'] = '#' if request_data[index][2][0] == -1 else \
                                request_data[index][2][0]
                                line1['reduced_re'] = request_data[index][2][1]
                                line2['reduced_sample_size'] = request_data[index][2][10]
                                line2['reduced_cumulative_sample_size'] = int(request_data[index][2][10]) * 2
                                line2['reduced_ac'] = request_data[index][2][2]
                                line2['reduced_re'] = request_data[index][2][3]
                                line3['reduced_sample_size'] = request_data[index][2][10]
                                line3['reduced_cumulative_sample_size'] = int(request_data[index][2][10]) * 3
                                line3['reduced_ac'] = request_data[index][2][4]
                                line3['reduced_re'] = request_data[index][2][5]
                                line4['reduced_sample_size'] = request_data[index][2][10]
                                line4['reduced_cumulative_sample_size'] = int(request_data[index][2][10]) * 4
                                line4['reduced_ac'] = request_data[index][2][6]
                                line4['reduced_re'] = request_data[index][2][7]
                                line5['reduced_sample_size'] = request_data[index][2][10]
                                line5['reduced_cumulative_sample_size'] = int(request_data[index][2][10]) * 5
                                line5['reduced_ac'] = request_data[index][2][8]
                                line5['reduced_re'] = request_data[index][2][9]
                            lines.append(line1)
                            lines.append(line2)
                            lines.append(line3)
                            lines.append(line4)
                            lines.append(line5)
                        self.update({'sample_plan_ids': lines})

            else:
                print '-----------%s----------' % (response_data['message'])
                raise ValidationError('查询结果返回为 None')
        else:
            raise ValidationError('查询结果返回为 None')

     # 计量创建 样本查询表

    def create_measurement_sample_table(self, param, lot_size_desc):
        url = 'http://127.0.0.1:5000/GBT6378.1-2008/read_sample_table'
        headers = {'content-type': 'application/json'}

        response = None
        try:
            response = requests.post(url, data=json.dumps(param), headers=headers)
        except Exception as e:
            print '----Error in method model_sample_plan.create_count_sample_table: the request failed'
            raise ValidationError('请求服务失败或服务器未开启')
        # 计量的创建 查询表
        if response:
            # 请求返回的数据
            response_data = response.json()
            if response_data['success']:
                request_data = response_data['result']['lines']

                if request_data:
                    lot_size_desc_len = len(lot_size_desc)
                    lines = list()

                    if self.sample_type_code in ['one_side_s_method', 'one_side_sigma_method']:
                        for index in range(lot_size_desc_len):
                            line = {
                                'lot_size': lot_size_desc[index],
                                'normal_sample_size': request_data[index][0][0],
                                'normal_k': request_data[index][0][1],
                                'tightened_sample_size': request_data[index][1][0],
                                'tightened_k': request_data[index][1][1],
                                'reduced_sample_size': request_data[index][2][0],
                                'reduced_k': request_data[index][2][1],
                            }
                            lines.append(line)
                        self.update({'measurement_table_one_ids': lines})

                    elif self.sample_type_code in ['both_side_s_method']:
                        for index in range(lot_size_desc_len):
                            line = {
                                'lot_size': lot_size_desc[index],
                                'normal_sample_size': request_data[index][0][0],
                                'normal_fs': request_data[index][0][1],
                                'tightened_sample_size': request_data[index][1][0],
                                'tightened_fs': request_data[index][1][1],
                                'reduced_sample_size': request_data[index][2][0],
                                'reduced_fs': request_data[index][2][1],
                            }
                            lines.append(line)
                        self.update({'measurement_table_two_ids': lines})

                    elif self.sample_type_code in ['both_side_sigma_method']:
                        for index in range(lot_size_desc_len):
                            line = {
                                'lot_size': lot_size_desc[index],
                                'normal_sample_size': request_data[index][0][0],
                                'normal_k': request_data[index][0][1],
                                'normal_f_sigma': request_data[index][0][2],
                                'tightened_sample_size': request_data[index][1][0],
                                'tightened_k': request_data[index][1][1],
                                'tightened_f_sigma': request_data[index][1][2],
                                'reduced_sample_size': request_data[index][2][0],
                                'reduced_k': request_data[index][2][1],
                                'reduced_f_sigma': request_data[index][2][2],
                            }
                            lines.append(line)
                        self.update({'measurement_table_three_ids': lines})

                else:
                    print '-----------%s----------' % (response_data['message'])
                    raise ValidationError('服务器查询结果为空')
            else:
                print '-----------%s----------' % (response_data['message'])
                raise ValidationError('服务器查询结果为空')
        else:
            raise ValidationError('服务器查询结果为空')


    @api.depends('check_level_name', 'aql_name')
    @api.multi
    def create_sample_table(self):

        # 先对输入的数据进行判定是否为 空
        if self.gb_standard_name not in ['GB/T2828.1-2012', 'GB/T6378.1-2008']:
            raise ValidationError('字段 标准 不存在不能进行查询')
        if self.sample_type_code == False:
            raise ValidationError('抽样检验类型不能为空')
        if self.check_level_name == False:
            raise ValidationError('检验水平不能为空')
        if self.aql_name == False:
            raise ValidationError('aql值不能为空')

        # 如果model对应的表中，存在记录，将删除所有的记录
        self.clear_old_result()
        # 看输出的结果 是否 能够居中，否则通过 使用空格 或者 使用 页面布局进行实现
        lot_size_desc = ['[2,8]',
                         '[9,15]',
                         '[16,25]',
                         '[26,50]',
                         '[51,90]',
                         '[91,150]',
                         '[151,280]',
                         '[281,500]',
                         '[501,1200]',
                         '[1201,3200]',
                         '[3201,10000]',
                         '[10001,35000]',
                         '[35001,150000]',
                         '[150001,500000]',
                         '[500001级以上]']
        lot_size_list = [5, 12, 20, 38, 70, 120, 215, 390, 850, 2200, 6600, 22500, 92500, 325000, 500001]
        # 有可能，检验严格度中，不是固定的三种，是一个动态的。
        check_degree_list = ['normal_check', 'tighted_check', 'reduced_check']
        lot_size_desc_len = len(lot_size_desc)
        lines = list()
        # rest 服务的 请求的参数
        param = dict()
        param['aql'] = self.aql_name
        param['check_level'] = self.check_level_name
        param['sample_type'] = self.sample_type_code
        param['lot_size_list'] = lot_size_list
        param['check_degree_list'] = check_degree_list

        if self.gb_standard_name == 'GB/T2828.1-2012':
            self.create_count_sample_table(param,lot_size_desc)
        elif self.gb_standard_name == 'GB/T6378.1-2008':
            self.create_measurement_sample_table(param, lot_size_desc)
        else:
            raise ValidationError('字段 标准 为空')

    @api.multi
    @api.onchange('sampling_standard')
    def onchange_gb_standard_id(self):
        if self.sampling_standard != False and self.sampling_standard != 'use_sample_scheme':
            self.gb_standard_id = False
            self.sample_check_type_id = False
            self.check_level_id = False
            self.check_degree_id = False
            self.aql_id = False

    @api.multi
    @api.onchange('gb_standard_id')
    def onchange_gb_standard_id(self):
        self.sample_check_type_id = False
        self.check_level_id = False
        self.check_degree_id = False
        self.aql_id = False

    @api.multi
    @api.onchange('sample_check_type_id')
    def on_change_sample_check_type_id(self):
        self.check_level_id = False
        self.check_degree_id = False
        self.aql_id = False





    # # 计数创建 样本查询表
    # def create_count_sample_table(self, param, lot_size_desc):
    #
    #     if self.sample_type_code in ['Integer_one_sample', 'Fraction_one_sample_fixed',
    #                                  'Fraction_one_sample_unfixed']:
    #         url = 'http://127.0.0.1:5000/read_sample_table'
    #         headers = {'content-type': 'application/json'}
    #         response = requests.post(url, data=json.dumps(param), headers=headers)
    #         # 请求返回的数据
    #         request_data = response.json()['lines']
    #         if request_data is not None:
    #             lot_size_desc_len = len(lot_size_desc)
    #             lines=list()
    #             for index in range(lot_size_desc_len):
    #                 normal_re = request_data[index][2]
    #
    #                 tightened_re = request_data[index][5]
    #
    #                 reduced_re = request_data[index][8]
    #
    #                 line = {
    #                     'lot_size': lot_size_desc[index],
    #                     'normal_sample_size': request_data[index][0],
    #                     'normal_ac': request_data[index][1],
    #                     'normal_re': normal_re,
    #                     'tightened_sample_size': request_data[index][3],
    #                     'tightened_ac': request_data[index][4],
    #                     'tightened_re': tightened_re,
    #                     'reduced_sample_size': request_data[index][6],
    #                     'reduced_ac': request_data[index][7],
    #                     'reduced_re': reduced_re,
    #                 }
    #                 lines.append(line)
    #         self.update({'sample_plan_ids': lines})
    #     elif self.sample_type_code == 'Integer_two_sample':
    #         raise ValidationError('整数二次抽样 样本查询表功能还未实现')
    #
    #     elif self.sample_type_code == 'Integer_many_sample':
    #         raise ValidationError('整数多次抽样 样本查询表功能还未实现')
    #
    #     # url = 'http://127.0.0.1:5000/read_sample_table'
    #     # headers = {'content-type': 'application/json'}
    #     # response = requests.post(url, data=json.dumps(param), headers=headers)
    #     # if response:
    #     #     # 请求返回的数据
    #     #     lines = list()
    #     #     lot_size_desc_len = len(lot_size_desc)
    #     #     response_data = response.json()
    #     #     if response_data['success']:
    #     #         request_data = response_data['result']['lines']
    #     #         if request_data:
    #     #             if self.sample_type_code in ['Integer_one_sample', 'Fraction_one_sample_fixed',
    #     #                                          'Fraction_one_sample_unfixed']:
    #     #                 for index in range(lot_size_desc_len):
    #     #                     line = {
    #     #                         'lot_size': lot_size_desc[index],
    #     #                         'normal_sample_size': request_data[index][0][2],
    #     #                         'normal_ac': request_data[index][0][0],
    #     #                         'normal_re': request_data[index][0][1],
    #     #                         'tightened_sample_size': request_data[index][1][2],
    #     #                         'tightened_ac': request_data[index][1][0],
    #     #                         'tightened_re': request_data[index][1][1],
    #     #                         'reduced_sample_size': request_data[index][2][2],
    #     #                         'reduced_ac': request_data[index][2][0],
    #     #                         'reduced_re': request_data[index][2][1],
    #     #                     }
    #     #                     lines.append(line)
    #     #                 self.update({'sample_plan_ids': lines})
    #     #             elif self.sample_type_code == 'Integer_two_sample':
    #     #                 raise ValidationError('整数二次抽样 样本查询表功能还未实现')
    #     #
    #     #             elif self.sample_type_code == 'Integer_many_sample':
    #     #                 raise ValidationError('整数多次抽样 样本查询表功能还未实现')
    #     #
    #     #         else:
    #     #             print '-----------%s----------' % (response_data['message'])
    #     #             raise ValidationError('服务器查询结果为空')
    #     #     else:
    #     #         print '-----------%s----------' % (response_data['message'])
    #     #         raise ValidationError('服务器查询结果为空')
    #     # else:
    #     #     raise ValidationError('服务器查询结果为空')
    #
    #
    #  # 计量创建 样本查询表

# class sample_talbe(models.Model):
#     _name = 'qm.sample_table'
#     sample_plan_id = fields.Many2one('qm.sample_plan', string='抽样检验类型', select=True, required=True, ondelete='cascade')
#     lot_size = fields.Char(string='批量')
#     normal_sample_size = fields.Integer(string='样本量(正常)')
#     normal_ac = fields.Float(string='Ac(正常)')
#     normal_re = fields.Float(string='Re(正常)')
#
#     tightened_sample_size = fields.Integer(string='样本量(加严)')
#     tightened_ac = fields.Float(string='Ac(加严)')
#     tightened_re = fields.Float(string='Re(加严)')
#
#     reduced_sample_size = fields.Integer(string='样本量(放宽)')
#     reduced_ac = fields.Float(string='Ac(放宽)')
#     reduced_re = fields.Float(string='Re(放宽)')
#
#     # added by mlq 2016年11月7日16:13:41
#
#     sample_code = fields.Char(string='样本量字码')
#     sample_time = fields.Char(string='样本')
#     normal_cumulative_sample_size = fields.Char(string='累计样本量(正常)')
#     tighted_cumulative_sample_size = fields.Char(string='累计样本量(加严)')
#     reduced_cumulative_sample_size = fields.Char(string='累计样本量(放宽)')




#  GB/T2828.1-2012  创建采样方案表 对应的model
class sample_talbe(models.Model):
    _name = 'qm.sample_table'
    sample_plan_id = fields.Many2one('qm.sample_plan', string='抽样检验类型', select=True, required=True, ondelete='cascade')
    lot_size = fields.Char(string='批量')
    normal_sample_size = fields.Char(string='样本量(正常)')
    normal_ac = fields.Char(string='Ac(正常)')
    normal_re = fields.Char(string='Re(正常)')

    tightened_sample_size = fields.Char(string='样本量(加严)')
    tightened_ac = fields.Char(string='Ac(加严)')
    tightened_re = fields.Char(string='Re(加严)')

    reduced_sample_size = fields.Char(string='样本量(放宽)')
    reduced_ac = fields.Char(string='Ac(放宽)')
    reduced_re = fields.Char(string='Re(放宽)')

    sample_code=fields.Char(string='样本量字码')
    sample_time=fields.Char(string='样本')
    normal_cumulative_sample_size=fields.Char(string='累计样本量(正常)')
    tighted_cumulative_sample_size = fields.Char(string='累计样本量(加严)')
    reduced_cumulative_sample_size = fields.Char(string='累计样本量(放宽)')


class measurement_sample_table(models.Model):
    _name='qm.measurement_sample_table'
    sample_plan_id = fields.Many2one('qm.sample_plan', string='抽样检验类型', select=True, required=True, ondelete='cascade')
    lot_size = fields.Char(string='批量')

    normal_sample_size = fields.Char(string='样本量(正常)')
    normal_k = fields.Char(string='k(正常)')
    normal_fs = fields.Char(string='fs(正常)')
    normal_f_sigma=fields.Char(string='sigma(正常)')

    tightened_sample_size = fields.Char(string='样本量(加严)')
    tightened_k = fields.Char(string='k(加严)')
    tightened_fs = fields.Char(string='fs(加严)')
    tightened_f_sigma = fields.Char(string='sigma(加严)')

    reduced_sample_size = fields.Char(string='样本量(放宽)')
    reduced_k = fields.Char(string='k(放宽)')
    reduced_fs = fields.Char(string='fs(放宽)')
    reduced_f_sigma = fields.Char(string='sigma(放宽)')
