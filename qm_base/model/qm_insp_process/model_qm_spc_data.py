# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError
import requests, json

'''
    问题：
        1. ##### 子组大小不固定的， 哪有什么标准值呢?

'''


class qm_spc_data(models.Model):
    _name = "qm.spc_data"
    monitor_process_type = fields.Selection([('making_product_insp', '生产过程控制'),
                                             ('import_material_insp', '采购过程控制'),
                                             ('export_good_insp', '发货过程控制'), ], string='监控过程类型',
                                            default='making_product_insp')

    product_id = fields.Many2one('product.template', string='监控产品')
    product_type = fields.Char(related='product_id.product_version', string='产品型号', readonly=True)
    inspection_series = fields.Many2one('qm.lot.num.rule', string='检验系列批')
    inspection_series_num = fields.Char(related='inspection_series.name', string='检验系列批号', store=True)
    spc_yn = fields.Many2one('qm.insp_project_def', string='SPC特性')

    quality_quantity_character = fields.Selection(related='spc_yn.quality_quantity_character', string='特性类型',
                                                  readonly=True)

    # 通过程序，计算出来
    product_line = fields.Char(string='生产线')

    inspect_equipment = fields.Many2one('hr.equipment', string='检验设备')
    supplier_id = fields.Many2one('res.partner', string='供应商')
    # customer = fields.Many2one('res.users', u'客户')
    customer = fields.Many2one('res.partner', u'客户')
    work_center = fields.Char(string='工作中心')

    create_date = fields.Date(string='创建日期', default=fields.Date.today())

    control_chart_type = fields.Many2one('spc.control_chart_type', string='控制图类型')
    control_chart_type_code = fields.Char(related='control_chart_type.control_chart_type_code', string='控制图类型码',
                                          store=True)

    is_constant_sub_group_size = fields.Boolean(string='子组大小恒定')
    sub_group_size = fields.Integer(string='子组大小')
    target_value = fields.Float(related='spc_yn.target_value', string='目标值', readonly=True)
    lower_bound_values = fields.Float(related='spc_yn.lower_bound_values', string='规范上限(U)', readonly=True,
                                      )
    upper_bound_values = fields.Float(related='spc_yn.upper_bound_values', string='规范下限(L)', readonly=True)
    measurement_units = fields.Many2one(related='spc_yn.measurement_units', string='计量单位', readonly=True)
    round_precision = fields.Char(string='舍入精度')

    # 与检验项目中是相对应
    accept_depend = fields.Selection([('depend_1', '不合格品数检验'), ('depend_2', '不合格数检验')], string='定性接收性判定', readonly=True)

    set_standard_value = fields.Boolean(string='给定标准值')
    X0 = fields.Float(string='X0')
    u = fields.Float(string='u')
    R0 = fields.Float(string='R0')
    s0 = fields.Float(string='s0')
    sigma0 = fields.Float(string='σ0')
    # 计数标准值
    p0 = fields.Float(string='p0')
    u0 = fields.Float(string='u0')
    np0 = fields.Float(string='np0')
    c0 = fields.Float(string='c0')

    # 通过计算获得标准值
    # 计数的n不确定的标准值如何进行确定
    up_ccl = fields.Float(string='中心线')
    up_ucl = fields.Float(string='UCL')
    up_lcl = fields.Float(string='LCL')

    down_ccl = fields.Float(string='中心线')
    down_ucl = fields.Float(string='UCL')
    down_lcl = fields.Float(string='LCL')

    # 工作流状态
    state = fields.Selection([
        ('create', '新建'),
        ('activate', '激活的'),
        ('close', '关闭的')
    ], readonly=True, select=True, copy=False, string="工作流状态")

    # # 动态创建 控制限
    # @api.multi
    # def get_dynamic_control_limit(self):
    #
    #     print '--------------starting-----------'
    #
    #     # 先判断 需要的字段是否为False
    #     if self.inspection_series == False:
    #         raise ValidationError('字段检验系列批不能为空')
    #     if self.control_chart_type == False:
    #         raise ValidationError('字段控制图类型不能为空')
    #     if self.is_constant_sub_group_size == True:
    #         if self.sub_group_size == False:
    #             raise ValidationError('字段子组大小不能为空')
    #
    #         # 获取请求参数的数据
    #         series_num = self.inspection_series_num
    #         series_len = len(series_num)
    #         # 根据系列批获取 观测的数据
    #         # 判断批号的组成是否规范
    #         if series_len > 6:
    #             task_records = self.env['qm.insp.task.record'].search(
    #                 [('lot_num', 'like', series_num[0:series_len - 6])])
    #             # 配凑 观测值数据
    #             n_defect_sequence = list()
    #             if len(task_records) > 20:
    #                 # 判断n是否相等
    #                 sample_counts = self.sub_group_size
    #                 record_counts = 0
    #                 for task_record in task_records:
    #                     # 判断每一条记录的 子组数是否相等
    #                     if task_record.sample_count == sample_counts:
    #                         n_defect_sequence.append((sample_counts, task_record.d))
    #                         record_counts += 1
    #
    #                 # 同一批的数量 >20 ，才有效
    #                 if len(n_defect_sequence) > 20:
    #                     # 构造请求参数
    #                     request_args = dict(sequence=n_defect_sequence, control_chart_type=self.control_chart_type_code,
    #                                         valid_num=4, is_constant_sub_group_size=self.is_constant_sub_group_size)
    #
    #                     # 进行请求
    #                     url = 'http://127.0.0.1:8080/SPC/get_dynamic_count_control_lines'
    #                     headers = {'content-type': 'application/json'}
    #                     response = requests.post(url, data=json.dumps(request_args), headers=headers)
    #                     # 对请求后的数据进行处理
    #
    #                     if response:
    #                         # 请求返回的数据
    #                         response_data = response.json()
    #                         print '!!!!!!!!%s' % response_data['message']
    #                         if response_data['success']:
    #                             result = response_data['result']
    #                             # 请求结果不为空，怎进行更新数据
    #                             if result :
    #                                 self.up_ccl = result['up_ccl']
    #                                 self.up_ucl = result['up_ucl']
    #                                 self.up_lcl = result['up_lcl']
    #                     else:
    #                         raise ValidationError('本次请求失败，响应的数据为空')
    #                 else:
    #                     raise ValidationError('子组数小于20,不能进行动态创建标准值')
    #             else:
    #                 raise ValidationError('子组数小于20,不能进行动态创建标准值')
    #         else:
    #             raise ValidationError('检验系列批构造存在问题')
    #
    #     else:
    #         ##### 子组大小不固定的， 哪有什么标准值呢?
    #         pass

    @api.multi
    def get_quantity_data(self):

        key_list = [ 'lower_bound_values', 'upper_bound_values', 'measurement_units',
                    'round_precision']
        for key in key_list:
            if self[key] == False:
                raise ValidationError('字段 %s 不能能空' % key)
        round_precision = int(self.round_precision)

        return dict(target_value=self.target_value,
                    lower_bound_values=self.lower_bound_values, upper_bound_values=self.upper_bound_values,
                    measurement_units=self.measurement_units, round_precision=round_precision)

    @api.onchange('inspection_series')
    def get_sub_code_name(self):
        # 批次号id
        inspection_series_id = self.inspection_series
        if inspection_series_id != False:
            # 供应商
            self.supplier_id = inspection_series_id.partner_num.belong_partner
            # 顾客
            self.customer = inspection_series_id.customer_num.belong_customer
            # 设备
            self.inspect_equipment = inspection_series_id.equipment_num.belong_equipment
            # 生产线
            self.product_line = inspection_series_id.pro_line_num.product_line_num

    @api.multi
    def get_static_measurement_line(self):
        print 'start to testing ++++++++++++++'
        if self.sub_group_size == False:
            raise ValidationError('字段 子组大小 不能为空')

        if self.quality_quantity_character == 'quantity_character' and self.control_chart_type_code and self.set_standard_value:
            request_args = dict()
            if not self.is_constant_sub_group_size:
                raise ValidationError('使用给定值创建标准限，是在 子组容量大小固定的情况下使用的')

            if self.control_chart_type_code in ['x_bar_range_chart', 'single_value_moving_range_chart']:
                request_args['control_chart_type'] = self.control_chart_type_code
                if self.R0 == False:
                    raise ValidationError('字段 R0 不能能空')
                request_args['R0'] = self.R0

                if self.control_chart_type_code =='single_value_moving_range_chart' and self.sub_group_size!=1:
                    raise ValidationError('单值-移动极差控制图的子组大小取值为1')

            elif self.control_chart_type_code == 'x_bar_standard_deviation_chart':
                request_args['control_chart_type'] = self.control_chart_type_code
                if self.s0 == False:
                    raise ValidationError('字段 s0 不能能空')
                request_args['s0'] = self.s0

            elif self.control_chart_type_code == 'median_range_chart':
                raise ValidationError('中位数控制图没有基于给定值，创建标准值的方法')

            key_list = ['X0', 'u', 'sigma0']
            for key in key_list:
                if self[key] == False:
                    raise ValidationError('字段 %s 不能为空' % key)
                else:
                    request_args[key] = self[key]
            quantity_args = self.get_quantity_data()
            request_args['sub_group_size'] = self.sub_group_size
            request_args['valid_num'] = quantity_args['round_precision']

            url = 'http://127.0.0.1:8080/SPC/get_static_measurement_control_lines'
            headers = {'content-type': 'application/json'}
            response = None
            try:
                response = requests.post(url, data=json.dumps(request_args), headers=headers)
            except Exception as e:
                print '----Error in method model_sample_plan.create_count_sample_table: the request failed'
                raise ValidationError('请求服务失败或服务器未开启')
            if response :
                # 请求返回的数据
                response_data = response.json()
                print '!!!!!!!!%s' % response_data['message']
                if response_data['success']:
                    result = response_data['result']
                    print '-----------', result
                    if result is not None:
                        self.up_ccl = result['up_ccl']
                        self.up_ucl = result['up_ucl']
                        self.up_lcl = result['up_lcl']
                        self.down_ccl = result['down_ccl']
                        self.down_ucl = result['down_ucl']
                        self.down_lcl = result['down_lcl']
            else:
                raise ValidationError('本次请求失败，响应的数据为空')

    @api.multi
    def get_static_count_line(self):

        if self.quality_quantity_character == 'quality_character' and self.control_chart_type_code and self.set_standard_value:
            request_args = dict()
            if not self.is_constant_sub_group_size:
                raise ValidationError('使用给定值创建标准限，是在 子组容量大小固定的情况下使用的')

            # 针对不同的 控制图，进行不同处理

            if self.control_chart_type_code in ['defect_rate_p_chart', 'unit_defect_number_u_chart',
                                                'defect_number_np_chart', 'defect_number_c_chart', 'p_to_z_chart']:
                # 针对不同的控制图，获得不同的参数值
                # 参数不为空，进行处理

                request_args['control_chart_type'] = self.control_chart_type_code
                request_args['sub_group_size'] = self.sub_group_size
                request_args['valid_num'] = 4
                if self.control_chart_type_code == 'defect_rate_p_chart':
                    if self.p0 == False:
                        raise ValidationError('字段 p0 不能能空')
                    request_args['p0'] = self.p0
                elif self.control_chart_type_code == 'unit_defect_number_u_chart':
                    if self.u0 == False:
                        raise ValidationError('字段 u0 不能能空')
                    request_args['u0'] = self.u0

                elif self.control_chart_type_code == 'defect_number_np_chart':
                    # 此处需要进行处理
                    if self.p0 == False:
                        raise ValidationError('字段 p0 不能能空')
                    request_args['np0'] = self.p0 * self.sub_group_size

                elif self.control_chart_type_code == 'defect_number_c_chart':

                    if self.c0 == False:
                        raise ValidationError('字段 c0 不能能空')
                    request_args['c0'] = self.c0

                url = 'http://127.0.0.1:8080/SPC/get_static_count_control_lines'
                headers = {'content-type': 'application/json'}

                response = None
                try:
                    response = requests.post(url, data=json.dumps(request_args), headers=headers)
                except Exception as e:
                    print '----Error in method model_sample_plan.create_count_sample_table: the request failed'
                    raise ValidationError('请求服务失败或服务器未开启')


                if response :
                    # 请求返回的数据
                    response_data = response.json()
                    print '!!!!!!!!%s' % response_data['message']
                    if response_data['success']:
                        result = response_data['result']
                        print '-----------', result
                        if result is not None:
                            self.up_ccl = result['up_ccl']
                            self.up_ucl = result['up_ucl']
                            self.up_lcl = result['up_lcl']
                else:
                    raise ValidationError('本次请求失败，响应的数据为空')

    # @api.multi
    # def create_control_line(self):
    #
    #     # 子组大小固定，创建控制限
    #
    #     # 根据不同的  控制图类型创建不同的标准限
    #
    #
    #     if self.sub_group_size == False:
    #         raise ValidationError('字段 子组大小 不能为空')
    #
    #     if self.quality_quantity_character == 'quantity_character' and self.control_chart_type_code and self.set_standard_value:
    #         request_args = dict()
    #         if not self.is_constant_sub_group_size:
    #             raise ValidationError('使用给定值创建标准限，是在 子组容量大小固定的情况下使用的')
    #
    #         if self.control_chart_type_code in ['x_bar_range_chart', 'single_value_moving_range_chart']:
    #             request_args['control_chart_type'] = self.control_chart_type_code
    #             if self.R0 == False:
    #                 raise ValidationError('字段 R0 不能能空')
    #             request_args['R0'] = self.R0
    #
    #         elif self.control_chart_type_code == 'x_bar_standard_deviation_chart':
    #             request_args['control_chart_type'] = self.control_chart_type_code
    #             if self.s0 == False:
    #                 raise ValidationError('字段 s0 不能能空')
    #             request_args['s0'] = self.s0
    #
    #         elif self.control_chart_type_code == 'median_range_chart':
    #             raise ValidationError('中位数控制图没有基于给定值，创建标准值的方法')
    #
    #         key_list = ['X0', 'u', 'sigma0']
    #         for key in key_list:
    #             if self[key] == False:
    #                 raise ValidationError('字段 %s 不能为空' % key)
    #             else:
    #                 request_args[key] = self[key]
    #         quantity_args = self.get_quantity_data()
    #         request_args['sub_group_size'] = self.sub_group_size
    #         request_args['valid_num'] = quantity_args['round_precision']
    #
    #         url = 'http://127.0.0.1:8080/SPC/get_static_measurement_control_lines'
    #         print '-----------', url
    #         headers = {'content-type': 'application/json'}
    #         response = requests.post(url, data=json.dumps(request_args), headers=headers)
    #         if response is not None:
    #             # 请求返回的数据
    #             response_data = response.json()
    #             print '!!!!!!!!%s' % response_data['message']
    #             if response_data['success']:
    #                 result = response_data['result']
    #                 print '-----------', result
    #                 if result is not None:
    #                     self.up_ccl = result['up_ccl']
    #                     self.up_ucl = result['up_ucl']
    #                     self.up_lcl = result['up_lcl']
    #                     self.down_ccl = result['down_ccl']
    #                     self.down_ucl = result['down_ucl']
    #                     self.down_lcl = result['down_lcl']
    #         else:
    #             raise ValidationError('本次请求失败，响应的数据为空')
    #
    #     if self.quality_quantity_character == 'quality_character' and self.control_chart_type_code and self.set_standard_value:
    #         request_args = dict()
    #         if not self.is_constant_sub_group_size:
    #             raise ValidationError('使用给定值创建标准限，是在 子组容量大小固定的情况下使用的')
    #
    #         # 针对不同的 控制图，进行不同处理
    #
    #         if self.control_chart_type_code in ['defect_rate_p_chart', 'unit_defect_number_u_chart',
    #                                             'defect_number_np_chart', 'defect_number_c_chart', 'p_to_z_chart']:
    #             # 针对不同的控制图，获得不同的参数值
    #             request_args['control_chart_type'] = self.control_chart_type_code
    #             request_args['sub_group_size'] = self.sub_group_size
    #             request_args['valid_num'] = 4
    #             if self.control_chart_type_code == 'defect_rate_p_chart':
    #                 if self.p0 == False:
    #                     raise ValidationError('字段 p0 不能能空')
    #                 request_args['p0'] = self.p0
    #             elif self.control_chart_type_code == 'unit_defect_number_u_chart':
    #                 if self.u0 == False:
    #                     raise ValidationError('字段 p0 不能能空')
    #                 request_args['u0'] = self.u0
    #
    #             elif self.control_chart_type_code == 'defect_number_np_chart':
    #                 # 此处需要进行处理
    #                 if self.p0 == False:
    #                     raise ValidationError('字段 p0 不能能空')
    #                 request_args['np0'] = self.p0 * self.sub_group_size
    #
    #             elif self.control_chart_type_code == 'defect_number_c_chart':
    #                 if self.c0 == False:
    #                     raise ValidationError('字段 c0 不能能空')
    #                 request_args['c0']=self.c0
    #
    #             url = 'http://127.0.0.1:8080/SPC/get_static_count_control_lines'
    #             headers = {'content-type': 'application/json'}
    #             response = requests.post(url, data=json.dumps(request_args), headers=headers)
    #             if response :
    #                 # 请求返回的数据
    #                 response_data = response.json()
    #                 print '!!!!!!!!%s' % response_data['message']
    #                 if response_data['success']:
    #                     result = response_data['result']
    #                     print '-----------', result
    #                     if result is not None:
    #                         self.up_ccl = result['up_ccl']
    #                         self.up_ucl = result['up_ucl']
    #                         self.up_lcl = result['up_lcl']
    #             else:
    #                 raise ValidationError('本次请求失败，响应的数据为空')



    # 动态创建 p_to_z_chart

    @api.multi
    def get_dynamic_count_control_limit(self):

        # 先判断 需要的字段是否为False
        print self.inspection_series
        print self.control_chart_type

        if not self.inspection_series:
            raise ValidationError('字段 检验系列批 不能为空')
        if not self.control_chart_type:
            raise ValidationError('字段 控制图类型 不能为空')

        request_args = None
        if self.control_chart_type_code and self.control_chart_type_code == 'p_to_z_chart':
            request_args = dict(control_chart_type='p_to_z_chart')

        elif self.is_constant_sub_group_size == True:
            if not self.sub_group_size:
                raise ValidationError('字段 子组大小 不能为空')

            
            # 获取请求参数的数据
            series_num = self.inspection_series_num
            print '--------------------------',self.inspection_series_num

            series_len = len(series_num)
            # 根据系列批获取 观测的数据
            # 判断批号的组成是否规范
            if series_len > 6:
                task_records = self.env['qm.insp.task.record'].search(
                    [('lot_num', 'like', series_num[0:series_len - 6])])
                print '------------------11',task_records,len(task_records)
                # 配凑 观测值数据
                n_defect_sequence = list()
                if len(task_records) > 20:
                    # 判断n是否相等
                    sample_counts = self.sub_group_size
                    record_counts = 0
                    for task_record in task_records:
                        # 判断每一条记录的 子组数是否相等
                        if task_record.sample_count == sample_counts:
                            n_defect_sequence.append((sample_counts, task_record.d))
                            record_counts += 1
                    # 同一批的数量 >20 ，才有效
                    if len(n_defect_sequence) > 20:
                        # 构造请求参数
                        request_args = dict(sequence=n_defect_sequence,
                                            control_chart_type=self.control_chart_type_code,
                                            valid_num=4, is_constant_sub_group_size=self.is_constant_sub_group_size)
                    else:
                        raise ValidationError('子组大小为%s的子组数小于20,不能进行动态创建标准值'%sample_counts)
                else:
                    raise ValidationError('子组数小于20,不能进行动态创建标准值')
            else:
                raise ValidationError('检验系列批构造存在问题')

        # 子组大小不固定
        elif self.is_constant_sub_group_size == False:
            print '--------------------------',self.inspection_series_num
            # 获取请求参数的数据
            series_num = self.inspection_series_num
            series_len = len(series_num)
            # 根据系列批获取 观测的数据
            # 判断批号的组成是否规范
            if series_len > 6:
                task_records = self.env['qm.insp.task.record'].search(
                    [('lot_num', 'like', series_num[0:series_len - 6])])
                print '----------------------------',task_records
                # 配凑 观测值数据
                n_defect_sequence = list()
                if len(task_records) > 20:
                    # 判断n是否相等
                    for task_record in task_records:
                        # 判断每一条记录的 子组数是否相等
                        n_defect_sequence.append((task_record.sample_count, task_record.d))

                    # 构造请求参数
                    request_args = dict(sequence=n_defect_sequence,
                                        control_chart_type=self.control_chart_type_code,
                                        valid_num=4, is_constant_sub_group_size=self.is_constant_sub_group_size)
                else:
                    raise ValidationError('子组数小于20,不能进行动态创建标准值')
            else:
                raise ValidationError('检验系列批构造存在问题')

        # 进行请求
        if request_args is None:
            raise ValidationError('请求参数为 空')
        url = 'http://127.0.0.1:8080/SPC/get_dynamic_count_control_lines'
        headers = {'content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(request_args), headers=headers)
        # 对请求后的数据进行处理
        if response:
            # 请求返回的数据
            response_data = response.json()
            print '!!!!!!!!%s' % response_data['message']
            if response_data['success']:
                result = response_data['result']
                # 请求结果不为空，怎进行更新数据
                if result:
                    if self.is_constant_sub_group_size == True:
                        self.up_ccl = result['up_ccl']
                        self.up_ucl = result['up_ucl']
                        self.up_lcl = result['up_lcl']
                    elif self.is_constant_sub_group_size == False:
                        self.up_ccl = result['up_ccl']
                        self.up_ucl = -1
                        self.up_lcl = -1
        else:
            raise ValidationError('本次请求失败，响应的数据为空')

    # 动态创建 控制限
    def get_dynamic_measurement_limit(self):
        # 先判断 需要的字段是否为False
        if not self.inspection_series:
            raise ValidationError('字段 检验系列批 不能为空')
        if not self.control_chart_type:
            raise ValidationError('字段 控制图类型 不能为空')
        if not self.is_constant_sub_group_size:
            raise ValidationError('字段 子组大小恒定 未勾选')
        if self.sub_group_size == False:
            raise ValidationError('字段 子组大小 不能为空')
        # 不同控制图 ， 子组的范围不同
        control_chart_type = self.control_chart_type_code
        sub_group_size = self.sub_group_size

        if control_chart_type == 'x_bar_range_chart' and (sub_group_size < 2 or sub_group_size > 25):
            raise ValidationError('均值-极差控制图的子组大小取值为[2,25]')

        elif control_chart_type == 'single_value_moving_range_chart' and sub_group_size != 1:
            raise ValidationError('单值-移动极差控制图的子组大小取值为1')

        elif control_chart_type == 'median_range_chart' and (sub_group_size < 2 or sub_group_size > 10):
            raise ValidationError('中位数控制图的子组大小取值为[2,10]')

        elif control_chart_type == 'x_bar_standard_deviation_chart' and (sub_group_size < 2 or sub_group_size > 25):
            raise ValidationError('均值-标准差控制图的子组大小取值为[2,25]')

        if self.round_precision == False:
            raise ValidationError('字段 舍入精度 不能为空')

        # 获取请求参数的数据
        request_args = None

        # 根据系列批获取 观测的数据
        series_num = self.inspection_series_num
        series_len = len(series_num)

        # 判断批号的组成是否规范
        if series_len < 6:
            raise ValidationError('检验系列批构造存在问题')

        # 根据批次号，获取观测数据
        task_records = self.env['qm.insp.task.record'].search(
            [('lot_num', 'like', series_num[0:series_len - 6])])

        print '------------------task_records',task_records,len(task_records),series_num

        # task_records = self.env['qm.insp.task.record'].search(
        #     [('lot_num', '=', series_num)])

        # 配凑 观测值数据
        # 判断获得数据是否有 20条数据
        if len(task_records) > 20:
            # 判断n是否相等

            record_count = 0
            sequence = list()

            for task_record in task_records:
                # 通过 子组大小 过滤 记录
                if task_record.sample_count == sub_group_size:
                    # 获取具体的观测值
                    single_results = self.env['qm.result.single.quantify'].search(
                        [('task_result_id', '=', task_record.id)])
                    sub_sequence = list()
                    for single_result in single_results:
                        if single_result:
                            sub_sequence.append(single_result['sample_insp_avg'])
                            record_count += 1
                    sequence.append(sub_sequence)
            if record_count < 20:
                raise ValidationError('子组大小为%s的子组数小于20,不能进行动态创建标准值' % sub_group_size)
            # 构造请求参数
            request_args = dict(sequence=sequence,
                                control_chart_type=control_chart_type,
                                sub_group_size=sub_group_size,
                                valid_num=4, is_constant_sub_group_size=self.is_constant_sub_group_size)

        else:
            raise ValidationError('子组数小于20,不能进行动态创建标准值')

        # 进行请求
        if request_args is None:
            raise ValidationError('请求参数为 空')
        url = 'http://127.0.0.1:8080/SPC/get_dynamic_measurement_control_lines'
        headers = {'content-type': 'application/json'}

        response = None
        try:
            response = requests.post(url, data=json.dumps(request_args), headers=headers)
        except Exception as e:
            print '----Error in method model_sample_plan.create_count_sample_table: the request failed'
            raise ValidationError('请求服务失败或服务器未开启')


        # 对请求后的数据进行处理
        if response:
            # 请求返回的数据
            response_data = response.json()
            print '!!!!!!!!%s' % response_data['message']
            if response_data['success']:
                result = response_data['result']
                # 请求结果不为空，怎进行更新数据
                if result:
                    self.up_ccl = result['up_ccl']
                    self.up_ucl = result['up_ucl']
                    self.up_lcl = result['up_lcl']

                    self.down_ccl = result['down_ccl']
                    self.down_ucl = result['down_ucl']
                    self.down_lcl = result['down_lcl']
        else:
            raise ValidationError('本次请求失败，响应的数据为空')

    @api.multi
    def create_control_line(self):
        # 子组大小不固定不能创建标准值
        if not self.is_constant_sub_group_size:
            raise ValidationError('子组大小不恒定，不能创建标准值')

        # 子组大小固定，创建控制限
        # 根据不同的  控制图类型创建不同的标准限
        if not self.quality_quantity_character:
            raise ValidationError('字段 特性类型 不能为空')

        # 创建计量型标准线
        if self.quality_quantity_character == 'quantity_character':
            # 静态创建标准值
            if self.set_standard_value:
                #pass
                self.get_static_measurement_line()

            # 动态创建标准值
            else:
                # pass
                self.get_dynamic_measurement_limit()

        # 创建计数标准线
        elif self.quality_quantity_character == 'quality_character':
            # 静态创建标准值
            if self.set_standard_value:
                # pass
                self.get_static_count_line()
            # 动态创建标准值
            else:
                #pass
                self.get_dynamic_count_control_limit()









                # 静态创建标准值

                # if self.sub_group_size == False:
                #     raise ValidationError('字段 子组大小 不能为空')
                #
                # if self.quality_quantity_character == 'quantity_character' and self.control_chart_type_code and self.set_standard_value:
                #     request_args = dict()
                #     if not self.is_constant_sub_group_size:
                #         raise ValidationError('使用给定值创建标准限，是在 子组容量大小固定的情况下使用的')
                #
                #     if self.control_chart_type_code in ['x_bar_range_chart', 'single_value_moving_range_chart']:
                #         request_args['control_chart_type'] = self.control_chart_type_code
                #         if self.R0 == False:
                #             raise ValidationError('字段 R0 不能能空')
                #         request_args['R0'] = self.R0
                #
                #     elif self.control_chart_type_code == 'x_bar_standard_deviation_chart':
                #         request_args['control_chart_type'] = self.control_chart_type_code
                #         if self.s0 == False:
                #             raise ValidationError('字段 s0 不能能空')
                #         request_args['s0'] = self.s0
                #
                #     elif self.control_chart_type_code == 'median_range_chart':
                #         raise ValidationError('中位数控制图没有基于给定值，创建标准值的方法')
                #
                #     key_list = ['X0', 'u', 'sigma0']
                #     for key in key_list:
                #         if self[key] == False:
                #             raise ValidationError('字段 %s 不能为空' % key)
                #         else:
                #             request_args[key] = self[key]
                #     quantity_args = self.get_quantity_data()
                #     request_args['sub_group_size'] = self.sub_group_size
                #     request_args['valid_num'] = quantity_args['round_precision']
                #
                #     url = 'http://127.0.0.1:8080/SPC/get_static_measurement_control_lines'
                #     print '-----------', url
                #     headers = {'content-type': 'application/json'}
                #     response = requests.post(url, data=json.dumps(request_args), headers=headers)
                #     if response :
                #         # 请求返回的数据
                #         response_data = response.json()
                #         print '!!!!!!!!%s' % response_data['message']
                #         if response_data['success']:
                #             result = response_data['result']
                #             print '-----------', result
                #             if result is not None:
                #                 self.up_ccl = result['up_ccl']
                #                 self.up_ucl = result['up_ucl']
                #                 self.up_lcl = result['up_lcl']
                #                 self.down_ccl = result['down_ccl']
                #                 self.down_ucl = result['down_ucl']
                #                 self.down_lcl = result['down_lcl']
                #     else:
                #         raise ValidationError('本次请求失败，响应的数据为空')
                #
                # if self.quality_quantity_character == 'quality_character' and self.control_chart_type_code and self.set_standard_value:
                #     request_args = dict()
                #     if not self.is_constant_sub_group_size:
                #         raise ValidationError('使用给定值创建标准限，是在 子组容量大小固定的情况下使用的')
                #
                #     # 针对不同的 控制图，进行不同处理
                #
                #     if self.control_chart_type_code in ['defect_rate_p_chart', 'unit_defect_number_u_chart',
                #                                         'defect_number_np_chart', 'defect_number_c_chart', 'p_to_z_chart']:
                #         # 针对不同的控制图，获得不同的参数值
                #         request_args['control_chart_type'] = self.control_chart_type_code
                #         request_args['sub_group_size'] = self.sub_group_size
                #         request_args['valid_num'] = 4
                #         if self.control_chart_type_code == 'defect_rate_p_chart':
                #             if self.p0 == False:
                #                 raise ValidationError('字段 p0 不能能空')
                #             request_args['p0'] = self.p0
                #         elif self.control_chart_type_code == 'unit_defect_number_u_chart':
                #             if self.u0 == False:
                #                 raise ValidationError('字段 p0 不能能空')
                #             request_args['u0'] = self.u0
                #
                #         elif self.control_chart_type_code == 'defect_number_np_chart':
                #             # 此处需要进行处理
                #             if self.p0 == False:
                #                 raise ValidationError('字段 p0 不能能空')
                #             request_args['np0'] = self.p0 * self.sub_group_size
                #
                #         elif self.control_chart_type_code == 'defect_number_c_chart':
                #             if self.c0 == False:
                #                 raise ValidationError('字段 c0 不能能空')
                #             request_args['c0'] = self.c0
                #
                #         url = 'http://127.0.0.1:8080/SPC/get_static_count_control_lines'
                #         headers = {'content-type': 'application/json'}
                #         response = requests.post(url, data=json.dumps(request_args), headers=headers)
                #         if response :
                #             # 请求返回的数据
                #             response_data = response.json()
                #             print '!!!!!!!!%s' % response_data['message']
                #             if response_data['success']:
                #                 result = response_data['result']
                #                 print '-----------', result
                #                 if result is not None:
                #                     self.up_ccl = result['up_ccl']
                #                     self.up_ucl = result['up_ucl']
                #                     self.up_lcl = result['up_lcl']
                #         else:
                #             raise ValidationError('本次请求失败，响应的数据为空')

    @api.onchange('control_chart_type')
    def onchange_control_chart_type(self):
        if self.control_chart_type_code in ['x_bar_range_chart', 'x_bar_standard_deviation_chart',
                                            'single_value_moving_range_chart', 'median_range_chart',
                                            'defect_number_np_chart', 'defect_number_c_chart']:
            self.is_constant_sub_group_size = True
        else:
            self.is_constant_sub_group_size = False

        if self.control_chart_type_code in ['defect_rate_p_chart', 'defect_number_np_chart', 'p_to_z_chart']:
            # 不合格品数检验
            self.accept_depend = 'depend_1'
        elif self.control_chart_type_code in ['unit_defect_number_u_chart', 'defect_number_c_chart']:
            # 不合格数检验
            self.accept_depend = 'depend_2'
        else:
            self.accept_depend = False

        # 将标准限的值设置为 False，避免遗留数据造成假象，造成影响
        self.up_ccl = False
        self.up_ucl = False
        self.up_lcl = False
        self.down_ccl = False
        self.down_ccl = False
        self.down_ccl = False

        if self.set_standard_value == True:
            self.sub_group_size = False
            self.X0 = False
            self.u = False
            self.R0 = False
            self.s0 = False
            self.sigma0 = False
            self.p0 = False
            self.u0 = False
            self.np0 = False
            self.c0 = False

        # 进行约束性判定
        if self.quality_quantity_character == 'quality_character' and self.accept_depend != False and self.spc_yn.accept_depend != self.accept_depend:
            control_chart_type_dict = {'x_bar_range_chart': '均值-极差控制图', 'x_bar_standard_deviation_chart': '均值-标准差控制图',
                                       'single_value_moving_range_chart': '单值-移动极差控制图', 'median_range_chart': '中位数控制图',
                                       'defect_rate_p_chart': '不合格品率控制图', 'unit_defect_number_u_chart': '单位缺陷数控制图',
                                       'defect_number_np_chart': '不合格品数控制图', 'defect_number_c_chart': '缺陷数控制图',
                                       'p_to_z_chart': 'p图等效Z控制图'}
            raise ValidationError('定性接受性判定，与检验项目的不同，不能生成 %s！' % control_chart_type_dict[self.control_chart_type_code])

    @api.onchange('spc_yn')
    def onchange_spc_yn(self):
        if self.quality_quantity_character == 'quantity_character':
            #self.round_precision = self.spc_yn.round_precision
            if self.spc_yn.result_record_way != 'single_record':
                raise ValidationError('特性类型为定量时，结果记录方式不是单个记录，不能生成 spc 图！')
        # 不同条件下，有不同的值，只能存储一份
        self.control_chart_type = False

        # 使用程序进行解析批次号方法
        # @api.multi
        # def get_sub_code(self, serial_number):
        #     # 截取前后字符
        #     index = 0
        #     serial_number_len = len(serial_number)
        #     if serial_number_len >= 6:
        #         code_dict = dict(material_code=' ', supplier_code='S', production_line_code='P', equipment_code='E',
        #                          client_code='C', date_code=' ')
        #
        #         code_dict['material_code'] = serial_number[0:6]
        #         if serial_number_len >= 12:
        #             code_dict['date_code'] = serial_number[-6:]
        #             # 不确定字段的起始位置
        #             index += 6
        #             # 不确定字段的结束位置
        #             right_index = serial_number_len - 6
        #
        #             while (index + 7 <= right_index):
        #                 sub_code = serial_number[index:index + 7]
        #                 for key in code_dict:
        #                     if code_dict[key] == sub_code[0]:
        #                         code_dict[key] = sub_code
        #                 index += 7
        #         # 对数据结果进行统一处理
        #         for key in code_dict:
        #             if len(code_dict[key]) < 6:
        #                 code_dict[key] = None
        #         return code_dict

        # #根据批次号，将批次号 解析为对应 应用意义
        # @api.onchange('inspection_series')
        # def get_sub_code_name(self):
        #     serial_number = self.inspection_series.name
        #     if serial_number != False:
        #         code_dict = self.get_sub_code(serial_number)
        # if code_dict:
        #     material_code = code_dict['material_code']
        #     supplier_code = code_dict['supplier_code']
        #     production_line_code = code_dict['production_line_code']
        #     equipment_code = code_dict['equipment_code']
        #     client_code = code_dict['client_code']
        #     date_code = code_dict['date_code']
        #
        #     # if material_code:
        # #     #     self.env['qm.product.num'].search([('name', '=', material_code)])
        # supplier_record_id = self.env['qm.partner.num'].search([('name', '=', supplier_code)])
        # self.supplier_id = supplier_record_id[0].belong_partner
        # equipment_record_id=self.env['qm.equipment.num'].search([('name', '=', equipment_code)])
        # self.inspect_equipment=equipment_record_id[0].belong_equipment


# 控制图类型, 标记 计量 或 计数类型
class spc_control_chart_type(models.Model):
    _name = 'spc.control_chart_type'
    name = fields.Char(string='控制图类型')
    control_chart_type_code = fields.Char(string='控制图类型码')
    # 如果字段发生变化，添加新的字段，通过添加方法进行动态转换
    quality_quantity_character = fields.Selection([('quantity_character', '定量特性'), ('quality_character', '定性特性')],
                                                  string='定性定量检验')
