# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError

class qm_usage_decision(models.Model):
    _name = "qm.usage.decision"

    name = fields.Char("使用决策")
    product_id = fields.Many2one("product.template","产品",required=True)
    test_lot = fields.Char("检验批")
    lot_num = fields.Char("批次")
    batch = fields.Integer("批量")
    simple_size = fields.Integer("样本量")
    test_end_date = fields.Datetime("检验完成时间",required=True)
    fectory = fields.Char("工厂")
    origin = fields.Char("源单据")
    partner= fields.Many2one('res.users','合作伙伴')
    product_owner = fields.Many2one('res.users',"产品负责人")
    test_owner = fields.Many2one('res.users',"检验责任人")
    qm_notice_type = fields.Selection([('customer_complaint','客户投诉'),('complaint_partner','投诉供应商'),('inner_problem_report','内部问题报告'),('specific_qm_notice','用户特定的质量通知')],"质量通知类型",required=True)
    usage_decision = fields.Selection([('receive','接收'),('concession','让步接收'),('return','返工'),('reuse','回用'),('refuse','退货'),('scrap','整批报废')],string="使用决策")
    later_option = fields.Char("后续操作")
    usage_decision_persion = fields.Many2one('res.users',"使用决策人")
    usage_decision_date = fields.Datetime("使用决策日期")
    insp_order = fields.Many2one('qm.inspection.order','检验单')

    defect_struct_ids = fields.One2many('qm.defect.struct','usage_decision_id',"缺陷结构")

    result_order_ids = fields.One2many('qm.feature.overview','usage_decision_id','特性概览')
    stock_move_info_ids = fields.One2many("qm.stock.move.info","usage_decision_id","库存转移信息")


    _defaults = {'usage_decision_persion':lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context=context).id,
               'usage_decision_date':fields.datetime.today(),
               'name': lambda self, cr, uid, context={}: self.pool.get('ir.sequence').get(cr, uid, 'qm.usage.decision')}

    #新建的使用决策
    @api.model
    def default_get(self, fields):
        rec = super(qm_usage_decision, self).default_get(fields)
        context = dict(self._context or {})
        insp_order_id = context['insp_order']
        insp_order = self.env['qm.inspection.order'].browse(insp_order_id)
        rec['insp_order'] = insp_order_id
        rec['product_id'] = insp_order.product_id.id
        rec['fectory'] = insp_order.factory.id
        rec['test_lot'] = insp_order.name #检验批是质检单的单号
        rec['origin'] = insp_order.origin
        rec['lot_num'] = insp_order.lot_num #批次号是质检单的检验批编号
        rec['batch'] = insp_order.lot_count
        rec['simple_size'] = insp_order.sample_count
        rec['test_end_date'] = insp_order.insp_finish_time
        rec['test_owner'] = insp_order.inspector.id

        #获取当前检验单下的缺陷记录
        defect_record_ids = self.env['qm.defect.record'].search([('insp_order','=',insp_order_id)])
        defect_ids = []
        for defect_record_id in defect_record_ids:
            record = self.env['qm.defect.record'].browse(defect_record_id.id)
            defect = [0,False,{
                'test_lot': record.test_lot,
                'option': record.test_process.id,
                'test_feature': record.test_project.id,
                'defect_type': record.defect_type.id,
                'defect_count': record.defect_count,
                'defect_position': record.defect_position,
                'defect_leval': record.defect_leval.id,
                'qm_insp_order_id': record.insp_order.id,
                'notice_state': record.unqualified_review_application and "send" or "un_send",
                'notice_send': record.unqualified_review_application and True or False,
                'defect_order_id': record.id
            }]
            defect_ids.append(defect)
        rec['defect_struct_ids'] = defect_ids

        #获取当前检验单下的结果记录
        result_record_ids = self.env['qm.insp.task.record'].search([('qm_inspection_order_id','=',insp_order_id)])
        result_ids = []
        for result_record in result_record_ids:
            record = self.env['qm.insp.task.record'].browse(result_record.id)
            result = [0,False,{
                'insp_lot_num':record.insp_lot_num,
                'product_id':record.product_id.id,
                'work_procedure_id':record.work_procedure_id.id,
                'project_id':record.project_id.id,
                'd':record.d,
                'out_limit_count':record.out_limit_count,
                'insp_person':record.insp_person.id,
                'project_accept':record.project_accept,
                'project_type':record.project_type
            }]
            result_ids.append(result)
        rec['result_order_ids'] = result_ids
        return rec

    @api.model
    def create(self, vals):
        def create_insp_order(vals):
            insp_order_model = self.env['qm.inspection.order']
            insp_order = insp_order_model.browse(vals['insp_order'])
            insp_order_vals = {
                'name':insp_order.name,
                'lot_num':insp_order.lot_num,
                'insp_plan_type':insp_order.insp_plan_type,
                'plan_id':insp_order.plan_id.id,
                'lot_count':insp_order.lot_count,
                'again_commit_lot':True
            }
            insp_order_model.create(insp_order_vals)
        moves = vals['stock_move_info_ids']
        move_vals = []
        move_qty = 0
        if moves:
            for move in moves:
                #如果是沿用批次号，重新检验，那么就不需要在新建库存移动了
                if move[2]['follow_lot_num']:
                    create_insp_order(vals)
                else:
                    if move[2]['move_count'] ==0:
                        raise ValidationError(u'转移的数量不能为零')
                    if move_qty > vals['batch']:
                        raise ValidationError(u'转移的数量不能超过该批量')
                    move_qty = move_qty + move[2]['move_count']
                    product = self.env['product.template'].browse(vals['product_id'])
                    move_val = {
                        'origin': vals['name'],
                        'date_expected':vals['test_end_date'],
                        'product_id': product.id,
                        'product_uom': product.uom_id.id,
                        'picking_type_id': False,
                        'partner_id': False,
                        'product_uom_qty':  move[2]['move_count'],
                        'company_id': product.company_id.id,
                        'priority': '1',
                        'procure_method': u'make_to_stock',
                        'location_dest_id': move[2]['stock'],
                        'date': vals['test_end_date'],
                        'picking_partner_id': False,
                        'group_id': False,
                        'location_id': 12,
                        'picking_id': False,
                        'name': product.name
                    }
                    move_vals.append(move_val)
                    self.env['stock.move'].create(move_val)
        return super(qm_usage_decision,self).create(vals)

    @api.multi
    def send_notice(self):
        context = dict(self._context or {})
        vals = {}
        if context.has_key('origin') and context['origin']:
            vals['origin'] = context['origin']
        if context.has_key('product_id') and context['product_id']:
            vals['product_id'] = context['product_id']
        if context.has_key('test_lot')and context['test_lot']:
            vals['test_lot'] = context['test_lot']
        if context.has_key('lot_num') and context['lot_num']:
            vals['lot_num'] = context['lot_num']
        if context.has_key('partner') and context['partner']:
            vals['partner'] = context['partner']
        if context.has_key('qm_notice_type') and context['qm_notice_type']:
            vals['notice_type'] = context['qm_notice_type']
        else:
            raise ValueError('请选择通知类型')

        defect_order_ids = []
        defects = context['defect_struct_ids']
        for struct in defects:
            defect_struct_id = struct[1]
            defect_struct = self.env['qm.defect.struct'].browse(defect_struct_id)
            defect_order = defect_struct.defect_order_id
            if defect_order.notice_usage_state:
                defece_analysis = [0,False,{
                    'test_lot':defect_order.test_lot,
                    'option':defect_order.test_process.id,
                    'test_feature':defect_order.test_project.id,
                    'defect_type':defect_order.defect_type.id,
                    'defect_count':defect_order.defect_count,
                    'defect_position':defect_order.defect_position,
                    'defect_leval':defect_order.defect_leval.id,
                    'qm_insp_order_id':defect_order.insp_order.id
                }]
                defect_order_ids.append(defece_analysis)
        vals['defect_analysis_ids'] = defect_order_ids
        self.env['qm.notice'].create(vals)

#缺陷结构
class qm_defect_struct(models.Model):
    _name = "qm.defect.struct"

    usage_decision_id = fields.Many2one("qm.usage.decision")
    test_lot = fields.Char("检验批")
    option = fields.Many2one("qm.work_procedure","操作工序")
    test_feature = fields.Many2one('qm.insp_project_def',"检验特性")
    defect_type = fields.Many2one('qm.defects',"缺陷类型")
    defect_count = fields.Integer("缺陷数量")
    defect_position = fields.Selection([('posion_A','上部分'),('posion_B','中部'),('posion_C','下部')],"缺陷位置")
    defect_leval = fields.Many2one('defects.level',"缺陷等级")
    notice_state = fields.Selection([("un_send","未发送"),("send","已发送")],"质量通知")
    notice_send = fields.Boolean("是否发送")
    defect_order_id = fields.Many2one('qm.defect.record','缺陷记录')
    qm_insp_order_id = fields.Many2one("qm.inspection.order","质检订单")
    #defect_order_ids = fields.Integer('缺陷记录列表')



    @api.multi
    @api.onchange('notice_send')
    def onchange_notcie_send(self):
        if self.notice_send:
            #self.defect_order_ids = self.defect_order_id
            self.notice_state = 'send'
            self.pool.get('qm.defect.record').write(self._cr,self._uid,self.defect_order_id.id,{'notice_usage_state':True,'unqualified_review_application':True},self._context)
            #self.env['qm.defect.record'].write(self.defect_order_id,{'notice_usage_state':False})
        else:
            #self.defect_order_ids = 0
            self.notice_state = 'un_send'
            #self.env['qm.defect.record'].write(self.defect_order_id,{'notice_usage_state':False})
            self.pool.get('qm.defect.record').write(self._cr,self._uid,self.defect_order_id.id,{'notice_usage_state':False,'unqualified_review_application':False},self._context)


#特性概览
class qm_feature_overview(models.Model):
    _name = "qm.feature.overview"

    usage_decision_id = fields.Many2one("qm.usage.decision")
    insp_lot_num = fields.Char(string='检验批')
    work_procedure_id = fields.Many2one("qm.work_procedure", string="工序")
    product_id = fields.Many2one('product.template', string="产品")
    project_type = fields.Selection([('quality', '定性特性'), ('quantity', '定量特性')], string="特性类型")
    project_id = fields.Many2one("qm.insp_project_def", string="检验项目")
    # 定性特性列表独占数据字段
    d = fields.Integer(string="d(累积)")
    # 定量特性列表独占数据字段
    out_limit_count = fields.Integer(string="d(累积)")
    project_accept = fields.Selection(
        [('result_1', '待验'), ('result_2', '接收'), ('result_3', '不接收'), ('result_4', '不可判定')], string="特性接收判定")


#库存转移信息
class qm_stock_move_info(models.Model):
    _name = "qm.stock.move.info"

    usage_decision_id = fields.Many2one("qm.usage.decision")
    move_to = fields.Selection([('next','库位链的下一目的库位'),('scrap','报废库位'),('freeze','冻结库存'),('qm_test','质检库存'),('origin','源库位'),('assign_location','指定库位')],"转移到")
    move_count = fields.Integer("转移数量")
    stock = fields.Many2one('stock.location',"库位")
    action = fields.Char("动作")
    follow_lot_num = fields.Boolean("沿用批次号")
    move_desc = fields.Char("库存转移说明")


    @api.multi
    @api.onchange('move_count')
    def onchange_move_count(self):
        if self.move_count <= 0:
            raise ValidationError(u'转移的数量不能为零')