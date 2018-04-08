# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError
import requests
import json
import math


class TaskRecord(models.Model):
    _name = "qm.insp.task.record"

    name = fields.Char("样本特性检验单")
    insp_task_record_id = fields.Many2one("qm.insp.task", string="质检工序单")
    qm_inspection_order_id = fields.Many2one("qm.inspection.order", string="质检单")

    # 基础通用数据
    product_id = fields.Many2one('product.template', string="产品")
    product_name = fields.Char(related='product_id.name', string='产品名称')
    insp_lot_num = fields.Char(string='检验批')
    result_record_way = fields.Selection([('single_record', '单个记录'),
                                          ('classified_record', '分类记录'),
                                          ('total_record', '总计记录')], string='记录方式')
    work_procedure_id = fields.Many2one("qm.work_procedure", string="工序")
    sample_plan_id = fields.Many2one("qm.sample_plan", string='采样方案')
    project_type = fields.Selection([('quality', '定性特性'), ('quantity', '定量特性')], string="特性类型")
    project_id = fields.Many2one("qm.insp_project_def", string="检验项目")
    accept_depend = fields.Selection([('depend_1', '不合格品数检验'), ('depend_2', '不合格数检验')], string='接收性判定依据')

    factory = fields.Many2one(related='product_id.factory_id', string='工厂')
    lot_num = fields.Char(string='批次')
    insp_principal = fields.Many2one('res.users', string='检验责任人')
    sample_count = fields.Integer(string='样本量')
    response_json_data = fields.Char(string="请求的json数据")
    measurement_units = fields.Many2one('product.uom', string='计量单位')

    # 定性特性列表独占数据字段
    ac = fields.Float(string="Ac")
    re = fields.Float(string="Re")
    ac_before = fields.Float(string="前一位Ac")
    re_before = fields.Float(string="前一位Re")
    d = fields.Integer(string="d(累积)")
    sample_status_code = fields.Char("检验结果统计码")

    # 定量特性列表独占数据字段
    target_value = fields.Float(string='目标值')
    u = fields.Float(string="规范上限")
    l = fields.Float(string="规范下线")
    # 2016年11月29日14:40:36 added by mlq
    is_sigma = fields.Boolean(string='已知sigma')
    sigma = fields.Float(string="sigma")
    measurement_units = fields.Many2one('product.uom', string='计量单位')
    x_max = fields.Float(string='最大值')
    x_min = fields.Float(string='最小值')
    x_avg = fields.Float(string='平均值')
    s = fields.Float(string='标准差')
    r = fields.Float(string='极差')
    me = fields.Float(string='中位数')
    out_limit_count = fields.Integer(string="d(累积)")
    insp_person = fields.Many2one('res.users', string='检验员')
    insp_date = fields.Date(string='检验日期')
    project_accept = fields.Selection(
        [('result_1', '待验'), ('result_2', '接收'), ('result_3', '不接收'), ('result_4', '不可判定')], string="特性接收判定")

    # 检验结果定义
    single_quality_results = fields.One2many("qm.result.single.quality", "task_result_id", string="定性/单个记录")
    single_quantify_results = fields.One2many("qm.result.single.quantify", "task_result_id", string="定量/单个记录")
    classified_quality_results = fields.One2many("qm.result.classified.quality", "task_result_id", string="定性/分类记录")
    classified_quantify_results = fields.One2many("qm.result.classified.quantify", "task_result_id", string="定量/分类记录")

    '''
    根据样本量值创建样本检验表单
        未能实现自动触发过程
    '''

    @api.multi
    def create_sample_record(self):
        # 每次更新之前清空数据
        self.clear_old_result()
        sample_count = self.sample_count
        # 数据存储
        lines = []
        if sample_count is not None and sample_count != 0:
            # 循环创建记录
            for x in range(sample_count):
                line_item = {
                    'sample_num': x + 1,
                }
                lines.append(line_item)
        if self.result_record_way == 'single_record':
            if self.project_type == 'quality':
                # 定性
                self.update({'single_quality_results': lines})
            elif self.project_type == 'quantity':
                # 定量
                self.update({'single_quantify_results': lines})
            else:
                raise ValidationError('非指定“特性类型”，不能生成样本检测表！')
        else:
            raise ValidationError('记录方式不是“单值记录”，不能生成样本检测表！')

    '''
    统计检验结果的数据内容并赋值(监听)
    '''

    # 单值-定性
    @api.multi
    @api.onchange('single_quality_results')
    def compute_single_quality_defect_counts(self):
        # 置空
        self.sample_status_code = False
        self.d = False
        self.out_limit_count = False
        self.project_accept = False
        single_quality_results = self.single_quality_results
        if single_quality_results is not None:
            records_len = len(single_quality_results)
            if records_len != 0:
                sample_status_code = str()
                defect_count = 0
                count = 0
                for x in range(records_len):
                    if single_quality_results[x].sample_insp_result.name is False:
                        count += 1
                    if single_quality_results[x].sample_insp_result.assess == "assess_2":
                        sample_status_code += '1'
                        defect_count += 1
                    else:
                        sample_status_code += '0'
                self.d = defect_count
                self.sample_status_code = sample_status_code
                # 当所有样本检测完成后开始调用接收性判断服务
                if count == 0:
                    self.handle_acceptance()

    # 单值-定量
    @api.multi
    @api.onchange('single_quantify_results')
    def compute_single_quantify_defect_counts(self):
        # 置空
        self.sample_status_code = False
        self.d = False
        self.out_limit_count = False
        self.project_accept = False
        single_quantify_results = self.single_quantify_results
        # 存在记录
        if single_quantify_results:
            records_len = len(single_quantify_results)
            if records_len != 0:
                # 对数据值，进行初始化
                # 检测后的 d 码
                sample_status_code = str()
                # 在上下线之外的记录的数量
                defect_count = 0
                # 观测值的结果集
                list_data = []
                # 生成记录中的 观测值 是否 全部都有 值
                count = 0
                for x in range(records_len):
                    sample_insp_avg = single_quantify_results[x].sample_insp_avg
                    # 对应该记录具体的观测值，不为空
                    if single_quantify_results[x].sample_insp_result:
                        list_data.append(sample_insp_avg)
                        if sample_insp_avg < self.l or sample_insp_avg > self.u:
                            sample_status_code += '1'
                            defect_count += 1
                        else:
                            # 0 表示正常，1 表示缺陷
                            sample_status_code += '0'
                    else:
                        count += 1
                self.out_limit_count = defect_count
                self.sample_status_code = sample_status_code
                # 更新6个结果值
                # 最大值
                self.x_max = max(list_data)
                # 最小值
                self.x_min = min(list_data)
                # 标准差
                self.s = self.cal_standard_deviation(list_data)
                # 平均值
                self.x_avg = self.cal_mean_value(list_data)
                # 极差
                self.r = self.cal_range(list_data)
                # 中位数
                self.me = self.cal_median(list_data)
                if count == 0:
                    self.handle_quantity_acceptance()

    '''
           计量接受性判断服务
       '''

    # 2016年11月29日14:45:40  added by mlq    根据采样方案的抽样检验类型方法，设置 sigma
    def onchange_is_sigma(self):
        standard_type = self.sample_plan_id.sample_type_code
        if not standard_type:
            raise ValidationError('采样方案的抽样检验类型不能为空')
        if standard_type.find('sigma') != -1:
            self.is_sigma = True
        else:
            self.is_sigma = False

    def handle_quantity_acceptance(self):
        if not self.lot_num:
            raise ValidationError('字段 批次 不能为空！')
        if not self.x_avg:
            raise ValidationError('字段 平均值 不能为空！')
        if not self.response_json_data:
            raise ValidationError('查表结果为空')

        lot_num = self.lot_num
        x_bar = self.x_avg
        s = self.s
        check_degree = self.sample_plan_id.check_degree_id.name.check_degree_code
        json_data = eval(self.response_json_data)

        # 标准类型选择
        standard_id = self.sample_plan_id.gb_standard_id.name
        # 采样类型
        standard_type = self.sample_plan_id.sample_type_code
        # 服务器地址
        sample_count = self.sample_count
        if standard_id == "GB/T6378.1-2008":
            values = {
                "type_code": 0,
                "x_bar": x_bar,
                "s": s,
                "sample_type": standard_type,
                "lot_num": lot_num,
                "check_degree": check_degree,
                "sample_size": sample_count,
            }
            # 根据不同的采样类型，获取不同的参数值


            if standard_type == 'one_side_s_method':
                url = "http://127.0.0.1:5000/GBT6378.1-2008/judge_acceptance_s_method"

                if self.project_id.check_upper_bound and self.project_id.check_lower_bound:
                    raise ValidationError('检验项目中同时勾选规范上限和规范下限,不符合单侧规范限S法要求')
                elif not self.project_id.check_upper_bound and not self.project_id.check_lower_bound:
                    raise ValidationError('检验项目中未勾选规范上限和规范下限中任意一个')
                elif self.project_id.check_upper_bound:
                    values['check_bound'] = 1
                    values['U'] = self.u
                elif self.project_id.check_lower_bound:
                    values['check_bound'] = -1
                    values['L'] = self.l

                if 'normal_k' not in json_data:
                    raise ValidationError('查表结果中没有参数 k')
                values['k'] = json_data['normal_k']
            elif standard_type == "both_side_s_method":
                url = "http://127.0.0.1:5000/GBT6378.1-2008/judge_acceptance_s_method"

                if not self.project_id.check_upper_bound or not self.project_id.check_lower_bound:
                    raise ValidationError('检验项目中未同时勾选规范上限和规范下限,不符合双侧规范限Sigma法要求')
                values['check_bound'] = 0
                values['U'] = self.u
                values['L'] = self.l

                if 'fs' not in json_data:
                    raise ValidationError('查表结果中没有参数 fs')
                values['fs'] = json_data['fs']
                if sample_count == 3 or sample_count == 4:
                    if 'p_star' not in json_data:
                        raise ValidationError('查表结果中没有参数 p_star')
                    if not json_data['p_star']:
                        raise ValidationError('查表结果中，参数为空')
                    values['compare_object'] = json_data['p_star']
                elif sample_count > 4:
                    if 'acceptance_curve' not in json_data:
                        raise ValidationError('查表结果中没有参数 acceptance_curve')
                    if not json_data['acceptance_curve']:
                        raise ValidationError('查表结果中,参数为空')
                    values['compare_object'] = json_data['acceptance_curve']

            elif standard_type == 'one_side_sigma_method':
                url = "http://127.0.0.1:5000/GBT6378.1-2008/judge_acceptance_sigma_method"

                if self.project_id.check_upper_bound and self.project_id.check_lower_bound:
                    raise ValidationError('检验项目中同时勾选规范上限和规范下限,不符合单侧规范限Sigma法要求')
                elif not self.project_id.check_upper_bound and not self.project_id.check_lower_bound:
                    raise ValidationError('检验项目中未勾选规范上限和规范下限中任意一个')
                elif self.project_id.check_upper_bound:
                    values['check_bound'] = 1
                    values['U'] = self.u
                elif self.project_id.check_lower_bound:
                    values['check_bound'] = -1
                    values['L'] = self.l
                # 正常情况下，k 为 normal_k ， 加严一级的k 为 tighted_k
                if 'normal_k' not in json_data:
                    raise ValidationError('查表结果中没有参数 k')
                values['k'] = json_data['normal_k']
                if not self.sigma:
                    raise ValidationError('检验工序中定量特性中字段sigma值不能为空')
                values['sigma'] = self.sigma

            elif standard_type == 'both_side_sigma_method':
                url = "http://127.0.0.1:5000/GBT6378.1-2008/judge_acceptance_sigma_method"
                if not self.project_id.check_upper_bound or not self.project_id.check_lower_bound:
                    raise ValidationError('检验项目中未同时勾选规范上限和规范下限,不符合双侧规范限Sigma法要求')
                values['check_bound'] = 0
                values['U'] = self.u
                values['L'] = self.l

                if not self.sigma:
                    raise ValidationError('检验工序中定量特性中字段sigma值不能为空')
                values['sigma'] = self.sigma
                # 正常情况下，k 为 normal_k ， 加严一级的k 为 tighted_k
                if 'normal_k' not in json_data:
                    raise ValidationError('查表结果中没有参数 k')
                values['k'] = json_data['normal_k']
                if 'f_sigma' not in json_data:
                    raise ValidationError('查表结果中没有参数 f_sigma')
                values['f_sigma'] = json_data['f_sigma']

            headers = {'content-type': 'application/json'}

            # 调用rest服务开始查表过程
            response = None
            try:
                response = requests.post(url, data=json.dumps(values), headers=headers)
            except Exception as e:
                print '----Error in method model_qm_insp_task_record.handle_acceptance: the request failed'
                raise ValidationError('请求服务失败或服务器未开启')
            if response:
                response_args = response.json()
                if response_args['success']:
                    is_acceptance = response_args['result']['is_acceptance']
                    if is_acceptance == 1:
                        self.project_accept = "result_2"
                    elif is_acceptance == -1:
                        self.project_accept = "result_4"
                        raise ValidationError('不接受该过程，在降低过程变异后，在进行抽样检验')
                    elif is_acceptance == 0:
                        self.project_accept = "result_3"
                    else:
                        self.project_accept = "result_1"
                else:
                    raise ValidationError('服务端返回结果为空')
            else:
                print 'response  is none '
                raise ValidationError('服务端返回结果为空')




    # 分类-定性
    @api.multi
    @api.onchange('classified_quality_results')
    def compute_classified_quality_defect_counts(self):
        # 置空
        self.sample_status_code = False
        self.d = False
        self.out_limit_count = False
        self.project_accept = False
        classified_quality_results = self.classified_quality_results
        if classified_quality_results is not None:
            records_len = len(classified_quality_results)
            if records_len != 0:
                sample_status_code = str()
                defect_count = 0
                count = 0
                type_num_all = 0
                for x in range(records_len):
                    type_num_all += classified_quality_results[x].sample_group_count

                    if classified_quality_results[x].sample_insp_code.name is False:
                        count += 1
                    if classified_quality_results[x].sample_insp_code.assess == "assess_2":
                        sample_group_count = classified_quality_results[x].sample_group_count
                        defect_count += sample_group_count
                    else:
                        print '其他为合格不予计算'
                if type_num_all <= self.sample_count:
                    self.d = defect_count
                    self.sample_status_code = sample_status_code
                    # 当所有样本检测完成后开始调用接收性判断服务
                    if count == 0:
                        self.handle_acceptance()
                else:
                    self.sample_status_code = False
                    self.d = False
                    self.out_limit_count = False
                    self.project_accept = False
                    raise ValidationError('分类样本总数量，超出样本数量，请检查！')

    # 分类-定量
    # @api.multi
    # @api.onchange('classified_quantify_results')
    # def compute_single_quantify_defect_counts(self):
    #     # 置空
    #     self.sample_status_code = False
    #     self.d = False
    #     self.out_limit_count = False
    #     self.project_accept = False
    #     single_quantify_results = self.single_quantify_results
    #     if single_quantify_results is not None:
    #         records_len = len(single_quantify_results)
    #         if records_len != 0:
    #             sample_status_code = str()
    #             defect_count = 0
    #             list_data = []
    #             count = 0
    #             for x in range(records_len):
    #                 sample_insp_avg = single_quantify_results[x].sample_insp_avg
    #                 if single_quantify_results[x].sample_insp_result is not False:
    #                     list_data.append(sample_insp_avg)
    #                     if sample_insp_avg < self.l or sample_insp_avg > self.u:
    #                         sample_status_code += '1'
    #                         defect_count += 1
    #                     else:
    #                         sample_status_code += '0'
    #                 else:
    #                     count += 1
    #             self.out_limit_count = defect_count
    #             self.sample_status_code = sample_status_code
    #             # 更新6个结果值
    #             # 1.平均值
    #             self.x_max = max(list_data)
    #             self.x_min = min(list_data)
    #
    #             if count == 0:
    #                 print '此处配置计量检验服务'
    #                 # 调用服务开始


    # 计算平均值
    def cal_mean_value(self, sequence):
        '''
        计算平均值
        :param sequence:
        :return: 平均值
        '''
        sequence_len = len(sequence)
        if sequence_len > 0:
            return sum(sequence) * 1.0 / sequence_len

    # 计算标准差
    def cal_standard_deviation(self, sequence):
        '''
        计算标准差
        :param sequence:
        :return: 标准差
        '''
        sequence_len = len(sequence)
        if sequence_len > 1:
            # sequence 均值
            mean_value = self.cal_mean_value(sequence)
            return math.sqrt(
                sum(map(lambda x, mean_value=mean_value: (x - mean_value) ** 2, sequence)) / (sequence_len - 1))
        return 0

    # 计算中位数
    def cal_median(self, sequence):
        '''
        计算中位数
        :param sequence:
        :return: 中位数
        '''
        sequence_len = len(sequence)
        if sequence_len > 0:
            # 先进行排序
            sequence.sort()
            mid_index = sequence_len / 2
            # 当n为偶数时，中位数等于该组数中间两个数的平均值；当n为奇数时，中位数等于该组数中间的那个数；
            if sequence_len % 2 == 0:
                median = (sequence[mid_index] + sequence[mid_index - 1]) * 0.5
            else:
                median = sequence[mid_index]
            return median
        return 0

    # 计算极差
    def cal_range(self, sequence):
        '''
        计算极差
        :param sequence:  数据序列
        :return:  极差值
        '''
        sequence_len = len(sequence)
        if sequence_len > 0:
            range_value = max(sequence) - min(sequence)
            return range_value

    '''
    单位样本特性--接收性判断过程
    '''

    def handle_acceptance(self):
        # 参量配置
        product_id = self.product_id.id
        db_name = 'flask'
        factory_name = self.factory.name
        supplier_id = 1
        product_line = 1
        check_point = 1
        customer_id = 1
        lot_num = self.lot_num
        d = self.d

        json_data = eval(self.response_json_data)
        ac_before = json_data["before_ac"]
        re_before = json_data["before_re"]
        ac = json_data["ac"]
        re = json_data["re"]

        check_degree = self.sample_plan_id.check_degree_id.name.check_degree_code
        # 类型码为"1"的时候进行转移得分和接收得分的判断，为"0"则只进行接收性的判断
        type_code = 0
        # 构建rest服务查表过程所需参数
        values = {
            "type_code": type_code,
            "product_id": product_id,
            "db_name": db_name,
            "factory_name": factory_name,
            "supplier_id": supplier_id,
            "product_line": product_line,
            "check_point": check_point,
            "customer_id": customer_id,
            "lot_num": lot_num,
            "d": d,
            "ac_before": ac_before,
            "re_before": re_before,
            "ac": ac,
            "re": re,
            "check_degree": check_degree
        }
        # 标准类型选择
        standard_id = self.sample_plan_id.gb_standard_id.name
        standard_type = self.sample_plan_id.sample_type_code
        # 服务器地址
        url = "123"
        if standard_id == "GB/T2828.1-2012":
            if standard_type == "Fraction_one_sample_unfixed":
                url = 'http://127.0.0.1:5000/fenshu/unfixed'
            elif standard_type == "Fraction_one_sample_fixed":
                url = 'http://127.0.0.1:5000/fenshu/fixed'
            elif standard_type == "Integer_one_sample":
                url = 'http://127.0.0.1:5000/GB/T2828.1-2012/judge_sample_acceptance_compute_switching_score'
        if url != "123":
            headers = {'content-type': 'application/json'}
            # 调用rest服务开始查表过程
            response = None
            try:
                response = requests.post(url, data=json.dumps(values), headers=headers)
            except Exception as e:
                print '----Error in method model_qm_insp_task_record.handle_acceptance: the request failed'
                raise ValidationError('请求服务失败或服务器未开启')


            if response :
                # 读取rest服务的返回值(ODOO与rest服务的交互使用Json数据类型)
                jsonData = response.json()
                is_acceptance = jsonData['is_acceptance']
                final_ac_score = float(jsonData["final_ac_score"])
                final_trans_score = float(jsonData["final_trans_score"])
                # 赋值
                if is_acceptance == 1:
                    self.project_accept = "result_2"
                elif is_acceptance == 0:
                    self.project_accept = "result_3"
                elif is_acceptance == -1:
                    self.project_accept = "result_4"
                else:
                    self.project_accept = "result_1"
                self.trans_score = final_ac_score
                self.ac_score = final_trans_score
            else:
                raise ValidationError('查表服务返回数据为空，不能生成有效样本量！')

    '''
    切换记录方式将清空结果记录(监听)
    '''

    @api.onchange('result_record_way')
    def result_record_way_listening(self):
        self.clear_old_result()
        self.update({'single_quality_results': [],
                     'single_quantify_results': [],
                     'classified_quality_results': [],
                     'classified_quantify_results': []
                     })

    '''
    清空结果记录
    '''

    def clear_old_result(self):
        old_records_result = self.env['qm.result.single.quality'].search([('task_result_id', '=', self.id)])
        old_records_result.unlink()
        old_records_result = self.env['qm.result.single.quantify'].search([('task_result_id', '=', self.id)])
        old_records_result.unlink()
        old_records_result = self.env['qm.result.classified.quality'].search([('task_result_id', '=', self.id)])
        old_records_result.unlink()
        old_records_result = self.env['qm.result.classified.quantify'].search([('task_result_id', '=', self.id)])
        old_records_result.unlink()

    '''
    将值更新到工序任务对应项目中
    '''

    # @api.onchange('project_accept')
    # def update_insp_task_state(self):
    #     print '==================================11====='
    #     # if self.project_type is 'quality':
    #     print '==================================22====='
    #     task_quality_records = self.env['qm.insp.task.quality'].search(
    #         [('insp_task_record_id', '=', self.insp_task_record_id.id)])
    #     print '==================================11=====', task_quality_records
    #     task_quality_records.write({'project_accept': self.project_accept})


# 定性/单个记录
class SingleQualityResult(models.Model):
    _name = "qm.result.single.quality"
    task_result_id = fields.Many2one("qm.insp.task.record", string="检验结果记录")
    sample_num = fields.Char(string="样本号")
    sample_insp_result = fields.Many2one('attributes.values', string="检验结果")
    sample_insp_describe = fields.Char(string="检测描述")


# 定量/单个记录
class SingleQuantifyResult(models.Model):
    _name = "qm.result.single.quantify"
    task_result_id = fields.Many2one("qm.insp.task.record", string="检验结果记录")

    sample_num = fields.Char(string="样本号")
    sample_insp_result = fields.Char(string="检验结果")
    sample_insp_num = fields.Integer(string="检验次数")
    measurement_units = fields.Many2one('product.uom', string='计量单位')
    sample_insp_avg = fields.Float(string="检测平均")
    sample_insp_describe = fields.Char(string="检测描述")

    # 单值-定性
    @api.multi
    @api.onchange('sample_insp_result')
    def sample_insp_result_listening(self):
        string_data = self.sample_insp_result
        list = string_data.split(',')
        length = len(list)
        sum = 0.00
        # 计算均值的过程
        for i in range(length):
            item = list[i]
            sum += float(item)
        avg = sum / length
        self.update({'sample_insp_num': length, 'sample_insp_avg': avg})


# 定性/分类记录
class ClassifiedQualityResult(models.Model):
    _name = "qm.result.classified.quality"
    task_result_id = fields.Many2one("qm.insp.task.record", string="检验结果记录")

    sample_insp_code = fields.Many2one('attributes.values', string="结果代码")
    sample_group_count = fields.Integer(string="数量")
    sample_insp_describe = fields.Char(string="检测描述")


# 定量/分类记录
class ClassifiedQuantifyResult(models.Model):
    _name = "qm.result.classified.quantify"
    task_result_id = fields.Many2one("qm.insp.task.record", string="检验结果记录")

    sample_insp_code = fields.Char(string="结果代码")
    sample_insp_u = fields.Integer(string="上边界")
    sample_insp_l = fields.Integer(string="下边界")
    sample_group_count = fields.Integer(string="数量")
    sample_insp_describe = fields.Char(string="检测描述")
