# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError
import requests
import json


class InspectionOrder(models.Model):
    _name = "qm.inspection.order"

    PLAN_TYPE = [
        ('import_material_insp', '采购订单的收货检验'),
        ('making_product_insp', '在制品检验'),
        ('making_procedure_insp', '制程终验'),
        ('export_good_insp', '出货检验')
    ]

    ACCEPTANCE_TYPE = [
        ('acceptance_1', '接收'),
        ('acceptance_2', '不接收')
    ]

    KEY_PART_DEGREE = [
        ('class_a', 'A(关键)'),
        ('class_b', 'B(重要)'),
        ('class_c', 'C(一般)')
    ]

    # 标题数据
    name = fields.Char('检验单', required=True)
    lot_num = fields.Char(string='检验批编号', required=True)
    # 表头数据
    insp_plan_type = fields.Selection(PLAN_TYPE, string='检验类型', required=True)
    plan_id = fields.Many2one('qm.plan.instruction', string='检验计划', required=True)
    product_id = fields.Many2one(related='plan_id.product_id', string="产品名称")
    product_num = fields.Char(related='product_id.product_num', string='产品编码')
    product_chart = fields.Char(related='product_id.product_chart', string='产品图号')
    sample_plan_id = fields.Many2one(related='plan_id.sample_plan_id', string='采样方案', required=True)
    lot_count = fields.Integer(string='检验批数量', required=True)
    sample_count = fields.Integer(string='采样数量')
    key_parts_degree = fields.Selection(related='product_id.importance_category', string="零部件重要度")

    response_json_data = fields.Char('请求的json数据')

    factory = fields.Many2one(related='product_id.factory_id', string='工厂')
    supplier_id = fields.Many2one('res.partner', string='供应商')
    origin = fields.Char(related='product_id.godown_origin', string='源单据')
    inspector = fields.Many2one(related='plan_id.test_charge_persion', string='检验责任人')
    insp_start_time = fields.Datetime(string='检验开始时间', default=fields.Date.today())
    insp_finish_time = fields.Datetime(string='检验完成时间')
    again_commit_lot = fields.Boolean(string="再提交批")
    trans_rule_id = fields.Many2one('qm.check.degree.trans.rule', string="动态转移规则")

    # 任务列表数据
    task_ids = fields.One2many('qm.insp.task', 'inspection_order_id', '任务列表')
    workstage_one = fields.One2many(related='plan_id.workstage_one', string='总工序')

    # 使用决策数据
    policy = fields.Many2one('qm.usage.decision', string="使用决策")
    quality_score = fields.Integer(string="质量计分")
    trans_score = fields.Integer(string="转移得分")
    aptitude_score = fields.Integer(string="资格得分")
    credit_score = fields.Integer(string="信用得分")

    accept_decide = fields.Selection(ACCEPTANCE_TYPE, "自动判定结果")
    next_todo = fields.Char(string="后续操作")

    _defaults = {'name': lambda self, cr, uid, context: self.pool['ir.sequence'].next_by_code(cr, uid,
                                                                                              'qm.inspection.order.name',
                                                                                              context=context)}
    '''批量值触发--REST查表过程'''

    @api.multi
    @api.onchange('lot_count')
    def _onchange_equipment(self):
        self.ensure_one()
        # 获取检验计划对应的采样方案对象
        sample_plan = self.sample_plan_id
        # 依据采样类型执行不同的检验标准:
        sampling_type = sample_plan.sampling_standard
        # 固定采样
        if sampling_type == 'fixed_sample':
            self.sample_count = 100
        # 100%采样
        elif sampling_type == 'complete_inspection':
            self.sample_count = self.lot_count
        # 百分比采样
        elif sampling_type == 'percentage_inspection':
            sample_percentage = sample_plan.sample_percentage
            self.sample_count = self.lot_count * sample_percentage
        # 使用采样方案
        elif sampling_type == 'use_sample_scheme':
            # 检验标准
            gb_standard_name = sample_plan.gb_standard_name
            # 检验标准下的抽样检验类型(采样方案添加了新的字段标识：样本抽样类型码)
            sample_type_code = sample_plan.sample_type_code
            # 检验严格度（暂时先从该处获取）
            check_degree = sample_plan.check_degree_name.check_degree_code
            # 检验水平
            check_level = sample_plan.check_level_name
            # aql (string类型)
            aql = sample_plan.aql_name
            # 批量值
            lot_size = self.lot_count
            # 确认批量范围
            lot_min = self.plan_id.lot_min
            lot_max = self.plan_id.lot_max
            if lot_size <= lot_max and lot_size >= lot_min:
                # 服务器地址
                if gb_standard_name == 'GB/T2828.1-2012':
                    url = 'http://127.0.0.1:5000/sample/excel'
                elif gb_standard_name == 'GB/T6378.1-2008':
                    url = 'http://127.0.0.1:5000/GBT6378.1-2008/read_table'
                # 构建rest服务查表过程所需参数
                values = {
                    "sample_type": sample_type_code,
                    "check_degree": check_degree,
                    "check_level": check_level,
                    "lot_size": lot_size,
                    "aql": aql
                }
                headers = {'content-type': 'application/json'}
                # 调用rest服务开始查表过程
                response = None
                try:
                    response = requests.post(url, data=json.dumps(values), headers=headers)
                except Exception as e:
                    print '----Error in method model_qm_insp_order._onchange_equipment: the request failed'
                    raise ValidationError('请求服务失败或服务器未开启')

                if response :
                    # 读取rest服务的返回值(ODOO与rest服务的交互使用Json数据类型)

                    if gb_standard_name == 'GB/T2828.1-2012':
                        jsonData = response.json()
                    elif gb_standard_name == 'GB/T6378.1-2008':
                        response_data = response.json()
                        if response_data['success']:
                            jsonData = response.json()['result']
                        else:
                            raise ValidationError('查表服务返回数据为空，不能生成有效样本量！')
                    # 赋值样本量

                    sample_size = jsonData['sample_size']
                    print sample_size, '---------------------------'
                    if sample_size is not None:
                        if sample_size > self.lot_count:
                            self.sample_count = self.lot_count
                            raise ValidationError('查表返回样本量值大于批量值为：' + str(sample_size) + '，建议全检！')
                        else:
                            self.sample_count = sample_size
                        self.response_json_data = jsonData
                        # self.ac = float(jsonData["ac"])
                        # self.re = float(jsonData["re"])
                        # self.ac_before = float(jsonData["ac_before"])
                        # self.re_before = float(jsonData["re_before"])
                        # print self.sample_count, self.ac, self.re, self.ac_before, self.re_before, '============'
                else:
                    raise ValidationError('查表服务返回数据为空，不能生成有效样本量！')
            else:
                raise ValidationError('填入批量值不在规定的批量范围内，请从新填写！')
        elif sampling_type is False:
            print '采样方案采样类型不配，不能生成有效样本量！'
        else:
            raise ValidationError('采样方案采样类型不配，不能生成有效样本量！')

    '''动态转移规则触发--检验严格度转移服务'''

    @api.multi
    @api.onchange('trans_rule_id')
    def get_trans_rule_records(self):
        self.ensure_one()
        # 基础字段
        product_id = self.product_id.id
        db_name = 'flask'
        factory_name = self.factory.name
        lot_num = self.lot_num
        check_degree = self.sample_plan_id.check_degree_id.name.check_degree_code

        # 获取对应动态转移规则
        trans_rule_id = self.trans_rule_id
        # 需要资格验证
        is_certificate = trans_rule_id.is_certificate
        # s法与σ法的转换
        is_certificate = trans_rule_id.is_certificate
        # 数据存储
        lines = []
        # 获取总规则列表的对象集
        condition_list_ids = trans_rule_id.condition_list_ids
        # 非空判断
        if condition_list_ids is not None:
            # 规则列表数量统计
            condition_list_count = len(condition_list_ids)
            if condition_list_count is not 0:
                for x in range(condition_list_count):
                    # 规则对象
                    condition_list_id = condition_list_ids[x]
                    # 获取类型编号
                    type_num = condition_list_id.trans_rule_type.num
                    # 判断条件
                    condition_and_or = condition_list_id.and_or_one
                    # 获取条件编号
                    condition_one_num = condition_list_id.condition_one.num
                    condition_two_num = condition_list_id.condition_two.num
                    condition_three_num = condition_list_id.condition_three.num
                    condition_four_num = condition_list_id.condition_four.num
                    # 单条动态数据统计填充
                    line_item = {
                        'type_num': type_num,
                        'condition_and_or': condition_and_or,
                        'condition_one_num': condition_one_num,
                        'condition_two_num': condition_two_num,
                        'condition_three_num': condition_three_num,
                        'condition_four_num': condition_four_num
                    }
                    # 数据集合
                    lines += [line_item]
                    print lines, '*************************', len(lines)
            else:
                raise ValidationError('规则列表数量统计为零！')
        else:
            raise ValidationError('获取总规则列表的对象集为空！')

        # 总数据集
        values = []
        # 当前检验严格度为--正常--的数据处理
        if check_degree is "normal_check":
            size = len(lines)
            if size is not 0:
                count_num = 0
                for x in range(size):
                    read_data = lines[x]

                    if read_data['type_num'] is 1 or read_data['type_num'] is 3:
                        data_item = {
                            'condition_and_or': read_data["condition_and_or"],
                            'condition_one_num': read_data["condition_one_num"],
                            'condition_two_num': read_data["condition_two_num"],
                            'condition_three_num': read_data["condition_three_num"],
                        }
                        values += [data_item]
                        count_num += 1
                if count_num is 0:
                    raise ValidationError('当前检验严格度为动态规则中，未配置正常转移项！')
        # 当前检验严格度为--加严--的数据处理
        elif check_degree is "tighted_check":
            size = len(lines)
            if size is not 0:
                count_num = 0
                for x in range(size):
                    read_data = lines[x]

                    if read_data['type_num'] is 4 or read_data['type_num'] is 5:
                        data_item = {
                            'condition_and_or': read_data["condition_and_or"],
                            'condition_one_num': read_data["condition_one_num"],
                            'condition_two_num': read_data["condition_two_num"],
                            'condition_three_num': read_data["condition_three_num"],
                        }
                        values += [data_item]
                        count_num += 1
                if count_num is 0:
                    raise ValidationError('当前检验严格度为动态规则中，未配置加严转移项！')
        # 当前检验严格度为--放宽--的数据处理
        elif check_degree is "reduced_check":
            size = len(lines)

            if size is not 0:
                count_num = 0
                for x in range(size):
                    read_data = lines[x]
                    if read_data['type_num'] is 2:
                        data_item = {
                            'condition_and_or': read_data["condition_and_or"],
                            'condition_one_num': read_data["condition_one_num"],
                            'condition_two_num': read_data["condition_two_num"],
                            'condition_three_num': read_data["condition_three_num"],
                        }
                        values += [data_item]
                        count_num += 1
                if count_num is 0:
                    raise ValidationError('当前检验严格度为动态规则中，未配置加放宽移项！')
        else:
            raise ValidationError('当前检验严格度为动态规则中，未配置加放宽移项！')
        data_base = {
            'product_id': product_id,
            'db_name': db_name,
            'factory_name': factory_name,
            'lot_num': lot_num,
            'check_degree': check_degree,
        }
        values += [data_base]

        print product_id, db_name, factory_name, lot_num, check_degree, "*********************"

        print values, "&&&&&&&&&&&"

    '''检验计划触发--任务列表刷新'''

    @api.onchange('plan_id')
    def get_insp_plan_records(self):
        self.ensure_one()
        # 表头数据填充处理
        plan_id = self.plan_id
        # if plan_id.insp_plan_type == "import_material_insp":
        #     if plan_id.partner_object == "partners":
        #         self.supplier_id = plan_id.supplier_id
        #     elif plan_id.partner_object == "partner_groups":
        #         self.supplier_id = plan_id.product_partner[0].name
        #         print plan_id.product_partner[0].name
        supplier_id = plan_id.supplier_id
        # 数据存储
        lines = []
        # 获取总工序的对象集
        workstage_id = self.workstage_one
        # 非空判断

        if workstage_id is not None:
            # 工序数量统计
            workstage_count = len(workstage_id)
            if workstage_count is not 0:
                for x in range(workstage_count):
                    # 工序对象
                    workstage = workstage_id[x].workstage_id
                    # 工序名称
                    workstage_name = workstage.name
                    # 工作中心
                    work_center = workstage.work_center
                    # 工作描述
                    work_content_desc = workstage.work_content_desc
                    # 该工序下---定性&定量----检验项目数量
                    quality_count = len(workstage.work_procedure_quality_ids_one)
                    quantity_count = len(workstage.work_procedure_quantity_ids_one)
                    # 检验项目总数
                    project_count = quality_count + quantity_count

                    line_item = {
                        'work_procedure_id': workstage,
                        'work_content_desc': work_content_desc,
                        'work_center': work_center,
                        'project_count': project_count,
                        'product_id': self.product_id,
                        'lot_num': self.lot_num,
                        'insp_lot_num': self.name,
                        'insp_state': "state_1"
                    }
                    # 数据集合
                    lines += [line_item]
        self.update({'task_ids': lines, 'supplier_id': supplier_id})

    '''更新任务页的列表数据'''

    def get_insp_plan_records_item(self):
        self.ensure_one()
        # 数据存储
        lines = []
        # 获取总工序的对象集
        workstage_id = self.workstage_one
        # 非空判断
        if workstage_id is not None:
            # 工序数量统计
            workstage_count = len(workstage_id)
            if workstage_count is not 0:
                for x in range(workstage_count):
                    # 工序对象
                    workstage = workstage_id[x].workstage_id
                    # #定性&定量特性
                    lines_qality, lines_quantity = self.update_records(workstage)
                    print u'*************************************：', lines_qality
                    print u'+++++++++++++++++++++++++++++++++++++：', lines_quantity
                    res = self.env['qm.insp.task'].search(
                        [('work_procedure_id', '=', workstage)])
                    line_item = {
                        'record_quality': lines_qality,
                        'record_quantify': lines_quantity
                    }
                    lines += [line_item]
        print lines, '##################################################'

        res.update({'record_quality': lines_qality, 'record_quantify': lines_quantity})

    @api.multi
    def update_records(self, workstage):
        self.ensure_one()
        lines_qality = []
        lines_quantity = []
        # 该工序下定性检验项目数量&定量检验项目的对象集
        quality = workstage.work_procedure_quality_ids_one
        quantity = workstage.work_procedure_quantity_ids_one
        if quality is not None:
            for i in range(len(quality)):
                # 检验项目ID
                project_id = quality[i].insp_project_def_id
                # 特性权重
                importance_degree = project_id.importance_degree
                # 依赖标准
                depend_standard = project_id.sample_plan_id.sample_check_type_id
                # 检验方法
                insp_method_id = project_id.insp_method_id
                # 样本量
                sample_count = self.sample_count
                # Ac值
                ac = self.ac
                # Re值
                re = self.re
                # 结果记录方式
                result_record_way = project_id.result_record_way
                # 结果记录

                line_item = {
                    'project_id': project_id,
                    'importance_degree': importance_degree,
                    'depend_standard': depend_standard,
                    'insp_method_id': insp_method_id,
                    'sample_count': sample_count,
                    'ac': ac,
                    're': re,
                    'result_record_way': result_record_way
                }
                lines_qality += [line_item]

        if quantity is not None:
            for j in range(len(quantity)):
                # 检验项目ID
                project_id = quantity[j].insp_project_def_id
                # 特性权重
                importance_degree = project_id.importance_degree
                # 依赖标准
                depend_standard = project_id.sample_plan_id.sample_check_type_id
                # 检验方法
                insp_method_id = project_id.insp_method_id
                # 样本量
                sample_count = self.sample_count
                # 目标值
                target_value = project_id.target_value
                # 规范上限
                u = project_id.upper_bound_values
                # 规范上限
                l = project_id.lower_bound_values
                line_item = {
                    'project_id': project_id,
                    'importance_degree': importance_degree,
                    'depend_standard': depend_standard,
                    'insp_method_id': insp_method_id,
                    'sample_count': sample_count,
                    'target_value': target_value,
                    'u': u,
                    'l': l
                }
                lines_quantity += [line_item]
        print u'1111111111111111111111：', lines_qality
        print u'2222222222222222222222：', lines_quantity
        return lines_qality, lines_quantity

    # TODO:  zhaoli
    def active_defect_records(self, cr, uid, ids, context=None):
        return None
