# -*- coding: utf-8 -*-
from openerp import models, fields, api


class InspectionTask(models.Model):
    _name = "qm.insp.task"

    INSP_STATE_TYPE = [
        ('state_1', '待检'),
        ('state_2', '完成'),
    ]

    inspection_order_id = fields.Many2one('qm.inspection.order', string='质量订单')
    # 质检单展示层数据
    name = fields.Many2one(string="工序")
    work_procedure_id = fields.Many2one("qm.work_procedure", string="工序")
    work_content_desc = fields.Char(string='工作内容描述')
    work_center = fields.Many2one('qm.work.center', string='工作中心')
    project_count = fields.Integer(string="检验项目数")
    finish_insp_count = fields.Integer(string="已完成检验数")
    qualified_count = fields.Integer(string="达标特性数")
    unqualified_count = fields.Integer(string="不达标特性数")
    defect_degree_max = fields.Char(string="最高缺陷等级")
    insp_state = fields.Selection(INSP_STATE_TYPE, string="状态")
    # 本层表头数据
    product_id = fields.Many2one('product.template', string="产品")
    factory = fields.Many2one(related='product_id.factory_id', string='工厂')
    lot_num = fields.Char(string='批次')
    insp_lot_num = fields.Char(string='检验批')

    record_quality = fields.One2many('qm.insp.task.quality', 'insp_task_record_id', string="定性特性")
    record_quantify = fields.One2many('qm.insp.task.quantify', 'insp_task_record_id', string="定量特性")

    '''
    定性&定量特性列表刷新
    '''

    @api.multi
    def update_records(self):
        self.ensure_one()
        # 每次更新之前清空数据
        old_quality_records = self.env['qm.insp.task.quality'].search([('insp_task_record_id', '=', self.id)])
        old_quality_records.unlink()
        old_quantity_records = self.env['qm.insp.task.quantify'].search([('insp_task_record_id', '=', self.id)])
        old_quantity_records.unlink()
        # 数据存储
        lines_qality = []
        lines_quantity = []
        # 该工序下定性检验项目数量&定量检验项目的对象集
        quality = self.work_procedure_id.work_procedure_quality_ids_one
        quantity = self.work_procedure_id.work_procedure_quantity_ids_one
        # 定性特性刷新过程
        if quality is not None:
            for i in range(len(quality)):
                # 检验项目ID
                project_id = quality[i].insp_project_def_id
                # 特性权重
                importance_degree = project_id.importance_degree
                # 依赖标准
                depend_standard = self.work_procedure_id.quality_standard
                # 检验方法
                insp_method_id = project_id.insp_method_id
                # 样本量
                sample_count = self.inspection_order_id.sample_count
                # 请求的json数据
                response_json_data = self.inspection_order_id.response_json_data
                json_data = eval(response_json_data)
                # Ac值
                ac = json_data["ac"]
                # Re值
                re = json_data["re"]
                # 结果记录方式
                result_record_way = project_id.result_record_way
                # 依据
                accept_depend = project_id.accept_depend
                # 结果记录
                product_id = self.product_id
                insp_lot_num = self.insp_lot_num
                work_procedure_id = self.work_procedure_id
                sample_plan_id = self.inspection_order_id.sample_plan_id
                project_type = 'quality'
                factory = self.factory
                lot_num = self.lot_num
                task_record_id = self.id
                valus = {
                    'insp_task_record_id': task_record_id,
                    'name': "结果记录",
                    'product_id': product_id,
                    'insp_lot_num': insp_lot_num,
                    'result_record_way': result_record_way,
                    'work_procedure_id': work_procedure_id,
                    'sample_plan_id': sample_plan_id,
                    'project_type': project_type,
                    'project_id': project_id,
                    'accept_depend': accept_depend,
                    'factory': factory,
                    'lot_num': lot_num,
                    'sample_count': sample_count,
                    'response_json_data': response_json_data,
                    'ac': ac,
                    're': re
                }
                record_quality_id = self.create_insp_task_record_quality(valus)

                # TODO：beigin 2016-9-29 11:09:15 by zhaoli build data for defect_records
                # 需要判断，如果已存在该缺陷记录，则不不要再次创建
                vals = {
                    'defect_record_leval': '检验特性',
                    'product_id': product_id.id,
                    'test_process': work_procedure_id.id,  # 检验工序
                    'test_lot': insp_lot_num,
                    'lot_num': lot_num,
                    'test_project': project_id.id,
                    'test_owner': self.inspection_order_id.inspector.id,
                    'insp_order': self.inspection_order_id.id,
                    'qm_notice_type':'customer_complaint'
                }
                defect_records = self.create_defect_records(vals)
                # end
                line_item = {
                    'project_id': project_id,
                    'importance_degree': importance_degree,
                    'depend_standard': depend_standard,
                    'insp_method_id': insp_method_id,
                    'sample_count': sample_count,
                    'ac': ac,
                    're': re,
                    'result_record_way': result_record_way,
                    'accept_depend': accept_depend,
                    'record_bill': record_quality_id,
                    # TODO:2016-9-29 11:13:29 added by zhaoli
                    'defect_record': defect_records
                }
                lines_qality += [line_item]
        # 定量特性刷新过程
        if quantity is not None:
            for j in range(len(quantity)):
                # 检验项目ID
                project_id = quantity[j].insp_project_def_id
                # 特性权重
                importance_degree = project_id.importance_degree
                # 依赖标准
                depend_standard = self.work_procedure_id.quality_standard
                # 检验方法
                insp_method_id = project_id.insp_method_id
                # 样本量
                sample_count = self.inspection_order_id.sample_count
                # 请求的json数据
                response_json_data = self.inspection_order_id.response_json_data
                # 目标值
                target_value = project_id.target_value
                # 规范上限
                u = project_id.upper_bound_values
                # 规范上限
                l = project_id.lower_bound_values
                # 计量单位
                measurement_units = project_id.measurement_units
                # 结果记录方式
                result_record_way = project_id.result_record_way
                # 结果记录
                product_id = self.product_id
                insp_lot_num = self.insp_lot_num
                work_procedure_id = self.work_procedure_id
                sample_plan_id = self.inspection_order_id.sample_plan_id
                project_type = 'quantity'
                accept_depend = project_id.accept_depend
                factory = self.factory
                lot_num = self.lot_num
                task_record_id = self.id
                valus = {
                    'insp_task_record_id': task_record_id,
                    'name': "结果记录",
                    'product_id': product_id,
                    'insp_lot_num': insp_lot_num,
                    'result_record_way': result_record_way,
                    'work_procedure_id': work_procedure_id,
                    'sample_plan_id': sample_plan_id,
                    'project_type': project_type,
                    'project_id': project_id,
                    'accept_depend': accept_depend,
                    'factory': factory,
                    'lot_num': lot_num,
                    'sample_count': sample_count,
                    'response_json_data': response_json_data,
                    'measurement_units': measurement_units,
                    'target_value': target_value,
                    'u': u,
                    'l': l
                }
                record_quantify_id = self.create_insp_task_record_quantity(valus)

                # TODO：beigin 2016-9-29 11:09:15 by zhaoli build data for defect_records
                vals = {
                    'defect_record_leval': '检验特性',
                    'product_id': product_id.id,
                    'test_process': work_procedure_id.id,  # 检验工序
                    'test_lot': insp_lot_num,
                    'lot_num': lot_num,
                    'test_project': project_id.id,
                    'test_owner': self.inspection_order_id.inspector.id,
                    'insp_order': self.inspection_order_id.id,
                    'qm_notice_type':'customer_complaint'
                }
                defect_records = self.create_defect_records(vals)

                line_item = {
                    'project_id': project_id,
                    'importance_degree': importance_degree,
                    'depend_standard': depend_standard,
                    'insp_method_id': insp_method_id,
                    'sample_count': sample_count,
                    'target_value': target_value,
                    'u': u,
                    'l': l,
                    'measurement_units': measurement_units,
                    'result_record_way': result_record_way,
                    'accept_depend': accept_depend,
                    'record_bill': record_quantify_id,
                    # TODO:2016-9-29 11:13:29 added by zhaoli
                    'defect_record': defect_records
                }
                lines_quantity += [line_item]

        self.update({'record_quality': lines_qality, 'record_quantify': lines_quantity})

    '''创建---定性特性---结果记录表单'''

    @api.multi
    def create_insp_task_record_quality(self, values):
        data = {
            'name': values['name'],
            'product_id': values['product_id'].id,
            'insp_lot_num': values['insp_lot_num'],
            'result_record_way': values['result_record_way'],
            'work_procedure_id': values['work_procedure_id'].id,
            'sample_plan_id': values['sample_plan_id'].id,
            'project_type': values['project_type'],
            'project_id': values['project_id'].id,
            'accept_depend': values['accept_depend'],
            'factory': values['factory'],
            'lot_num': values['lot_num'],
            'sample_count': values['sample_count'],
            'response_json_data': values['response_json_data'],
            'ac': values['ac'],
            're': values['re'],
        }
        record_id = self.env['qm.insp.task.record'].sudo().create(data)
        return record_id

    '''创建---定量特性---结果记录表单'''

    @api.multi
    def create_insp_task_record_quantity(self, values):
        data = {
            'name': values['name'],
            'product_id': values['product_id'].id,
            'insp_lot_num': values['insp_lot_num'],
            'result_record_way': values['result_record_way'],
            'work_procedure_id': values['work_procedure_id'].id,
            'sample_plan_id': values['sample_plan_id'].id,
            'project_type': values['project_type'],
            'project_id': values['project_id'].id,
            'accept_depend': values['accept_depend'],
            'factory': values['factory'],
            'lot_num': values['lot_num'],
            'sample_count': values['sample_count'],
            'response_json_data': values['response_json_data'],
            'measurement_units': values['measurement_units'].id,
            'target_value': values['target_value'],
            'u': values['u'],
            'l': values['l'],
        }
        record_id = self.env['qm.insp.task.record'].sudo().create(data)
        return record_id

    # TODO:创建--定性特性--缺陷记录 2016-9-29 11:17:15 by zhaoli
    @api.multi
    def create_defect_records(self, vals):
        name = self.env['ir.sequence'].next_by_code('qm.defect.records')
        values = {
            'name': name,
            'defect_record_leval': '检验特性',
            'product_id': vals['product_id'],
            'test_process': vals['test_process'],  # 检验工序
            'test_lot': vals['test_lot'],
            'lot_num': vals['lot_num'],
            'test_project': vals['test_project'],
            'test_owner': vals['test_owner'],
            'insp_order': vals['insp_order']
        }
        return self.env['qm.defect.records'].create(vals)

    '''
    字段监听
    '''

    @api.onchange('record_quality')
    def record_quality_listening(self):
        self.compute_finish_insp_num()

    @api.multi
    @api.onchange('record_quantify')
    def record_quantify_listening(self):
        self.compute_finish_insp_num()

    '''统计已完成检测项目数，达标特性数，不达标特性数'''

    @api.multi
    def compute_finish_insp_num(self):
        record_quality_ids = self.record_quality
        record_quantify_ids = self.record_quantify
        # 统计定性&定量项目的数量
        record_quality_len = len(record_quality_ids)
        record_quantify_len = len(record_quantify_ids)
        # 已完成项目数定义
        quality_finish_insp_count = 0
        quantify_finish_insp_count = 0
        # 达标特性数定义
        quality_qualified_count = 0
        quantify_qualified_count = 0
        # 不达标特性数定义
        # 定性接收状态统计
        quality_unqualified_count = 0
        quantify_unqualified_count = 0
        # 记录统计已完成的状态
        finish_insp_state_count = 0
        # 定性特性的统计过程
        if record_quality_len != 0:
            for x in range(record_quality_len):
                project_accept = record_quality_ids[x].project_accept
                if project_accept not in [False, "result_1"]:
                    quality_finish_insp_count += 1
                    if project_accept == 'result_2':
                        quality_qualified_count += 1
                    if project_accept == 'result_3':
                        quality_unqualified_count += 1
                else:
                    finish_insp_state_count += 1

        # 定量特性的统计过程
        if record_quantify_len != 0:
            for j in range(record_quantify_len):
                project_accept = record_quantify_ids[j].project_accept
                if project_accept not in [False, "result_1"]:
                    quantify_finish_insp_count += 1
                    if project_accept == 'result_2':
                        quantify_qualified_count += 1
                    if project_accept == 'result_3':
                        quantify_unqualified_count += 1
                else:
                    finish_insp_state_count += 1

        # 检验项目数
        project_count = record_quality_len + record_quantify_len
        # 已完成项目数
        finish_insp_count = quality_finish_insp_count + quantify_finish_insp_count
        # 已完成项目中的达标数
        qualified_count = quality_qualified_count + quantify_qualified_count
        # 已完成项目中的不达标数
        unqualified_count = quality_unqualified_count + quantify_unqualified_count
        # 统计工序的的检验状态
        if finish_insp_state_count == 0:
            self.insp_state = "state_2"
        else:
            self.insp_state = "state_1"
        # 界面赋值
        self.project_count = project_count
        self.finish_insp_count = finish_insp_count
        self.qualified_count = qualified_count
        self.unqualified_count = unqualified_count
