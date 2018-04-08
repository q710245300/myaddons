# -*-coding:utf-8-*-
{
    'name': 'QM',
    'description': 'QM',
    'author': 'peraglobal',
    'depends': ['base', 'product','auth_crypt','stock','hr_equipment'],#本模块对其他模块的依赖关系
    'application': True,
    'data': [#本模块要加载的数据文件(包括Odoo里面的视图、动作、工作流、模型具体对象)
        # 数据字典
        'view/qm_data_dictionary/view_attributes.xml',
        'view/qm_data_dictionary/view_attributes_type.xml',
        'view/qm_data_dictionary/view_attributes_values.xml',
        'view/qm_data_dictionary/view_defect.xml',
        'view/qm_data_dictionary/view_defect_type.xml',
        'view/qm_data_dictionary/view_defect_level.xml',
        'view/qm_data_dictionary/view_station_product_line.xml',
        'view/qm_data_dictionary/view_station_check_point.xml',
        'view/qm_data_dictionary/view_usage.xml',
        'view/qm_data_dictionary/view_technology.xml',
        'view/qm_data_dictionary/lot_num_rule/view_qm_partner_num.xml',
        'view/qm_data_dictionary/lot_num_rule/view_qm_customer_num.xml',
        'view/qm_data_dictionary/lot_num_rule/view_qm_pro_line_code.xml',
        'view/qm_data_dictionary/lot_num_rule/view_qm_equipment_num.xml',
        'view/qm_data_dictionary/lot_num_rule/view_qm_date_code.xml',
        'view/qm_data_dictionary/trans_level_rule/view_trans_level_rule.xml',
        'view/qm_data_dictionary/trans_level_rule/view_trans_rule_type.xml',
        # 质量数据
        'view/qm_data/view_ext_product_template.xml',
        'view/qm_data/view_ext_res_partner.xml',
        'view/qm_data/view_lot_num_rule.xml',
        'view/qm_data/view_qm_trans_level.xml',
        'view/qm_data/view_product_list.xml',

        # 检验计划
        'view/qm_insp_plan/squence_work_procedure.xml',
        'view/qm_insp_plan/view_gb_standard.xml',
        'view/qm_insp_plan/view_qm_insp_method_def.xml',
        'view/qm_insp_plan/view_qm_insp_project_def.xml',
        'view/qm_insp_plan/view_qm_plan_for_instruction.xml',
        'view/qm_insp_plan/view_sample_plan.xml',
        'view/qm_insp_plan/view_work_procedure.xml',
        
        # 质检过程
        'view/qm_insp_process/sequence_trans_level_record.xml',
        'view/qm_insp_process/squence_qm_inspection_order.xml',
        
        
        'view/qm_insp_process/view_qm_insp_task.xml',
        'view/qm_insp_process/view_qm_insp_task_quality.xml',
        'view/qm_insp_process/view_qm_insp_task_record.xml',
        'view/qm_insp_process/view_qm_spc_data.xml',
        'view/qm_insp_process/view_task_item.xml',
        'view/qm_insp_process/view_trans_level_record.xml',
        'view/qm_insp_process/workflow_qm_spc_data.xml',
        'view/qm_insp_process/workflow_trans_record.xml',
        
        #质量通知
        'view/qm_notice/sequence_for_qm_notice.xml',
        'view/qm_notice/view_qm_notice.xml',
        'view/qm_notice/workflow_for_qm_actions.xml',
        'view/qm_notice/workflow_for_qm_notice.xml',
        'view/qm_insp_process/view_qm_defect_records.xml',
        'view/qm_insp_process/view_qm_insp_order.xml',
        #SPC视图
        'view/qm_viewer/view_report_viewer.xml',

        'view/qm_insp_process/view_qm_usage_decision.xml',
        # 菜单
        'view/menu.xml',

        # 基础数据DATA
        'data/sample/data_gb_standard.xml',
        'data/sample/data_sample_check_type.xml',
        'data/sample/data_check_level.xml',
        'data/sample/data_accept_quality.xml',
        'data/sample/data_check_degree_item.xml',
        'data/sample/data_check_degree.xml',
        'data/condition/data_check_degree_trans_rule.xml',
        'data/condition/data_trans_level_type.xml',
        'data/condition/data_trans_type_condition_2828_1.xml',
        'data/condition/data_trans_type_condition_2828_3.xml',
        'data/condition/data_trans_type_condition_6378_1.xml',

        'data/spc_data/data_spc_control_chart_type.xml',
    ]
}