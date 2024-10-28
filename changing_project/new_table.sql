DROP TABLE IF EXISTS `wxapp_color`;
CREATE TABLE `wxapp_color`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `title` varchar(30) NULL DEFAULT '' COMMENT '标题',
  `values_json` mediumtext NULL COMMENT '配套设置',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '小程序配套颜色';


DROP TABLE IF EXISTS `wxapp_region`;
CREATE TABLE `wxapp_region`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `pid` int(0) NULL DEFAULT NULL COMMENT 'pid',
  `shortname` varchar(50) NULL DEFAULT NULL COMMENT '简称',
  `name` varchar(50) NULL DEFAULT NULL COMMENT '名称',
  `level` varchar(50) NULL DEFAULT NULL COMMENT '层级 1 2 3 省市区县',
  `first` varchar(50) NULL DEFAULT NULL COMMENT '首字母',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '全国地区表';



DROP TABLE IF EXISTS `wxapp_setting`;
CREATE TABLE `wxapp_setting`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `title` varchar(30) NULL DEFAULT '' COMMENT '设置项标示',
  `describes` varchar(255) NULL DEFAULT '' COMMENT '设置项描述',
  `values_json` mediumtext NULL COMMENT '设置内容(json格式)',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '设置表';


DROP TABLE IF EXISTS `wxapp_guide`;
CREATE TABLE `wxapp_guide`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `title` varchar(50) NULL DEFAULT '' COMMENT '标题',
  `content` varchar(1000) NULL DEFAULT '' COMMENT '内容',
  `weigh` int(10) NULL DEFAULT 0 COMMENT '权重',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '用户指南表';



DROP TABLE IF EXISTS `wxapp_picture`;
CREATE TABLE `wxapp_picture` (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `url` varchar(255) NULL DEFAULT NULL COMMENT '路径',
  `types` int(0)  NULL DEFAULT 0 COMMENT '类型:0图片,1banner,2二维码',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB COMMENT='图片';


DROP TABLE IF EXISTS `wxapp_authority`;
CREATE TABLE `wxapp_authority`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `name` varchar(50) NULL DEFAULT NULL COMMENT '名称',
  `authority` mediumtext NULL DEFAULT NULL COMMENT '权限',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '权限表';



DROP TABLE IF EXISTS `wxapp_note`;
CREATE TABLE `wxapp_note`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_name` varchar(255) NULL DEFAULT NULL COMMENT 'note名称',
  `province_id` int(11) NULL DEFAULT 0 COMMENT '所在省份id',
  `city_id` int(11) NULL DEFAULT 0 COMMENT '所在城市id',
  `region_id` int(11) NULL DEFAULT 0 COMMENT '所在辖区id',
  `address` varchar(100) NULL DEFAULT NULL COMMENT '详细地址',
  `longitude` varchar(50) NULL DEFAULT NULL COMMENT '经度',
  `latitude` varchar(50) NULL DEFAULT NULL COMMENT '纬度',
  `summary` varchar(1000) NULL DEFAULT NULL COMMENT 'NOTE简介',
  `status` int(0) NULL DEFAULT 0 COMMENT '状态(0停止 1正常)',
  `is_ind_dealer` int(0) NULL DEFAULT 0 COMMENT '是否开启单独分成(0关闭 1开启)',
  `bill_type` int(0) NULL DEFAULT 0 COMMENT '计费类型(0按时 1分档)',
  `predict_price` float(10, 2) NULL DEFAULT 0.00 COMMENT '预扣金额',
  `first_proportion` float(10, 2) NULL DEFAULT 0.00 COMMENT '一级分成比例(代理商)',
  `second_proportion` float(10, 2) NULL DEFAULT 0.00 COMMENT '二级分成比例(社区)',
  `free_time` int(0) NULL DEFAULT 0 COMMENT '免费停放时长（分钟）',
  `money` float(10, 2) NULL DEFAULT 0.00 COMMENT '门禁费用单次',
  `is_refund` int(0) NULL DEFAULT 0 COMMENT '是否开启充电时长不足退款(1是 0否)',
  `is_temporary_site` int(0) NULL DEFAULT 0 COMMENT '是否是临停场地(1是 0否)',
  `step` int(0) NULL DEFAULT 0 COMMENT '步长/小时(60分钟)',
  `refund_price` float(10, 2) NULL DEFAULT 0 COMMENT '步长/退款单价',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '社区节点';


DROP TABLE IF EXISTS `wxapp_note_elecdata`;
CREATE TABLE `wxapp_note_elecdata`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT '社区id',
  `ammeter_name` varchar(255) NULL DEFAULT '' COMMENT '电表名称',
  `end_number` float(10, 2) NULL DEFAULT 0 COMMENT '最后读数',
  `number` float(10, 2) NULL DEFAULT 0 COMMENT '上报读数',
  `image` varchar(1000) NULL DEFAULT NULL COMMENT '图片',
  `date_time` date(0) NULL DEFAULT NULL COMMENT '时间',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '社区电表数据';



DROP TABLE IF EXISTS `wxapp_bill`;
CREATE TABLE `wxapp_bill`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT '社区id',
  `total_price` float(10, 2)  NULL DEFAULT 0.00 COMMENT '总金额',
  `price` float(10, 2) NULL DEFAULT 0.00 COMMENT '单价',
  `title` varchar(50) NULL DEFAULT NULL COMMENT '标题描述(0.5元/2小时)',
  `billtype` int(0) NULL DEFAULT 0 COMMENT '计费方式(0默认,1按小时计费,2按时充满自停，3分档计费,4分档充满自停)',
  `is_ceil` int(0) NULL DEFAULT 0 COMMENT '充满自停计费模式(0默认按分钟,1按小时(向上取整))',
  `step` int(0) NOT NULL DEFAULT 1 COMMENT '步长/小时',
  `duration` int(0) NOT NULL DEFAULT 1 COMMENT '时长',
  `sort` int(0) NULL DEFAULT 0 COMMENT '排序',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '按时计费表';


DROP TABLE IF EXISTS `wxapp_bill_tranche`;
CREATE TABLE `wxapp_bill_tranche`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT '社区id',
  `price` float(10, 2) NULL DEFAULT 0.00 COMMENT '单价',
  `start_section` int(0) NULL DEFAULT 0 COMMENT '开始区间（分档）',
  `end_section` int(0) NULL DEFAULT 0 COMMENT '结束区间（分档）',
  `sort` int(0) NULL DEFAULT 0 COMMENT '排序',
  `remarks` varchar(255) NULL DEFAULT NULL COMMENT '备注',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '分档计费表';




DROP TABLE IF EXISTS `wxapp_pod_pile`;
CREATE TABLE `wxapp_pod_pile`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT '社区id',
  `gateway_id` varchar(255) NULL DEFAULT NULL COMMENT '网关id',
  `type` int(0) NULL DEFAULT NULL COMMENT '充电桩类型  1：新网 2：柏莱(二孔) 3：柏莱(十二孔) 4:柏莱(子母机) 5网关 6:柏莱（十口）',
  `title` varchar(255) NULL DEFAULT NULL COMMENT '标题',
  `snum` varchar(50) NULL DEFAULT NULL COMMENT '设备SN编码',
  `serialnum` varchar(50) NULL DEFAULT NULL COMMENT '充电桩串号',
  `pileport` int(0) NULL DEFAULT 12 COMMENT '充电桩端口数量',
  `pileversion` varchar(50) NULL DEFAULT NULL COMMENT '充电桩版本',
  `iccid` varchar(50) NULL DEFAULT NULL COMMENT 'ICCID号码',
  `xhqd` varchar(50) NULL DEFAULT NULL COMMENT '信号强度',
  `isonline` int(0) NULL DEFAULT 0 COMMENT '是否在线',
  `lastip` varchar(50) NULL DEFAULT NULL COMMENT '最后上线IP',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '充电桩信息表' ;



DROP TABLE IF EXISTS `wxapp_pod_pileport`;
CREATE TABLE `wxapp_pod_pileport`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT '社区id',
  `pile_id` int(0) NULL DEFAULT NULL COMMENT '充电桩id',
  `serialnum` varchar(50) NULL DEFAULT NULL COMMENT '充电桩串号',
  `portnum` int(0) NULL DEFAULT 0 COMMENT '端口编号',
  `portvoltage` int(0) NOT NULL DEFAULT 0 COMMENT '电压V',
  `portelectric` int(0) NOT NULL DEFAULT 0 COMMENT '电流mA',
  `portpulse` varchar(20) NOT NULL DEFAULT '0' COMMENT '脉冲值',
  `portstatus` int(0) NOT NULL DEFAULT 0 COMMENT '端口状态 1:占用 0未占用',
  `trouble_status` int(0) NOT NULL DEFAULT 0 COMMENT '是否故障 0否 1是',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '充电桩端口信息表' ;


DROP TABLE IF EXISTS `wxapp_default_param`;
CREATE TABLE `wxapp_default_param`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `pile_id` int(0) NULL DEFAULT NULL COMMENT '充电桩id',
  `null_charge_power` float(10, 2) NULL DEFAULT 0.00 COMMENT '空载功率阈值 w',
  `null_charge_delay` int(0) NULL DEFAULT NULL COMMENT '空载延时（秒）',
  `full_charge_power` float(10, 2) NULL DEFAULT 0.00 COMMENT '充满功率阈值 w',
  `full_charge_delay` int(0) NULL DEFAULT 0 COMMENT '充满延时（秒）',
  `high_temperature` int(0) NOT NULL DEFAULT 0 COMMENT '高温阈值 度',
  `max_recharge_time` int(0) NOT NULL DEFAULT 0 COMMENT '最大充电时间 分钟',
  `trickle_threshold` int(0) NOT NULL DEFAULT 0 COMMENT '涓流阈值 ma',
  `threshold_p` float(10, 2) NULL DEFAULT 0.00 COMMENT '功率限值 w',
  `threshold_i` float(10, 2) NULL DEFAULT 0.00 COMMENT '过流限值 mA',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '充电桩端口信息表' ;




DROP TABLE IF EXISTS `wxapp_order`;
CREATE TABLE `wxapp_order`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `order_id` varchar(50) NULL DEFAULT '' COMMENT '订单id',
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT '社区id',
  `user_id` int(0) NULL DEFAULT NULL COMMENT 'usre_id',
  `pile_id` int(0) NULL DEFAULT NULL COMMENT 'pile_id',
  `pileport_id` int(0) NULL DEFAULT NULL COMMENT '充电桩端口id',
  `snum` varchar(50) NULL DEFAULT '' COMMENT '设备SN编码',
  `portnum` varchar(50) NULL DEFAULT '' COMMENT '端口编号',
  `start_time` datetime(0) NULL DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime(0) NULL DEFAULT NULL COMMENT '结束时间',
  `recharge_time` double(10, 2) NULL DEFAULT 0.00 COMMENT '充电时长',
  `total_price` double(10, 2)  NULL DEFAULT 0.00 COMMENT '原支付金额',
  `pay_price` double(10, 2)  NULL DEFAULT 0.00 COMMENT '实际付款金额',
  `pay_type` tinyint(3) NULL DEFAULT 20 COMMENT '支付方式(10余额支付 20微信支付 30套餐扣款 40刷卡充电 50白名单用户 60虚拟金额支付)',
  `billtype` tinyint(3) NULL DEFAULT 0 COMMENT '计费方式(0默认,1按小时计费,2充满自停 3分档计费,4分档充满自停)',
  `order_status` tinyint(3)  NULL DEFAULT 10 COMMENT '订单状态(0未开始充电 1启动中 10充电中 11结束中 20充电结束 30充电失败)',
  `pay_status` tinyint(3)  NULL DEFAULT 10 COMMENT '支付状态(10待支付 20已支付 30已退款 40退款异常)',
  `refund_type` tinyint(3)  NULL DEFAULT 10 COMMENT '退款类型(0自动 1手动)',
  `residue_money` double(10, 2)  NULL DEFAULT 0.00 COMMENT '退款金额',
  `refund_time` datetime(0) NULL DEFAULT NULL COMMENT '退款时间',
  `is_charge_buy` tinyint(3)  NULL DEFAULT 0 COMMENT '是否购买无忧充电(0否 1是)',
  `pay_time` datetime(0) NULL DEFAULT NULL COMMENT '付款时间',
  `transaction_id` varchar(30) NULL DEFAULT '' COMMENT '微信支付交易号',
  `refund_id` varchar(30) NULL DEFAULT '' COMMENT '微信退款单号',
  `user_received_account` varchar(50) NULL DEFAULT '' COMMENT '退款入账账户',
  `is_invalid` tinyint(3) NULL DEFAULT 0 COMMENT '订单是否失效(0未失效 1已失效)',
  `is_settled` tinyint(3) NULL DEFAULT 0 COMMENT '是否已结算佣金(0未结算 1已结算)',
  `first_proportion_money` float(10, 2) NULL DEFAULT 0.00 COMMENT '一级分成金额',
  `second_proportion_money` float(10, 2) NULL DEFAULT 0.00 COMMENT '二级分成金额',
  `endcode` int(3) NULL DEFAULT 0 COMMENT '结束代码1~7',
  `powerwaste` int(3) NULL DEFAULT 0 COMMENT '当次功耗',
  `porttag` int(5) NULL DEFAULT 0 COMMENT '端口标记',
  `endelectric` int(5) NULL DEFAULT 0 COMMENT '结束时电流值',
  `portpulse` varchar(20) NULL DEFAULT '' COMMENT '脉冲值',
  `onlytag` varchar(20) NULL DEFAULT '' COMMENT '唯一标识/网关id/mac',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  `cmd` tinyint(3)  NULL DEFAULT 0 COMMENT '回调判断是否调用充电桩端口控制指令 1:是 0否',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '订单记录表';



DROP TABLE IF EXISTS `wxapp_rescue_note`;
CREATE TABLE `wxapp_rescue_note`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_name` varchar(255) NULL DEFAULT '' COMMENT '救援note名称',
  `mobile` varchar(20) NULL DEFAULT '' COMMENT '联系方式',
  `province_id` int(11) NULL DEFAULT 0 COMMENT '所在省份id',
  `city_id` int(11) NULL DEFAULT 0 COMMENT '所在城市id',
  `region_id` int(11) NULL DEFAULT 0 COMMENT '所在辖区id',
  `address` varchar(100) NULL DEFAULT '' COMMENT '详细地址',
  `longitude` varchar(50) NULL DEFAULT '' COMMENT '经度',
  `latitude` varchar(50) NULL DEFAULT '' COMMENT '纬度',
  `is_maintain` tinyint(3) NULL DEFAULT 0 COMMENT '是否可维修(0否 1是)',
  `is_recharge` tinyint(3) NULL DEFAULT 0 COMMENT '是否可充电(0否 1是)',
  `status` tinyint(3) NULL DEFAULT 0 COMMENT '状态(0停止 1正常)',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '救援节点记录表';



DROP TABLE IF EXISTS `wxapp_recharge_plan`;
CREATE TABLE `wxapp_recharge_plan`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `plan_name` varchar(255)  NOT NULL DEFAULT '' COMMENT '套餐名称',
  `money` double(10, 2) NOT NULL DEFAULT 0.00 COMMENT '充值金额',
  `gift_money` double(10, 2) NOT NULL DEFAULT 0.00 COMMENT '赠送金额',
  `sort` int(11) NOT NULL DEFAULT 0 COMMENT '排序 (数字越小越靠前)',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '余额充值套餐表';



DROP TABLE IF EXISTS `wxapp_recharge_order`;
CREATE TABLE `wxapp_recharge_order`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `order_id` varchar(50) NULL DEFAULT NULL COMMENT '订单id',
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `user_id` int(0) NULL DEFAULT NULL COMMENT '用户id',
  `plan_id` int(0) NULL DEFAULT NULL COMMENT '充值套餐id',
  `recharge_type` tinyint(3) NOT NULL DEFAULT 10 COMMENT '充值方式(10自定义金额 20套餐充值)',
  `pay_price` double(10, 2) NOT NULL DEFAULT 0.00 COMMENT '用户支付金额',
  `gift_money` double(10, 2) NOT NULL DEFAULT 0.00 COMMENT '赠送金额',
  `actual_money` double(10, 2) NOT NULL DEFAULT 0.00 COMMENT '实际到账金额',
  `refund_money` double(10, 2) NOT NULL DEFAULT 0.00 COMMENT '退款金额',
  `pay_status` tinyint(3) NOT NULL DEFAULT 10 COMMENT '支付状态(10待支付 20已支付)',
  `is_refund` tinyint(3) NOT NULL DEFAULT 0 COMMENT '退款状态(0未退款 1已退款)',
  `pay_type` tinyint(3) NOT NULL DEFAULT 10 COMMENT '支付状态(10微信 20虚拟)',
  `is_represent` tinyint(3) NOT NULL DEFAULT 0 COMMENT '是否代他充值(0否 1是)',
  `rechargeuser_id` varchar(50) NOT NULL DEFAULT '0' COMMENT '被充值用户id',
  `transaction_id` varchar(30)  NOT NULL DEFAULT '' COMMENT '微信支付交易号',
  `refund_id` varchar(30)  NOT NULL DEFAULT '' COMMENT '微信退款单号',
  `pay_time` datetime(0) NULL DEFAULT NULL COMMENT '付款时间',
  `refund_time` datetime(0) NULL DEFAULT NULL COMMENT '退款时间',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '用户充值订单表';



DROP TABLE IF EXISTS `wxapp_recharge_package`;
CREATE TABLE `wxapp_recharge_package`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT 'note_id',
  `type` tinyint(3) NULL DEFAULT 0 COMMENT '套餐类型 (1:停车包 2:停车加充电包)',
  `plan_name` varchar(255)  NULL DEFAULT '' COMMENT '套餐名称',
  `days` int(11) NOT NULL DEFAULT 0 COMMENT '天数',
  `money` double(10, 2) NULL DEFAULT 0.00 COMMENT '金额',
  `recharge_time`int(11) NULL DEFAULT 0 COMMENT '充电时间',
  `gift_recharge_time` int(11) NOT NULL DEFAULT 0 COMMENT '赠送小时',
  `sort` int(11) NULL DEFAULT 0 COMMENT '排序 (数字越小越靠前)',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '充电套餐包表';




DROP TABLE IF EXISTS `wxapp_recharge_package_order`;
CREATE TABLE `wxapp_recharge_package_order`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `order_id` varchar(50) NULL DEFAULT NULL COMMENT '订单id',
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT 'note_id',
  `user_id` int(0) NULL DEFAULT NULL COMMENT 'user_id',
  `rechargeuser_id` int(0) NULL DEFAULT NULL COMMENT '代充值用户(第三方)',
  `package_id` int(0) NULL DEFAULT NULL COMMENT '套餐包id',
  `pay_type` tinyint(3)  NULL DEFAULT 20 COMMENT '支付方式(10余额支付 20微信支付 30混合支付 40管理员代买)',
  `pay_price` double(10, 2) NULL DEFAULT 0.00 COMMENT '用户支付金额',
  `pay_status` tinyint(3) NULL DEFAULT 10 COMMENT '支付状态(10待支付 20已支付)',
  `order_status` tinyint(3) NULL DEFAULT 10 COMMENT '订单状态(10未完成 20已完成 30退款中 40已退款 50退款被拒绝 60退款异常)',
  `pay_time` datetime(0) NULL DEFAULT NULL COMMENT '付款时间',
  `refund_time` datetime(0) NULL DEFAULT NULL COMMENT '退款时间',
  `transaction_id` varchar(30)  NULL DEFAULT '' COMMENT '微信支付交易号',
  `type` tinyint(3)  NULL DEFAULT 0 COMMENT '套餐类型 (1:停车包 2:停车加充电包)',
  `plan_name` varchar(255)  NULL DEFAULT '' COMMENT '套餐名称',
  `recharge_time` int(11)  NULL DEFAULT 0 COMMENT '充电时间',
  `residue_time` int(11)  NULL DEFAULT 0 COMMENT '剩余充电时间',
  `is_effect` int(11)  NULL DEFAULT 0 COMMENT '是否立即生效(0否(次月) 1是)',
  `is_auto_renew` int(11)  NULL DEFAULT 0 COMMENT '是否自动续费(0否 1是)',
  `is_use` tinyint(3)  NULL DEFAULT 0 COMMENT '是否有效(0否 1是)',
  `is_renew` tinyint(3)  NULL DEFAULT 0 COMMENT '是否续费(0否 1是)',
  `is_charge_buy` tinyint(3)  NULL DEFAULT 0 COMMENT '是否购买无忧充电(0否 1是)',
  `is_invalid` tinyint(3)  NULL DEFAULT 0 COMMENT '订单是否失效(0未失效 1已失效)',
  `is_settled` tinyint(3)  NULL DEFAULT 0 COMMENT '是否已结算佣金(0未结算 1已结算)',
  `first_proportion_money` float(10, 2) NULL DEFAULT 0.00 COMMENT '一级分成金额',
  `second_proportion_money` float(10, 2) NULL DEFAULT 0.00 COMMENT '二级分成金额',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `start_time` datetime(0) NULL DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime(0) NULL DEFAULT NULL COMMENT '到期时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '用户充电套餐充值订单表';


DROP TABLE IF EXISTS `wxapp_recharge_package_order_renew`;
CREATE TABLE `wxapp_recharge_package_order_renew`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `order_id` varchar(50) NULL DEFAULT NULL COMMENT '订单id',
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT 'note_id',
  `user_id` int(0) NULL DEFAULT NULL COMMENT 'user_id',
  `packageorder_id` int(0) NULL DEFAULT NULL COMMENT '订单id',
  `recharge_time` int(11)  NULL DEFAULT 0 COMMENT '充电时间',
  `start_time` datetime(0) NULL DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime(0) NULL DEFAULT NULL COMMENT '到期时间',
  `pay_type` tinyint(3)  NULL DEFAULT 20 COMMENT '支付方式(10余额支付 20微信支付 30混合支付 40管理员代买)',
  `pay_price` double(10, 2) NULL DEFAULT 0.00 COMMENT '用户支付金额',
  `pay_status` tinyint(3) NULL DEFAULT 10 COMMENT '支付状态(10待支付 20已支付)',
  `order_status` tinyint(3) NULL DEFAULT 10 COMMENT '订单状态(10未完成 20已完成 30退款中 40已退款 50退款被拒绝 60退款异常)',
  `pay_time` datetime(0) NULL DEFAULT NULL COMMENT '付款时间',
  `refund_time` datetime(0) NULL DEFAULT NULL COMMENT '退款时间',
  `transaction_id` varchar(30)  NULL DEFAULT '' COMMENT '微信支付交易号',
  `is_charge_buy` tinyint(3)  NULL DEFAULT 0 COMMENT '是否购买无忧充电(0否 1是)',
  `is_invalid` tinyint(3)  NULL DEFAULT 0 COMMENT '订单是否失效(0未失效 1已失效)',
  `is_settled` tinyint(3)  NULL DEFAULT 0 COMMENT '是否已结算佣金(0未结算 1已结算)',
  `first_proportion_money` float(10, 2) NULL DEFAULT 0.00 COMMENT '一级分成金额',
  `second_proportion_money` float(10, 2) NULL DEFAULT 0.00 COMMENT '二级分成金额',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '续费套餐充值订单表';


DROP TABLE IF EXISTS `wxapp_recharge_package_order_refund`;
CREATE TABLE `wxapp_recharge_package_order_refund`  (
  `id` varchar(50) NOT NULL COMMENT 'id',
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `order_id` int(0) NULL DEFAULT NULL COMMENT '订单id',
  `user_id` int(0) NULL DEFAULT NULL COMMENT 'user_id',
  `apply_desc` varchar(1000)  NULL DEFAULT '' COMMENT '用户申请原因(说明)',
  `is_agree` tinyint(3)  NULL DEFAULT 0 COMMENT '商家审核状态(0待审核 10已同意 20已拒绝)',
  `order_status` tinyint(3)  NULL DEFAULT 10 COMMENT '订单状态(10退款中 20已退款 30退款被拒绝 40退款异常 50已关闭)',
  `refuse_desc` varchar(1000)  NULL DEFAULT '' COMMENT '商家拒绝原因(说明)',
  `user_received_account` varchar(1000)  NULL DEFAULT '' COMMENT '退款入账账户',
  `refund_id` varchar(1000)  NULL DEFAULT '' COMMENT '微信退款单号',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '套餐退款记录表';



DROP TABLE IF EXISTS `wxapp_problem_type`;
CREATE TABLE `wxapp_problem_type`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `type_name` varchar(255) NULL DEFAULT NULL COMMENT '问题类型名称',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '问题类型表';


DROP TABLE IF EXISTS `wxapp_problem_feedback`;
CREATE TABLE `wxapp_problem_feedback`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `type_id` int(0) NULL DEFAULT NULL COMMENT '问题类型id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT 'note_id',
  `user_id` int(0) NULL DEFAULT NULL COMMENT '用户id',
  `problem_detail` mediumtext NULL DEFAULT NULL COMMENT '问题描述',
  `is_status` tinyint(3) NULL DEFAULT 10 COMMENT '维修状态 (10待处理 20已处理)',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '问题反馈表';

DROP TABLE IF EXISTS `wxapp_dealer_order`;
CREATE TABLE `wxapp_dealer_order`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT '社区id',
  `account_id` int(0) NULL DEFAULT NULL COMMENT '账户id',
  `order_id` varchar(50) NULL DEFAULT NULL COMMENT '订单id',
  `type` int(0) NULL DEFAULT NULL COMMENT '角色(5:代理商  6物业)',
  `order_price` double(10, 2)  NULL DEFAULT 0.00 COMMENT '订单支付总金额',
  `share_money` double(10, 2)  NULL DEFAULT 0.00 COMMENT '分成金额',
  `is_invalid` tinyint(3) NULL DEFAULT 0 COMMENT '订单是否失效(0未失效 1已失效)',
  `is_settled` tinyint(3) NULL DEFAULT 0 COMMENT '是否已结算佣金(0未结算 1已结算)',
  `settle_time` datetime(0) NULL DEFAULT NULL COMMENT '结算时间',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '分成订单记录表';


DROP TABLE IF EXISTS `wxapp_dealer_note`;
CREATE TABLE `wxapp_dealer_note`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` varchar(30) NULL DEFAULT NULL COMMENT 'note_id',
  `type` int(0) NULL DEFAULT NULL COMMENT '角色(5:代理商  6物业)',
  `account_id` int(0) NULL DEFAULT NULL COMMENT '账户id',
  `money` double(10, 2)  NULL DEFAULT 0.00 COMMENT '当前可提现佣金',
  `freeze_money` double(10, 2)  NULL DEFAULT 0.00 COMMENT '已冻结佣金',
  `total_money` double(10, 2)  NULL DEFAULT 0.00 COMMENT '累积提现佣金',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '社区收益记录表';


DROP TABLE IF EXISTS `wxapp_dealer_order_detail`;
CREATE TABLE `wxapp_dealer_order_detail`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `dealer_order_id` int(0) NULL DEFAULT NULL COMMENT '分成id',
  `old_price` double(10, 2)  NULL DEFAULT 0.00 COMMENT '原金额',
  `now_money` double(10, 2)  NULL DEFAULT 0.00 COMMENT '现金额',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '分成明细';



DROP TABLE IF EXISTS `wxapp_dealer_withdraw`;
CREATE TABLE `wxapp_dealer_withdraw`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` varchar(30) NULL DEFAULT NULL COMMENT 'note_id',
  `account_id` int(0) NULL DEFAULT NULL COMMENT '账户id',
  `money` double(10, 2)  NULL DEFAULT 0.00 COMMENT '提现金额',
  `reality_money` double(10, 2)  NULL DEFAULT 0.00 COMMENT '实际到账金额',
  `pay_type` tinyint(3) NULL DEFAULT 10 COMMENT '打款方式 (20支付宝 30银行卡)',
  `account_name` varchar(255) NULL DEFAULT '' COMMENT '账户名字',
  `account` varchar(255) NULL DEFAULT '' COMMENT '账号',
  `apply_status` tinyint(3) NULL DEFAULT 10 COMMENT '申请状态 (10待审核 20审核通过 30驳回 40已打款)',
  `audit_time` datetime(0) NULL DEFAULT NULL COMMENT '审核时间',
  `reject_reason` varchar(500) NULL DEFAULT '' COMMENT '驳回原因',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '提现明细表';



DROP TABLE IF EXISTS `wxapp_pod_door`;
CREATE TABLE `wxapp_pod_door`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT '社区id',
  `title` varchar(50) NULL DEFAULT '' COMMENT '标题',
  `serialnum` varchar(50) NULL DEFAULT '' COMMENT '设备序列号',
  `doorindex` enum('01','02','03','04')  NULL DEFAULT '01' COMMENT '门号(01,02,03,04)',
  `readhead_num` int(0) NULL DEFAULT 1 COMMENT '读头数（1单读头 2双读头）',
  `status` tinyint(3)  NULL DEFAULT 0 COMMENT '状态(0离线 1在线)',
  `lastip` varchar(50)  NULL DEFAULT '' COMMENT '最后上线IP',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '门禁信息表' ;


DROP TABLE IF EXISTS `wxapp_user_door_log`;
CREATE TABLE `wxapp_user_door_log`  (
  `id` varchar(50) NOT NULL COMMENT 'id',
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT 'note_id',
  `user_id` int(0) NULL DEFAULT NULL COMMENT 'user_id',
  `serialnum` varchar(50)  NULL DEFAULT '' COMMENT '设备序列号',
  `idno` varchar(50)  NULL DEFAULT '' COMMENT '门禁卡ID',
  `type` int(0) NULL DEFAULT NULL COMMENT '进门类型 0扫码 1刷卡 (or)rfid',
  `doorindex` enum('01','02','03','04') NOT NULL DEFAULT '01' COMMENT '门号(01,02,03,04)',
  `doorio` enum('01','02')  NULL DEFAULT '01' COMMENT '进门01/出门02',
  `status` tinyint(3)  NULL DEFAULT 0 COMMENT '状态(0不通过 1通过)',
  `pay_type` tinyint(3)  NULL DEFAULT 0 COMMENT '支付方式(1白名单 2包月 3余额 4微信)',
  `pay_status` tinyint(3)  NULL DEFAULT 0 COMMENT '支付状态(1未支付 2已付款 3已退款)',
  `money` double(10, 2)  NULL DEFAULT 0 COMMENT '支付金额',
  `residue_money` double(10, 2)  NULL DEFAULT 0 COMMENT '退款金额',
  `transaction_id` varchar(50)  NULL DEFAULT '' COMMENT '微信交易号',
  `pay_time` datetime(0) NULL DEFAULT NULL COMMENT '付款时间',
  `refund_time` datetime(0) NULL DEFAULT NULL COMMENT '退款时间',
  `is_due` int(0) NULL DEFAULT NULL COMMENT '是否欠费 0否 1是',
  `due_time` datetime(0) NULL DEFAULT NULL COMMENT '欠费时间',
  `is_invalid` int(0) NULL DEFAULT NULL COMMENT '订单是否失效(0未失效 1已失效)',
  `is_settled` int(0) NULL DEFAULT NULL COMMENT '是否已结算佣金(0未结算 1已结算)',
  `first_proportion_money` double(10, 2)  NULL DEFAULT 0 COMMENT '一级分成金额',
  `second_proportion_money` double(10, 2)  NULL DEFAULT 0 COMMENT '二级分成金额',
  `refund_id` varchar(50)  NULL DEFAULT '' COMMENT '微信退款单号',
  `user_received_account` varchar(50)  NULL DEFAULT '' COMMENT '退款入账账户',
  `reason` varchar(50)  NULL DEFAULT '' COMMENT '原因代码',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '门禁刷卡记录表';



DROP TABLE IF EXISTS `wxapp_door_idno`;
CREATE TABLE `wxapp_door_idno`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `user_id` int(0) NULL DEFAULT NULL COMMENT 'user_id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT '社区id',
  `idno` varchar(50) NULL DEFAULT '' COMMENT '门禁卡ID',
  `rfid` varchar(50) NULL DEFAULT '' COMMENT 'rfid卡ID',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '用户门禁id卡表';



DROP TABLE IF EXISTS `wxapp_door_cards`;
CREATE TABLE `wxapp_door_cards`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `type` int(0) NULL DEFAULT NULL COMMENT '1 IC卡 2 RFID',
  `cardid` varchar(50) NULL DEFAULT '' COMMENT '卡号',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '所有门禁卡';



DROP TABLE IF EXISTS `wxapp_user_balance_log`;
CREATE TABLE `wxapp_user_balance_log`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT 'note_id',
  `user_id` int(0) NULL DEFAULT NULL COMMENT 'user_id',
  `rechargeuser_id` int(0) NULL DEFAULT NULL COMMENT '充值用户id',
  `type` int(3) NULL DEFAULT 0 COMMENT '消费类型 1 充电 2 门禁 3 其他',
  `start_time` datetime(0) NULL DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime(0) NULL DEFAULT NULL COMMENT '到期时间',
  `scene` int(3) NULL DEFAULT 0 COMMENT '余额变动场景(10用户充值 20用户消费(微信扣款) 21用户消费(钱包扣款) 30管理员操作 40订单退款)',
  `money` double(10, 2)  NULL DEFAULT 0.00 COMMENT '金额',
  `describes` varchar(30) NULL DEFAULT '' COMMENT '描述',
  `remark` varchar(30) NULL DEFAULT '' COMMENT '备注',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '用户消费记录表' ;





DROP TABLE IF EXISTS `wxapp_payinfo`;
CREATE TABLE `wxapp_payinfo`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `orgid` varchar(255)  NOT NULL DEFAULT '' COMMENT '共享集团号/代理商参数时必填/v3key',
  `pay_type` int(11) NOT NULL DEFAULT 0 COMMENT '1.普通支付 2.通联支付',
  `mchid` varchar(255)  NOT NULL DEFAULT '' COMMENT 'mchid',
  `apikey` mediumtext  NOT NULL DEFAULT '' COMMENT 'serial_number (tl app_id)',
  `cert_pem` mediumtext  NOT NULL DEFAULT '' COMMENT 'cert_pem',
  `key_pem` datetime(0) NULL DEFAULT NULL COMMENT 'key_pem',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '支付信息表';



DROP TABLE IF EXISTS `wxapp_white_list`;
CREATE TABLE `wxapp_white_list`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `user_id` int(0) NULL DEFAULT NULL COMMENT 'user_id',
  `note_id` int(0) NULL DEFAULT NULL COMMENT 'note_id',
  `type` int(11) NOT NULL DEFAULT 0 COMMENT '套餐类型 (1:停车包 2:停车加充电包)',
  `special_start` datetime(0) NULL DEFAULT NULL COMMENT '开始时间',
  `special_end` datetime(0) NULL DEFAULT NULL COMMENT '到期时间',
  `remarks` varchar(255)  NOT NULL DEFAULT '' COMMENT '备注',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '白名单表';



DROP TABLE IF EXISTS `wxapp_operate_record`;
CREATE TABLE `wxapp_operate_record`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `user_id` int(0) NULL DEFAULT NULL COMMENT '管理员id',
  `describes` varchar(255)  NOT NULL DEFAULT '' COMMENT '操作描述',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '操作日志表';


DROP TABLE IF EXISTS `wxapp_user`;
CREATE TABLE `wxapp_user`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `note_id` varchar(30) NULL DEFAULT NULL COMMENT '社区id',
  `authority_id` int(0) NULL DEFAULT NULL COMMENT '权限id',
  `mobile` varchar(11)  NOT NULL DEFAULT '' COMMENT '手机号',
  `password` varchar(100)  NOT NULL DEFAULT '' COMMENT '密码',
  `open_id` varchar(255)  NOT NULL DEFAULT '' COMMENT 'open_id',
  `nickname` varchar(255)  NOT NULL DEFAULT '' COMMENT '昵称',
  `avatar` varchar(255)  NOT NULL DEFAULT '' COMMENT '头像',
  `gender` int(11) NOT NULL DEFAULT 0 COMMENT '性别',
  `is_freeze` int(11) NOT NULL DEFAULT 0 COMMENT '是否冻结 1是 0否',
  `is_manage` int(11) NOT NULL DEFAULT 0 COMMENT '账号类型0:微信用户 1:系统管理员 2:操作员 3:区域操作员 5:代理商 6:物业',
  `balance` double(10, 2)  NULL DEFAULT 0.00 COMMENT '用户可用余额',
  `virtual_balance` double(10, 2)  NULL DEFAULT 0.00 COMMENT '虚拟余额',
  `point` double(10, 2)  NULL DEFAULT 0.00 COMMENT '积分',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '用户表';


DROP TABLE IF EXISTS `wxapp_mini`;
CREATE TABLE `wxapp_mini`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_name` varchar(30) NULL DEFAULT NULL COMMENT '小程序名称',
  `authorizer_appid` varchar(30) NULL DEFAULT NULL COMMENT 'authorizer_appid',
  `secret` varchar(30) NULL DEFAULT NULL COMMENT 'secret',
  `access_token` varchar(30) NULL DEFAULT NULL COMMENT 'access_token',
  `expird_time` datetime(0) NULL DEFAULT NULL COMMENT '过期时间',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '小程序表';


DROP TABLE IF EXISTS `wxapp_authority_log`;
CREATE TABLE `wxapp_authority_log`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `mini_id` int(0) NULL DEFAULT NULL COMMENT '小程序id',
  `user_id` int(0) NULL DEFAULT NULL COMMENT '用户id',
  `url` varchar(50) NULL DEFAULT NULL COMMENT '请求路径',
  `params` varchar(255) NULL DEFAULT NULL COMMENT '请求参数',
  `describes` mediumtext NULL COMMENT '描述',
  `deal_status` int(11) NOT NULL DEFAULT 0 COMMENT '审核状态 1已处理 0未处理',
  `add_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE = InnoDB COMMENT = '权限操作记录表';