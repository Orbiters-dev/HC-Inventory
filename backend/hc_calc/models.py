import datetime

from django.db import models
from django.utils import timezone

class ShippingRecord(models.Model):
    key = models.IntegerField(unique=True)
    date_of_dept = models.DateField()
    brand = models.CharField(max_length=100)
    po = models.CharField(max_length=100)
    cbm_invoice = models.FloatField()
    cbm_pl = models.FloatField()
    cbm_inv_per_pl = models.FloatField()
    pallet = models.IntegerField()
    local_delivery = models.FloatField()
    delivery_per_cbm_7 = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "A.[Dataset_1_I] Shipping Records"
        ordering = ["-key"]
        db_table = "shipping_records"


# 운임 지수 추가
class DeliveryIndex(models.Model):
    key = models.IntegerField(unique=True)
    date = models.DateField()
    delivery_idx_teu = models.FloatField()
    real_per_idx_teu = models.FloatField()
    delivery_real_teu = models.FloatField()
    delivery_idx_feu = models.FloatField()
    real_per_idx_feu = models.FloatField()
    delivery_real_feu = models.FloatField()
    avg_del_per_cbm = models.FloatField()
    del_per_cbm_1 = models.FloatField()
    del_per_cbm_2 = models.FloatField(null=True, blank=True)
    del_per_cbm_3 = models.FloatField(null=True, blank=True)
    del_per_cbm_4 = models.FloatField(null=True, blank=True)
    del_per_cbm_5 = models.FloatField(null=True, blank=True)
    del_per_cbm_6 = models.FloatField(null=True, blank=True)
    del_per_cbm_7 = models.FloatField(null=True, blank=True)
    del_per_cbm_8 = models.FloatField(null=True, blank=True)
    del_per_cbm_9 = models.FloatField(null=True, blank=True)
    del_per_cbm_10 = models.FloatField(null=True, blank=True)
    del_per_cbm_11 = models.FloatField(null=True, blank=True)
    del_per_cbm_12 = models.FloatField(null=True, blank=True)
    del_per_cbm_13 = models.FloatField(null=True, blank=True)
    del_per_cbm_14 = models.FloatField(null=True, blank=True)
    del_per_cbm_15 = models.FloatField(null=True, blank=True)
    del_per_cbm_16 = models.FloatField(null=True, blank=True)
    del_per_cbm_17 = models.FloatField(null=True, blank=True)
    del_per_cbm_18 = models.FloatField(null=True, blank=True)
    del_per_cbm_19 = models.FloatField(null=True, blank=True)
    del_per_cbm_20 = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "A.[Dataset_2_I] Delivery Indices"
        ordering = ["-key"]
        db_table = "delivery_indices"


# 중간 산출 테이블
class DeliveryIndicesSummary(models.Model):
    key = models.IntegerField(unique=True, default=1)
    recent_teu = models.FloatField(null=True, blank=True)
    avg_real_per_idx_teu = models.FloatField(null=True, blank=True)
    recent_feu = models.FloatField(null=True, blank=True)
    avg_real_per_idx_feu = models.FloatField(null=True, blank=True)
    recent_3_months_avg_cbm = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "A.[Dataset_2_O] Delivery Indices Summary"
        db_table = "delivery_indices_summary"


class ShippingRecordsSummary(models.Model):
    key = models.IntegerField(unique=True, default=1)
    avg_cbm_inv_per_pl = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "A.[Dataset_1_O] Shipping Records Summary"
        db_table = "shipping_records_summary"


# Common Center Outbound Fee 테이블
"""
데이터 샘플
key	so	no_of_box	unit	weight_kg	fulfillment_fee	per_box	per_unit	per_kg
	SO488529	15	960	187.33	475.03	31.66866667	0.494822917	2.535792452
	SO531492	6	420	80.74	208.83	34.805	0.497214286	2.586450334
	SO539880	12	900	170.55	412.59	34.3825	0.458433333	2.419173263
	SO547439	8	600	123.38	253.32	31.665	0.4222	2.053169071
...

db명: common_center_outbound_fee

int key,
char 50 so,
int no_of_box,
int unit,
float weight_kg,
float fulfillment_fee,
float per_box,
float per_unit,
float per_kg
"""


class CommonCenterOutboundFee(models.Model):
    key = models.AutoField(primary_key=True)
    so = models.CharField(max_length=50)
    no_of_box = models.IntegerField()
    unit = models.IntegerField()
    weight_kg = models.FloatField()
    fulfillment_fee = models.FloatField()
    per_box = models.FloatField()
    per_unit = models.FloatField()
    per_kg = models.FloatField()

    def __str__(self):
        return f"SO: {self.so} - Fulfillment Fee: {self.fulfillment_fee}"

    class Meta:
        db_table = "common_center_outbound_fee"
        verbose_name_plural = "A.[Dataset_3] Common Center Outbound Fees"


# Variables 테이블


class VariableConfigurations(models.Model):
    no = models.IntegerField()  # 일련번호, 수정 불가
    category = models.CharField(max_length=30, blank=False, null=False)
    name = models.CharField(max_length=50, blank=False, null=False)
    value = models.FloatField()
    value_type = models.CharField(max_length=20, blank=False, null=False)
    unit = models.CharField(max_length=20, blank=True, null=True, default="-")
    minimum = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True, default="-"
    )
    details = models.CharField(max_length=255, blank=True, null=True, default="-")

    def __str__(self):
        return f"{self.category} - {self.name}"

    class Meta:
        db_table = "variable_configurations"
        verbose_name_plural = "A.[Dataset_6] Variable Configurations"


# Ground Service 테이블


class GroundService(models.Model):
    key = models.IntegerField(unique=True, default="default_key")
    lbs = models.FloatField()
    zone_2 = models.FloatField()
    zone_3 = models.FloatField()
    zone_4 = models.FloatField()
    zone_5 = models.FloatField()
    zone_6 = models.FloatField()
    zone_7 = models.FloatField()
    zone_8 = models.FloatField()

    def __str__(self):
        return f"Key {self.key} - Lbs: {self.lbs}"

    class Meta:
        verbose_name_plural = "A.[Dataset_4_I] Ground Service Charges"
        db_table = "ground_service"


# Weighted Ground Service 테이블


class WeightedGroundService(models.Model):
    key = models.IntegerField(unique=True, default="default_key")
    lbs = models.FloatField()
    weighted_zone_2 = models.FloatField()
    weighted_zone_3 = models.FloatField()
    weighted_zone_4 = models.FloatField()
    weighted_zone_5 = models.FloatField()
    weighted_zone_6 = models.FloatField()
    weighted_zone_7 = models.FloatField()
    weighted_zone_8 = models.FloatField()
    weighted_zone_average = models.FloatField(default=0)

    def __str__(self):
        return f"Key {self.key} - Lbs: {self.lbs}"

    class Meta:
        verbose_name_plural = "A.[Dataset_4_O] Weighted Ground Service Charges"
        db_table = "weighted_ground_service"


# Zone Weight 테이블


class ZoneWeight(models.Model):
    key = models.IntegerField(unique=True)
    zone_2_weight = models.FloatField(default=1.0, verbose_name="Zone 2 Weight")
    zone_3_weight = models.FloatField(default=1.0, verbose_name="Zone 3 Weight")
    zone_4_weight = models.FloatField(default=1.0, verbose_name="Zone 4 Weight")
    zone_5_weight = models.FloatField(default=1.0, verbose_name="Zone 5 Weight")
    zone_6_weight = models.FloatField(default=1.0, verbose_name="Zone 6 Weight")
    zone_7_weight = models.FloatField(default=1.0, verbose_name="Zone 7 Weight")
    zone_8_weight = models.FloatField(default=1.0, verbose_name="Zone 8 Weight")
    discount = models.FloatField(default=0)

    def __str__(self):
        return "Weights"

    class Meta:
        ordering = ["-key"]
        verbose_name_plural = "A.[Dataset_4_X] Zone Weights"
        db_table = "zone_weight"


# Amazone Referral Fee Simple 테이블
"""
데이터 샘플
key	category	referral_fee_rate	minimum_fee	extra_fee
1	Amazon Device Accessories	0.45	0.3	0
2	Amazon Explore	0.3	2	0
...

db명: amazon_referral_fee_simple

int key,
char category,
float referral_fee_rate not blank/null,
float minimum_fee 기본값 0,
float extra_fee 기본값 0
"""


class AmazonReferralFeeSimple(models.Model):
    key = models.IntegerField(unique=True)
    category = models.CharField(max_length=100)
    referral_fee_rate = models.FloatField(blank=False, null=False)
    minimum_fee = models.FloatField(default=0)
    extra_fee = models.FloatField(default=0)

    def __str__(self):
        return f"{self.key} - {self.category}"

    class Meta:
        verbose_name_plural = "B.[Amz_1] Amazon Referral Fee Simple"
        db_table = "amazon_referral_fee_simple"


# Amazon Referral Fee Complex 테이블
"""
데이터 샘플
key	category	price_range_operator	price_range_value	referral_fee_rate	minimum_fee	extra_fee	type
1	Baby Products	<=	10	0.08	0.3	0	simple
2	Baby Products	>	10	0.15	0.3	0	simple
3	Beauty, Health and Personal Care	<=	10	0.08	0.3	0	simple
...

db명: amazon_referral_fee_complex

int key,
char category,
char price_range_operator,
float price_range_value,
float referral_fee_rate,
float minimum_fee 기본값 0,
float extra_fee 기본값 0,
char type
"""


class AmazonReferralFeeComplex(models.Model):
    key = models.IntegerField(unique=True)
    category = models.CharField(max_length=100)
    price_range_operator = models.CharField(max_length=2)
    price_range_value = models.FloatField()
    referral_fee_rate = models.FloatField()
    minimum_fee = models.FloatField(default=0)
    extra_fee = models.FloatField(default=0)
    type = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.key} - {self.category}"

    class Meta:
        verbose_name_plural = "B.[Amz_2] Amazon Referral Fee Complex"
        db_table = "amazon_referral_fee_complex"


# Amazon Product Tier 테이블
"""
데이터 샘플
key	product_tier_1	product_tier_2	shipping_wgt_lbs_opr	shipping_wgt_lbs_val	longest_inch_opr	longest_inch_val	median_inch_opr	median_inch_val	shortes_inch_opr	shortes_inch_val	lengirth_inch_opr	lengirth_inch_val
1	standard	small_std	<=	1	<=	15	<=	12	<=	0.75
2	standard	large_std	<=	20	<=	18	<=	14	<=	8
3	oversize	large_bulky	<=	50	<=	59	<=	33	<=	33	<=	130
4	oversize	ex_large_50	<=	50	>	59	>	33	>	33	>	130
...

db명: amazon_product_tier

int key,
char product_tier_1,
char product_tier_2,
char shipping_wgt_lbs_opr,
float shipping_wgt_lbs_val,
char longest_inch_opr,
float longest_inch_val,
char median_inch_opr,
float median_inch_val,
char shortes_inch_opr,
float shortes_inch_val,
char lengirth_inch_opr 기본값 None,
float lengirth_inch_val 기본값 None
"""


class AmazonProductTier(models.Model):
    key = models.IntegerField(unique=True)
    product_tier_1 = models.CharField(max_length=50)
    product_tier_2 = models.CharField(max_length=50)
    shipping_wgt_lbs_opr = models.CharField(max_length=2)
    shipping_wgt_lbs_val = models.FloatField()
    longest_inch_opr = models.CharField(max_length=2)
    longest_inch_val = models.FloatField()
    median_inch_opr = models.CharField(max_length=2)
    median_inch_val = models.FloatField()
    shortes_inch_opr = models.CharField(max_length=2)
    shortes_inch_val = models.FloatField()
    lengirth_inch_opr = models.CharField(max_length=2, null=True, blank=True, default=None)
    lengirth_inch_val = models.FloatField(null=True, blank=True, default=None)

    def __str__(self):
        return f"{self.key} - {self.product_tier_1} / {self.product_tier_2}"

    class Meta:
        verbose_name_plural = "B.[Amz_3_0] Amazon Product Tier"
        db_table = "amazon_product_tier"


# Amazon Fulfillment Fee 테이블
"""
데이터 샘플
key	category	product_tier_1	product_tier_2	shipping_wgt_lbs_opr	shipping_wgt_lbs_val	fulfillment_fee	extra_fee	condition
1	Non Apparel	standard	small_std	<=	0.125	3.06
2	Non Apparel	standard	small_std	<=	0.25	3.15
3	Non Apparel	standard	small_std	<=	0.375	3.24
4	Non Apparel	standard	small_std	<=	0.5	3.33	0.38	/0.25 lbs above 3lb
...

db명: amazon_fulfillment_fee

int key,
char category,
char product_tier_1,
char product_tier_2,
char shipping_wgt_lbs_opr,
float shipping_wgt_lbs_val,
float fulfillment_fee,
float extra_fee 기본값 0,
char condition 기본값 None
"""


class AmazonFulfillmentFee(models.Model):
    key = models.IntegerField(unique=True)
    category = models.CharField(max_length=50)
    product_tier_1 = models.CharField(max_length=50)
    product_tier_2 = models.CharField(max_length=50)
    shipping_wgt_lbs_opr = models.CharField(max_length=2)
    shipping_wgt_lbs_val = models.FloatField()
    fulfillment_fee = models.FloatField()
    extra_fee = models.FloatField(default=0)
    condition = models.CharField(max_length=100, null=True, blank=True, default=None)

    def __str__(self):
        return f"{self.key} - {self.category} - {self.product_tier_1} / {self.product_tier_2}"

    class Meta:
        verbose_name_plural = "B.[Amz_3_1] Amazon Fulfillment Fee"
        db_table = "amazon_fulfillment_fee"


# Common Storage Fee 테이블
"""
데이터 샘플
key	type	prd_tier	mon_opr	mon_val	mon_period_1	period_1_val	mon_period_2	period_2_val	mon_weighted_avg
1	amz	standard			9	0.78	3	2.4
2	amz	oversize			9	0.56	3	1.4
3	wmt		<=	1	9	0.75	3	0.75
4	wmt		>	1	9	0.75	3	2.25
...

db명: common_storage_fee

int key,
char type,
char prd_tier 기본값 None,
char mon_opr 기본값 None,
float mon_val 기본값 None,
int mon_period_1,
float period_1_val,
int mon_period_2,
float period_2_val,
float mon_weighted_avg
"""


class CommonStorageFee(models.Model):
    key = models.IntegerField(unique=True)
    type = models.CharField(max_length=50)
    prd_tier = models.CharField(max_length=50, null=True, blank=True, default=None)
    mon_opr = models.CharField(max_length=2, null=True, blank=True, default=None)
    mon_val = models.FloatField(null=True, blank=True, default=None)
    mon_period_1 = models.IntegerField()
    period_1_val = models.FloatField()
    mon_period_2 = models.IntegerField()
    period_2_val = models.FloatField()
    mon_weighted_avg = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.key} - {self.type} - {self.prd_tier}"

    class Meta:
        verbose_name_plural = "A.[Dataset_5] Common Storage Fee"
        db_table = "common_storage_fee"


# Amazon Inbound Fee 테이블
"""
key	product_tier_1	product_tier_2	shipping_wgt_lbs_opr	shipping_wgt_lbs_val	inbound_fee_Med	inbound_fee_MAX	inbound_fee_min
1	standard	small_std	<=	1		0.21	0.12
2	standard	large_std	<=	0.75		0.24	0.13
3	standard	large_std	<=	1.5		0.28	0.15
4	standard	large_std	<=	3		0.34	0.17
...

db명: amazon_inbound_fee

int key,
char product_tier_1,
char product_tier_2,
char shipping_wgt_lbs_opr,
float shipping_wgt_lbs_val,
float inbound_fee_Med blank/null True,
float inbound_fee_MAX blank/null True,
float inbound_fee_min blank/null True
"""


class AmazonInboundFee(models.Model):
    key = models.IntegerField(unique=True)
    product_tier_1 = models.CharField(max_length=50)
    product_tier_2 = models.CharField(max_length=50)
    shipping_wgt_lbs_opr = models.CharField(max_length=2)
    shipping_wgt_lbs_val = models.FloatField()
    inbound_fee_Med = models.FloatField(null=True, blank=True)
    inbound_fee_MAX = models.FloatField(null=True, blank=True)
    inbound_fee_min = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.key} - {self.product_tier_1} / {self.product_tier_2}"

    class Meta:
        verbose_name_plural = "B.[Amz_3_2] Amazon Inbound Fee"
        db_table = "amazon_inbound_fee"


# Walmart Referral Fee Simple 테이블
"""
데이터 샘플
key	category	referral_fee_rate
1	Automotive & Powersports	0.12
2	Automotive Electronics	0.08
3	Books	0.15
4	Camera & Photo	0.08
...

db명: walmart_referral_fee_simple

int key,
char category,
float referral_fee_rate
"""


class WalmartReferralFeeSimple(models.Model):
    key = models.IntegerField(unique=True)
    category = models.CharField(max_length=50)
    referral_fee_rate = models.FloatField()

    def __str__(self):
        return f"{self.key} - {self.category}"

    class Meta:
        verbose_name_plural = "C.[Wmt_1] Walmart Referral Fee Simple"
        db_table = "walmart_referral_fee_simple"


# Walmart Referral Fee Complex 테이블
"""
데이터 샘플
key	category	price_range_operator	price_range_value	referral_fee_rate	type
1	Apparel & Accessories	<=	15	0.05	simple
2	Apparel & Accessories	<=	20	0.1	simple
3	Apparel & Accessories	>	20	0.15	simple
4	Baby	<=	10	0.08	simple
...

verbose_name_plural: Walmart Referral Fee Complex
db명: walmart_referral_fee_complex

int key,
char category,
char price_range_operator,
float price_range_value,
float referral_fee_rate,
char type
"""


class WalmartReferralFeeComplex(models.Model):
    key = models.IntegerField(unique=True)
    category = models.CharField(max_length=50)
    price_range_operator = models.CharField(max_length=2)
    price_range_value = models.FloatField()
    referral_fee_rate = models.FloatField()
    type = models.CharField(max_length=50)

    def __str__(self):
        return (
            f"{self.key} - {self.category} - {self.price_range_operator} {self.price_range_value}"
        )

    class Meta:
        db_table = "walmart_referral_fee_complex"
        verbose_name_plural = "C.[Wmt_2] Walmart Referral Fee Complex"


# Walmart Fulfillment Fee 테이블
"""
데이터 샘플
key	product_tier	shipping_wgt_lbs_from_opr	shipping_wgt_lbs_from_val	shipping_wgt_lbs_to_opr	shipping_wgt_lbs_to_val	fulfillment_fee	extra_fee	extra_condition	add_category	add_val	add_min_opr	add_min_val	add_min_fee	long_in_fr_opr_1	long_in_fr_val_1	long_in_to_opr_1	long_in_to_val_1	long_in_add_1	med_in_opr	med_in_val	med_in_add	lg_in_fr_opr_1	lg_in_fr_val_1	lg_in_to_opr_1	lg_in_to_opr_1	lg_in_add_1	long_in_fr_opr_2	long_in_fr_val_2	long_in_to_opr_2	long_in_to_val_2	long_in_add_2	lg_in_fr_opr_2	lg_in_fr_val_2	lg_in_to_opr_2	lg_in_to_opr_2	lg_in_add_2
1	standard	>=	0	<=	1	3.45			Apparel & Accessories	0.5	<	10	1	>	48	<=	96	3	>	30	3	>	105	<=	130	3	>	96	<=	108	20	>	130	<=	165	20
2	standard	>	1	<=	2	4.95			Apparel & Accessories	0.5	<	10	1	>	48	<=	96	3	>	30	3	>	105	<=	130	3	>	96	<=	108	20	>	130	<=	165	20
3	standard	>	2	<=	3	5.45			Apparel & Accessories	0.5	<	10	1	>	48	<=	96	3	>	30	3	>	105	<=	130	3	>	96	<=	108	20	>	130	<=	165	20
4	standard	>	3	<=	20	5.75	0.4	$0.40/lb above 4lb	Apparel & Accessories	0.5	<	10	1	>	48	<=	96	3	>	30	3	>	105	<=	130	3	>	96	<=	108	20	>	130	<=	165	20
...

verbose_name_plural: Walmart Fulfillment Fee
db명: walmart_fulfillment_fee

int key,
char product_tier,
char shipping_wgt_lbs_from_opr,
float shipping_wgt_lbs_from_val,
char shipping_wgt_lbs_to_opr,
float shipping_wgt_lbs_to_val,
float fulfillment_fee,
float extra_fee blank/null True,
char extra_condition blank/null True,
char add_category blank/null True,
float add_val blank/null True,
char add_min_opr blank/null True,
float add_min_val blank/null True,
float add_min_fee blank/null True,
char long_in_fr_opr_1 blank/null True,
float long_in_fr_val_1 blank/null True,
char long_in_to_opr_1 blank/null True,
float long_in_to_val_1 blank/null True,
float long_in_add_1 blank/null True,
char med_in_opr blank/null True,
float med_in_val blank/null True,
float med_in_add blank/null True,
char lg_in_fr_opr_1 blank/null True,
float lg_in_fr_val_1 blank/null True,
char lg_in_to_opr_1 blank/null True,
float lg_in_to_val_1 blank/null True,
float lg_in_add_1 blank/null True,
char long_in_fr_opr_2 blank/null True,
float long_in_fr_val_2 blank/null True,
char long_in_to_opr_2 blank/null True,
float long_in_to_val_2 blank/null True,
float long_in_add_2 blank/null True,
char lg_in_fr_opr_2 blank/null True,
float lg_in_fr_val_2 blank/null True,
char lg_in_to_opr_2 blank/null True,
float lg_in_to_val_2 blank/null True,
float lg_in_add_2 blank/null True
"""


class WalmartFulfillmentFee(models.Model):
    key = models.IntegerField(unique=True)
    product_tier = models.CharField(max_length=50)
    shipping_wgt_lbs_from_opr = models.CharField(max_length=10)  # 적절한 길이로 수정
    shipping_wgt_lbs_from_val = models.FloatField()
    shipping_wgt_lbs_to_opr = models.CharField(max_length=10)  # 적절한 길이로 수정
    shipping_wgt_lbs_to_val = models.FloatField()
    fulfillment_fee = models.FloatField()
    extra_fee = models.FloatField(null=True, blank=True)
    extra_condition = models.CharField(max_length=100, null=True, blank=True)
    add_category = models.CharField(max_length=50, null=True, blank=True)
    add_val = models.FloatField(null=True, blank=True)
    add_min_opr = models.CharField(max_length=10, null=True, blank=True)  # 적절한 길이로 수정
    add_min_val = models.FloatField(null=True, blank=True)
    add_min_fee = models.FloatField(null=True, blank=True)
    long_in_fr_opr_1 = models.CharField(max_length=10, null=True, blank=True)  # 적절한 길이로 수정
    long_in_fr_val_1 = models.FloatField(null=True, blank=True)
    long_in_to_opr_1 = models.CharField(max_length=10, null=True, blank=True)  # 적절한 길이로 수정
    long_in_to_val_1 = models.FloatField(null=True, blank=True)
    long_in_add_1 = models.FloatField(null=True, blank=True)
    med_in_opr = models.CharField(max_length=10, null=True, blank=True)  # 적절한 길이로 수정
    med_in_val = models.FloatField(null=True, blank=True)
    med_in_add = models.FloatField(null=True, blank=True)
    lg_in_fr_opr_1 = models.CharField(max_length=10, null=True, blank=True)  # 적절한 길이로 수정
    lg_in_fr_val_1 = models.FloatField(null=True, blank=True)
    lg_in_to_opr_1 = models.CharField(max_length=10, null=True, blank=True)  # 적절한 길이로 수정
    lg_in_to_val_1 = models.FloatField(null=True, blank=True)
    lg_in_add_1 = models.FloatField(null=True, blank=True)
    long_in_fr_opr_2 = models.CharField(max_length=10, null=True, blank=True)  # 적절한 길이로 수정
    long_in_fr_val_2 = models.FloatField(null=True, blank=True)
    long_in_to_opr_2 = models.CharField(max_length=10, null=True, blank=True)  # 적절한 길이로 수정
    long_in_to_val_2 = models.FloatField(null=True, blank=True)
    long_in_add_2 = models.FloatField(null=True, blank=True)
    lg_in_fr_opr_2 = models.CharField(max_length=10, null=True, blank=True)  # 적절한 길이로 수정
    lg_in_fr_val_2 = models.FloatField(null=True, blank=True)
    lg_in_to_opr_2 = models.CharField(max_length=10, null=True, blank=True)  # 적절한 길이로 수정
    lg_in_to_val_2 = models.FloatField(null=True, blank=True)
    lg_in_add_2 = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.key} - {self.product_tier}"

    class Meta:
        db_table = "walmart_fulfillment_fee"
        verbose_name_plural = "C.[Wmt_3] Walmart Fulfillment Fee"


class CompanyBoxFee(models.Model):
    key = models.IntegerField(unique=True)
    type = models.CharField(max_length=50)
    longest = models.FloatField()
    median = models.FloatField()
    shortest = models.FloatField()
    unit_price = models.FloatField()

    def __str__(self):
        return f"Key: {self.key} - Type: {self.type} - Unit Price: {self.unit_price}"

    class Meta:
        db_table = "company_box_fee"
        verbose_name_plural = "A.[Dataset_7] Company Box Fee"


class AdditionalDeliveryFee(models.Model):
    key = models.IntegerField(unique=True, default="default_key")
    zone_2 = models.FloatField(default=1.0)
    zone_3 = models.FloatField(default=1.0)
    zone_4 = models.FloatField(default=1.0)
    zone_5 = models.FloatField(default=1.0)
    zone_6 = models.FloatField(default=1.0)
    zone_7 = models.FloatField(default=1.0)
    zone_8 = models.FloatField(default=1.0)
    weighted_average = models.FloatField(default=0)
    conditions = models.CharField(max_length=200)

    def __str__(self):
        return f"Weights - {self.zone_2}, {self.zone_3}, {self.zone_4}, {self.zone_5}, {self.zone_6}, {self.zone_7}, {self.zone_8}, {self.weighted_average}"

    def save(self, *args, **kwargs):
        zone_weight = ZoneWeight.objects.latest("key")

        weighted_sum = (
            self.zone_2 * zone_weight.zone_2_weight
            + self.zone_3 * zone_weight.zone_3_weight
            + self.zone_4 * zone_weight.zone_4_weight
            + self.zone_5 * zone_weight.zone_5_weight
            + self.zone_6 * zone_weight.zone_6_weight
            + self.zone_7 * zone_weight.zone_7_weight
            + self.zone_8 * zone_weight.zone_8_weight
        )
        total_weight = (
            zone_weight.zone_2_weight
            + zone_weight.zone_3_weight
            + zone_weight.zone_4_weight
            + zone_weight.zone_5_weight
            + zone_weight.zone_6_weight
            + zone_weight.zone_7_weight
            + zone_weight.zone_8_weight
        )
        if zone_weight.discount == 0:
            self.weighted_average = weighted_sum / total_weight
        else:
            self.weighted_average = weighted_sum / total_weight * (1 - zone_weight.discount)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "B.[Dataset_1] Additional Delivery Charge"
        db_table = "additional_delivery_fee"


class CalculationLog(models.Model):
    # 사용자 입력 필드
    num_pallets = models.IntegerField()
    products_per_carton = models.IntegerField()
    cartons_per_pallet = models.IntegerField()
    product_width = models.DecimalField(max_digits=10, decimal_places=2)
    product_height = models.DecimalField(max_digits=10, decimal_places=2)
    product_length = models.DecimalField(max_digits=10, decimal_places=2)
    product_weight = models.DecimalField(max_digits=10, decimal_places=2)
    cost_per_product = models.DecimalField(max_digits=10, decimal_places=2)
    amazon_price = models.DecimalField(max_digits=10, decimal_places=2)
    amazon_category = models.CharField(max_length=100)
    walmart_price = models.DecimalField(max_digits=10, decimal_places=2)
    walmart_category = models.CharField(max_length=100)
    own_shop_price = models.DecimalField(max_digits=10, decimal_places=2)
    own_aov = models.DecimalField(max_digits=10, decimal_places=2)

    # 계산 결과 필드
    total_products = models.IntegerField()
    estimated_price_own = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_price_amz = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_price_wmt = models.DecimalField(max_digits=10, decimal_places=2)
    product_cost = models.DecimalField(max_digits=10, decimal_places=2)
    freight_charges = models.DecimalField(max_digits=10, decimal_places=2)
    customs_charges = models.DecimalField(max_digits=10, decimal_places=2)
    devanning_cost = models.DecimalField(max_digits=10, decimal_places=2)
    declaration_fee = models.DecimalField(max_digits=10, decimal_places=2)
    port_charges = models.DecimalField(max_digits=10, decimal_places=2)
    bol_value = models.DecimalField(max_digits=10, decimal_places=2)
    receiving_charges = models.DecimalField(max_digits=10, decimal_places=2)
    total_export_and_associated_costs = models.DecimalField(max_digits=10, decimal_places=2)
    export_and_associated_costs_per_product = models.DecimalField(max_digits=10, decimal_places=2)
    profit_after_arrival_own = models.DecimalField(max_digits=10, decimal_places=2)
    profit_after_arrival_amz = models.DecimalField(max_digits=10, decimal_places=2)
    profit_after_arrival_wmt = models.DecimalField(max_digits=10, decimal_places=2)
    fulfillment_cost = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_cost_own = models.DecimalField(max_digits=10, decimal_places=2)
    amazon_referral_fee = models.DecimalField(max_digits=10, decimal_places=2)

    # 아마존 물류비 상세 필드
    amazon_fulfillment_fee = models.DecimalField(max_digits=10, decimal_places=2)
    amazon_storage_fee = models.DecimalField(max_digits=10, decimal_places=2)
    amazon_inbound_fee = models.DecimalField(max_digits=10, decimal_places=2)
    amazon_fba_logistics_fee = models.DecimalField(max_digits=10, decimal_places=2)

    amazon_fba_receiving_cost = models.DecimalField(max_digits=10, decimal_places=2)
    walmart_referral_fee = models.DecimalField(max_digits=10, decimal_places=2)

    # 월마트 물류비 상세 필드
    walmart_fulfillment_fee = models.DecimalField(max_digits=10, decimal_places=2)
    walmart_storage_fee = models.DecimalField(max_digits=10, decimal_places=2)
    walmart_wfs_logistics_fee = models.DecimalField(max_digits=10, decimal_places=2)

    walmart_wfs_receiving_cost = models.DecimalField(max_digits=10, decimal_places=2)
    own_result = models.DecimalField(max_digits=10, decimal_places=2)
    amz_result = models.DecimalField(max_digits=10, decimal_places=2)
    wmt_result = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.id} at {self.created_at}"

    class Meta:
        db_table = "user_calculation_log"
        verbose_name_plural = "X.[Admin] User Calculation Logs"


