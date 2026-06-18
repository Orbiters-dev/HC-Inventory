"""hc_calc 계산 로직 — calculations/services.py 49~1679 슬림 포크.

라벨/엑셀/재고 함수(1682~2012)와 barcode/openpyxl/PIL/재고모델 import 제외.
SummaryUpdater / 계산함수 / fee 클래스 / output_reporting 만 포함.
"""

import logging
import math
import operator
import re
import traceback

from django.db.models import Avg, Sum
from django.utils import timezone

from .models import (
    AdditionalDeliveryFee,
    AmazonFulfillmentFee,
    AmazonInboundFee,
    AmazonProductTier,
    AmazonReferralFeeComplex,
    AmazonReferralFeeSimple,
    CommonCenterOutboundFee,
    CommonStorageFee,
    CompanyBoxFee,
    DeliveryIndex,
    DeliveryIndicesSummary,
    ShippingRecord,
    ShippingRecordsSummary,
    VariableConfigurations,
    WalmartFulfillmentFee,
    WalmartReferralFeeComplex,
    WalmartReferralFeeSimple,
    WeightedGroundService,
)

logger = logging.getLogger(__name__)


def get_operator_func(op):
    ops = {
        "<": operator.lt,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
        ">=": operator.ge,
        ">": operator.gt,
    }
    return ops.get(op)


# SummaryUpdater 클래스 정의
class SummaryUpdater:
    @staticmethod
    def update_delivery_indices_summary():
        # 최신 데이터 기반 값 계산
        try:
            recent_teu = DeliveryIndex.objects.latest("date").delivery_idx_teu
            avg_real_per_idx_teu = DeliveryIndex.objects.aggregate(
                Avg("real_per_idx_teu")
            )["real_per_idx_teu__avg"]
            recent_feu = DeliveryIndex.objects.latest("date").delivery_idx_feu
            avg_real_per_idx_feu = DeliveryIndex.objects.aggregate(
                Avg("real_per_idx_feu")
            )["real_per_idx_feu__avg"]
            recent_3_months_avg_cbm = DeliveryIndex.objects.order_by("-date")[
                :3
            ].aggregate(Avg("avg_del_per_cbm"))["avg_del_per_cbm__avg"]

            # DeliveryIndicesSummary 모델 업데이트
            DeliveryIndicesSummary.objects.update_or_create(
                key=1,  # 특정 필드를 기준으로 업데이트
                defaults={
                    "recent_teu": recent_teu,
                    "avg_real_per_idx_teu": avg_real_per_idx_teu,
                    "recent_feu": recent_feu,
                    "avg_real_per_idx_feu": avg_real_per_idx_feu,
                    "recent_3_months_avg_cbm": recent_3_months_avg_cbm,
                    "created_at": timezone.now(),
                },
            )
        except DeliveryIndex.DoesNotExist:
            logger.error("No delivery index data found.")
        except Exception as e:
            logger.error(f"Error updating delivery indices summary: {e}")

    @staticmethod
    def update_shipping_records_summary():
        # 적용 CBM 멀티플 (평균)
        try:
            avg_cbm_inv_per_pl = ShippingRecord.objects.aggregate(
                Avg("cbm_inv_per_pl")
            )["cbm_inv_per_pl__avg"]

            # ShippingRecordsSummary 모델 업데이트
            ShippingRecordsSummary.objects.update_or_create(
                key=1,  # 특정 필드를 기준으로 업데이트
                defaults={
                    "avg_cbm_inv_per_pl": avg_cbm_inv_per_pl,
                    "created_at": timezone.now(),
                },
            )
        except ShippingRecord.DoesNotExist:
            logger.error("No shipping record data found.")
        except Exception as e:
            logger.error(f"Error updating shipping records summary: {e}")

    @staticmethod
    def update_all_summaries():
        # 모든 Summary 테이블 업데이트
        SummaryUpdater.update_delivery_indices_summary()
        SummaryUpdater.update_shipping_records_summary()


class ModelUpdater:
    @staticmethod
    def update_additional_delivery_fee(instance):
        try:
            additional_fee_list = AdditionalDeliveryFee.objects.all()

            for additional_fee in additional_fee_list:
                if (
                    additional_fee.zone_2 is not None
                    and additional_fee.zone_3 is not None
                    and additional_fee.zone_4 is not None
                    and additional_fee.zone_5 is not None
                    and additional_fee.zone_6 is not None
                    and additional_fee.zone_7 is not None
                    and additional_fee.zone_8
                ):

                    weighted_sum = (
                        additional_fee.zone_2 * instance.zone_2_weight
                        + additional_fee.zone_3 * instance.zone_3_weight
                        + additional_fee.zone_4 * instance.zone_4_weight
                        + additional_fee.zone_5 * instance.zone_5_weight
                        + additional_fee.zone_6 * instance.zone_6_weight
                        + additional_fee.zone_7 * instance.zone_7_weight
                        + additional_fee.zone_8 * instance.zone_8_weight
                    )
                    total_weight = (
                        instance.zone_2_weight
                        + instance.zone_3_weight
                        + instance.zone_4_weight
                        + instance.zone_5_weight
                        + instance.zone_6_weight
                        + instance.zone_7_weight
                        + instance.zone_8_weight
                    )
                    if instance.discount == 0:
                        additional_fee.weighted_average = weighted_sum / total_weight
                    else:
                        additional_fee.weighted_average = (
                            weighted_sum / total_weight * (1 - instance.discount)
                        )

                    additional_fee.save()
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


# [Cost Center 2] 해상 운임 계산 모듈
def _freight_for_pallets_1_to_20(
    num_pallets,
    volume,
    total_products,
    recent_teu,
    avg_real_per_idx_teu,
    recent_feu,
    avg_real_per_idx_feu,
    avg_cbm_inv_per_pl,
    recent_3_months_avg_cbm,
):
    """1~20 팔레트 구간 운임 계산 — calculate_freight_charges 내부 helper."""
    if num_pallets <= 7:
        return volume * avg_cbm_inv_per_pl * recent_3_months_avg_cbm * total_products
    elif 8 <= num_pallets <= 10:
        return recent_teu * avg_real_per_idx_teu
    else:  # 11 <= num_pallets <= 20
        return recent_feu * avg_real_per_idx_feu


def calculate_freight_charges(data, summary_data):
    """
    해상 운임 계산

    BUG FIX (2026-05-15): num_pallets > 20 분기에서 재귀 호출 시 data["numPallets"]
    를 갱신하지 않아 무한 재귀가 발생하던 문제를 수정.
    재귀 → loop + helper inline (옵션 A.1) 으로 대체하여 stack overflow risk 영구 차단.
    """
    logger.info(f"Calculating freight charges using data: {data}")

    # 데이터 추출
    num_pallets = int(data.get("numPallets", 0))
    products_per_carton = int(data.get("productsPerCarton", 0))
    cartons_per_pallet = int(data.get("cartonsPerPallet", 0))
    total_products = num_pallets * products_per_carton * cartons_per_pallet

    product_width = float(data.get("productWidth", 0))
    product_height = float(data.get("productHeight", 0))
    product_length = float(data.get("productLength", 0))

    # 부피 계산 (cm³를 m³로 변환)
    volume = (product_width * product_height * product_length) / 1e6

    # 기본값 설정
    recent_teu = summary_data.get("recent_teu", 0)
    avg_real_per_idx_teu = summary_data.get("avg_real_per_idx_teu", 0)
    recent_feu = summary_data.get("recent_feu", 0)
    avg_real_per_idx_feu = summary_data.get("avg_real_per_idx_feu", 0)
    avg_cbm_inv_per_pl = summary_data.get("avg_cbm_inv_per_pl", 0)
    recent_3_months_avg_cbm = summary_data.get("recent_3_months_avg_cbm", 0)

    if num_pallets <= 20:
        # 1~20 팔레트: helper 에 위임
        freight_charges = _freight_for_pallets_1_to_20(
            num_pallets,
            volume,
            total_products,
            recent_teu,
            avg_real_per_idx_teu,
            recent_feu,
            avg_real_per_idx_feu,
            avg_cbm_inv_per_pl,
            recent_3_months_avg_cbm,
        )
    else:
        # 20 팔레트 초과: FEU 단위(20팔레트) 반복 누적 후 remaining 을 helper 로 처리
        # 재귀 호출 제거 — data["numPallets"] 미갱신에 의한 무한 재귀 방지
        total_freight_charges = 0
        while num_pallets > 20:
            total_freight_charges += recent_feu * avg_real_per_idx_feu
            num_pallets -= 20
        # remaining (1~20 팔레트) 운임 — helper 직접 호출, 재귀 없음
        total_freight_charges += _freight_for_pallets_1_to_20(
            num_pallets,
            volume,
            total_products,
            recent_teu,
            avg_real_per_idx_teu,
            recent_feu,
            avg_real_per_idx_feu,
            avg_cbm_inv_per_pl,
            recent_3_months_avg_cbm,
        )
        freight_charges = total_freight_charges

    logger.info(f"Calculated freight charges: {freight_charges}")

    return freight_charges


# [Cost Center 3] 관세 계산 모듈
def calculate_customs_charges(data):
    """
    관세 관련 비용 계산
    """
    try:
        # '관세 관련 비용'의 value 호출
        customs_record = VariableConfigurations.objects.get(name="관세 관련 비용")
        customs_value = float(customs_record.value)  # float 변환

        # 사용자 입력 데이터
        num_pallets = int(data.get("numPallets", 0))
        products_per_carton = int(data.get("productsPerCarton", 0))
        cartons_per_pallet = int(data.get("cartonsPerPallet", 0))
        cost_per_product = float(data.get("costPerProduct", 0))

        # 로깅: 각 변수의 상태 확인
        logger.debug(
            f"num_pallets: {num_pallets}, products_per_carton: {products_per_carton}, cartons_per_pallet: {cartons_per_pallet}, cost_per_product: {cost_per_product}, customs_value: {customs_value}"
        )

        # 관세 관련 비용 계산
        customs_charges = (
            num_pallets
            * products_per_carton
            * cartons_per_pallet
            * cost_per_product
            * customs_value
        )

        logger.info(f"Calculated customs charges: {customs_charges}")
        return customs_charges

    except VariableConfigurations.DoesNotExist:
        logger.error("Customs charges configuration not found.")
        raise ValueError("Customs charges configuration not found.")
    except ValueError as ve:
        logger.error(f"Error converting input data to numbers: {str(ve)}")
        raise ValueError("Invalid input data for customs calculation.")


# [Cost Center 4] 하역 비용 계산 모듈
def calculate_devanning_cost(num_pallets):
    """
    하역 비용 계산
    """
    try:
        # 각 구간에 대한 하역 비용 설정값 가져오기
        devanning_7_value = float(
            VariableConfigurations.objects.get(name="Devanning_7").value
        )  # float 변환
        devanning_10_value = float(
            VariableConfigurations.objects.get(name="Devanning_10").value
        )  # float 변환
        devanning_20_value = float(
            VariableConfigurations.objects.get(name="Devanning_20").value
        )  # float 변환

        # 하역 비용 계산
        if num_pallets <= 7:
            devanning_cost = num_pallets * devanning_7_value
        elif 8 <= num_pallets <= 10:
            devanning_cost = devanning_10_value
        elif 11 <= num_pallets <= 20:
            devanning_cost = devanning_20_value
        else:
            # 20 팔레트 초과
            total_devanning_cost = 0
            while num_pallets > 20:
                total_devanning_cost += devanning_20_value
                num_pallets -= 20
            total_devanning_cost += calculate_devanning_cost(num_pallets)
            devanning_cost = total_devanning_cost

            logger.info(f"Calculated devanning cost: {devanning_cost}")
        return devanning_cost

    except VariableConfigurations.DoesNotExist:
        logger.error("Devanning cost configuration not found.")
        raise ValueError("Devanning cost configuration not found.")


# [Cost Center 5] 신고 수수료 계산 모듈
def calculate_declaration_fee(data):
    """
    신고 수수료 계산
    """
    try:
        # '신고수수료' 설정값 가져오기
        declaration_record = VariableConfigurations.objects.get(name="신고수수료")
        declaration_value = float(declaration_record.value)  # float 변환
        minimum_fee = float(declaration_record.minimum)  # float 변환

        # 사용자 입력 데이터
        num_pallets = int(data.get("numPallets", 0))
        products_per_carton = int(data.get("productsPerCarton", 0))
        cartons_per_pallet = int(data.get("cartonsPerPallet", 0))
        cost_per_product = float(data.get("costPerProduct", 0))

        # 로깅: 각 변수의 상태 확인
        logger.debug(
            f"num_pallets: {num_pallets}, products_per_carton: {products_per_carton}, cartons_per_pallet: {cartons_per_pallet}, cost_per_product: {cost_per_product}, declaration_value: {declaration_value}, minimum_fee: {minimum_fee}"
        )

        # 신고 수수료 계산
        calculated_fee = declaration_value * (
            num_pallets * products_per_carton * cartons_per_pallet * cost_per_product
        )
        declaration_fee = max(calculated_fee, minimum_fee)

        logger.info(f"Calculated declaration fee: {declaration_fee}")
        return declaration_fee

    except VariableConfigurations.DoesNotExist:
        logger.error("Declaration fee configuration not found.")
        raise ValueError("Declaration fee configuration not found.")
    except ValueError as ve:
        logger.error(f"Error converting input data to numbers: {str(ve)}")
        raise ValueError("Invalid input data for declaration fee calculation.")


# [Cost Center 6] 항만료 (Port Charges) 계산 모듈
def calculate_port_charges(data, avg_cbm_inv_per_pl):
    """
    항만료 계산
    """
    try:
        # 사용자 입력 데이터
        product_width = float(data.get("productWidth", 0))  # float 변환
        product_length = float(data.get("productLength", 0))  # float 변환
        product_height = float(data.get("productHeight", 0))  # float 변환
        num_pallets = int(data.get("numPallets", 0))
        products_per_carton = int(data.get("productsPerCarton", 0))
        cartons_per_pallet = int(data.get("cartonsPerPallet", 0))

        # 패키지 부피 계산 (CBM)
        volume = (product_width * product_length * product_height) / 1e6

        # 수출 제품 개수 계산
        total_products = num_pallets * products_per_carton * cartons_per_pallet

        # '항만료' 설정값 가져오기
        port_charge_record = VariableConfigurations.objects.get(name="항만료")
        port_value = float(port_charge_record.value)  # float 변환
        port_minimum = float(port_charge_record.minimum)  # float 변환

        # 항만료 계산
        calculated_port_charge = port_value * (
            volume * total_products * avg_cbm_inv_per_pl
        )

        # 최소값 비교
        port_charges = max(calculated_port_charge, port_minimum)

        logger.info(f"Calculated port charges: {port_charges}")
        return port_charges

    except VariableConfigurations.DoesNotExist:
        logger.error("Port charge configuration not found.")
        raise ValueError("Port charge configuration not found.")
    except ValueError as ve:
        logger.error(f"Error converting input data to numbers: {str(ve)}")
        raise ValueError("Invalid input data for port charges calculation.")


# [Cost Center 7] BOL 값 호출 모듈
def get_bol_value():
    """
    'BOL' 값 호출 모듈
    """
    try:
        bol_value = float(
            VariableConfigurations.objects.get(name="BOL").value
        )  # float 변환
        logger.info(f"Retrieved BOL value: {bol_value}")
        return bol_value
    except VariableConfigurations.DoesNotExist:
        logger.error("BOL configuration not found.")
        raise ValueError("BOL configuration not found.")


# [Cost Center 8] 수취료 비용 계산 모듈
def calculate_receiving_charges(data):
    """
    수취료 계산
    """
    try:
        # 'Receiving' 설정값 가져오기
        receiving_value = float(
            VariableConfigurations.objects.get(name="Receiving").value
        )  # float 변환

        # 사용자 입력 데이터
        num_pallets = int(data.get("numPallets", 0))

        # Reciving 계산
        receiving_charges = num_pallets * receiving_value

        logger.info(f"Calculated receiving charges: {receiving_charges}")
        return receiving_charges

    except VariableConfigurations.DoesNotExist:
        logger.error("Receiving configuration not found.")
        raise ValueError("Receiving configuration not found.")
    except ValueError as ve:
        logger.error(f"Error converting input data to numbers: {str(ve)}")
        raise ValueError("Invalid input data for receiving calculation.")


# [Cost Center 9_O_1] Order Processing Cost 계산 모듈
def calculate_order_processing_cost(data):
    """
    Order Processing Cost 계산
    """
    aov_value = 0

    try:
        # 'AOV' 설정값 가져오기
        aov_admin = float(
            VariableConfigurations.objects.get(name="AOV").value
        )  # float 변환

        # 사용자의 AOV값 입력 여부 확인 및 AOV값 설정 (0 포함 미입력 → admin fallback)
        aov_own = float(data.get("ownAOV", 0) or 0)
        aov_value = aov_own if aov_own > 0 else aov_admin

    except VariableConfigurations.DoesNotExist:
        logger.error("AOV 설정값을 찾을 수 없습니다.")
        raise ValueError("AOV configuration not found.")

    try:
        # 'Order Processing Cost' 설정값 가져오기
        order_processing_cost_value = float(
            VariableConfigurations.objects.get(name="Order processing").value
        )  # float 변환

        # 사용자 입력 데이터
        products_per_aov = aov_value / float(data.get("ownShopPrice", 0))

        # Order Processing Cost 계산
        order_processing_cost = order_processing_cost_value / products_per_aov

        logger.info(f"Calculated order processing cost: {order_processing_cost}")
        return order_processing_cost

    except VariableConfigurations.DoesNotExist:
        logger.error("Order Processing Cost configuration not found.")
        raise ValueError("Order Processing Cost configuration not found.")
    except ValueError as ve:
        logger.error(f"Error converting input data to numbers: {str(ve)}")
        raise ValueError("Invalid input data for order processing cost calculation.")


# [Cost Center 9_O_2] Picking Charges 계산 모듈
def calculate_picking_charges(data):
    """
    Picking Charges 계산
    """
    aov_value = 0

    try:
        # 사용자 설정값 가져오기
        aov_admin = float(
            VariableConfigurations.objects.get(name="AOV").value
        )  # float 변환
        num_pallets = int(data.get("numPallets", 0))
        products_per_carton = int(data.get("productsPerCarton", 0))
        cartons_per_pallet = int(data.get("cartonsPerPallet", 0))

        # 수출 제품 개수 계산
        total_products = num_pallets * products_per_carton * cartons_per_pallet

        # 사용자의 AOV값 입력 여부 확인 및 AOV값 설정 (0 포함 미입력 → admin fallback)
        aov_own = float(data.get("ownAOV", 0) or 0)
        aov_value = aov_own if aov_own > 0 else aov_admin

    except VariableConfigurations.DoesNotExist:
        logger.error("AOV 설정값을 찾을 수 없습니다.")
        raise ValueError("AOV configuration not found.")

    try:
        # 'Picking Charges' 설정값 가져오기
        picking_charges_value = float(
            VariableConfigurations.objects.get(name="Picking").value
        )  # float 변환

        # 사용자 입력 데이터
        product_price = float(data.get("ownShopPrice"))
        products_per_aov = aov_value / product_price
        is_picking_criteria_met = products_per_aov > 3

        # Picking Charges 계산
        picking_charges = (
            (picking_charges_value * (products_per_aov - 3)) / total_products
            if is_picking_criteria_met
            else 0
        )

        logger.info(f"Calculated picking charges: {picking_charges}")
        return picking_charges

    except VariableConfigurations.DoesNotExist:
        logger.error("Picking Charges configuration not found.")
        raise ValueError("Picking Charges configuration not found.")
    except ValueError as ve:
        logger.error(f"Error converting input data to numbers: {str(ve)}")
        raise ValueError("Invalid input data for picking charges calculation.")


# [Cost Center 9_O_3] Outbount Handling Cost 계산 모듈
def calculate_outbound_handling_cost(data):
    """
    Outbound Handling Cost 계산
    """
    aov_value = 0

    try:
        # 'AOV' 설정값 가져오기
        aov_admin = float(
            VariableConfigurations.objects.get(name="AOV").value
        )  # float 변환

        # 사용자의 AOV값 입력 여부 확인 및 AOV값 설정 (0 포함 미입력 → admin fallback)
        aov_own = float(data.get("ownAOV", 0) or 0)
        aov_value = aov_own if aov_own > 0 else aov_admin

    except VariableConfigurations.DoesNotExist:
        logger.error("AOV 설정값을 찾을 수 없습니다.")
        raise ValueError("AOV configuration not found.")

    try:
        # 'Outbound Handling Cost' 설정값 가져오기
        outbound_handling_cost_value = float(
            VariableConfigurations.objects.get(name="Outb. H/C").value
        )  # float 변환

        # 사용자 입력 데이터
        products_per_aov = aov_value / float(data.get("ownShopPrice", 0))

        # Outbound Handling Cost 계산
        outbound_handling_cost = outbound_handling_cost_value / products_per_aov

        logger.info(f"Calculated outbound handling cost: {outbound_handling_cost}")
        return outbound_handling_cost

    except VariableConfigurations.DoesNotExist:
        logger.error("Outbound Handling Cost configuration not found.")
        raise ValueError("Outbound Handling Cost configuration not found.")
    except ValueError as ve:
        logger.error(f"Error converting input data to numbers: {str(ve)}")
        raise ValueError("Invalid input data for outbound handling cost calculation.")


# [Cost Center 10_O] AOV당 무게 배송비 산출 모듈
def calculate_delivery_cost_per_aov(data):
    """
    AOV당 무게 배송비 산출
    """
    try:
        # 'AOV' 설정값 가져오기
        aov_admin = float(
            VariableConfigurations.objects.get(name="AOV").value
        )  # float 변환

        # 사용자의 AOV값 입력 여부 확인 및 AOV값 설정
        aov_own = float(data.get("ownAOV", 0))
        aov_value = aov_own if aov_own > 0 else aov_admin

        # 데이터 검증
        product_weight = float(data.get("productWeight", 0))
        own_shop_price = float(data.get("ownShopPrice", 0))

        if product_weight <= 0 or own_shop_price <= 0:
            raise ValueError("Invalid weight or shop price provided.")

        # 사용자 입력 데이터
        products_per_aov = aov_value / own_shop_price

        # AOV당 무게 계산 로직
        aov_weight = int(
            min(math.ceil(product_weight * aov_value / own_shop_price * 2.205), 151)
        )

        # 'Delivery Cost per AOV' 설정값 계산하기
        delivery_cost_per_aov = float(
            WeightedGroundService.objects.get(lbs=aov_weight).weighted_zone_average
        )  # float 변환

        if aov_weight == 151:
            aov_weight = math.ceil(product_weight * 2.205)
            delivery_cost_own = delivery_cost_per_aov * aov_weight
        else:
            # AOV당 무게 배송비 계산
            delivery_cost_own = delivery_cost_per_aov / products_per_aov

        logger.info(
            f"AOV 올림을 위한 input data: product_weight: {product_weight}, own_shop_price: {own_shop_price}, aov_value: {aov_value}"
        )
        logger.info(f"올림된 AOV 무게: {aov_weight}")
        logger.info(
            f"테이블에서 불러온 AOV 당 Zone 가중 배송비 : {delivery_cost_per_aov}"
        )
        logger.info(f"Calculated delivery cost per AOV: {delivery_cost_own}")
        return delivery_cost_own

    except VariableConfigurations.DoesNotExist:
        logger.error("Delivery Cost per AOV configuration not found.")
        raise ValueError("Delivery Cost per AOV configuration not found.")
    except WeightedGroundService.DoesNotExist:
        logger.error("WeightedGroundService configuration not found for given weight.")
        raise ValueError(
            "WeightedGroundService configuration not found for given weight."
        )
    except ValueError as ve:
        logger.error(f"Error converting input data to numbers: {str(ve)}")
        raise ValueError("Invalid input data for delivery cost per AOV calculation.")


# [Cost Center 9_A] Amazon Referral Fee 계산 모듈
class AmazonReferralFeeCalculator:
    """
    Amazon Referral Fee 계산 모듈

    - 주어진 상품의 카테고리와 가격에 따른 수수료 계산
    - 두 가지 수수료 타입 제공:
        - Simple: 고정 비율 수수료를 가격에 곱하여 계산
        - Complex: 가격 범위에 따라 단계적으로 수수료 누적 계산
    """

    def __init__(self):
        # 데이터베이스에서 수수료 정보 로드
        self.amz_ref_fee_complex = AmazonReferralFeeComplex.objects.all().values()
        self.amz_ref_fee_simple = AmazonReferralFeeSimple.objects.all().values()

    def calculate_amazon_referral_fee(self, data):
        """
        주어진 데이터에 따라 Amazon Referral Fee 계산

        :param data: {'category': <string>, 'price': <float>}
        :return: 계산된 수수료 금액
        """
        category = data.get("amazonCategory", "")
        price = float(data.get("amazonPrice", 0))  # 데이터에서 가격을 가져옴

        amazon_referral_fee = 0
        previous_max_price = 0
        fee_type_found = False

        # 'simple' 테이블 수수료 계산
        simple_fee = next(
            (fee for fee in self.amz_ref_fee_simple if fee["category"] == category),
            None,
        )
        if simple_fee:
            fee_type_found = True
            amazon_referral_fee = max(
                price * simple_fee["referral_fee_rate"] + simple_fee["extra_fee"],
                simple_fee["minimum_fee"],
            )
            return amazon_referral_fee

        # 'complex' 테이블 수수료 계산
        applicable_fees = sorted(
            [fee for fee in self.amz_ref_fee_complex if fee["category"] == category],
            key=lambda x: x["price_range_value"],
        )
        # 각 수수료 구간별 조건 검토 및 수수료 계산
        for fee in applicable_fees:
            if fee["type"] == "simple":
                fee_type_found = True
                # 'simple' 타입: 매칭되는 첫 구간에서 수수료 계산 및 함수 종료
                if (
                    fee["price_range_operator"] == "<="
                    and price <= fee["price_range_value"]
                ) or (
                    fee["price_range_operator"] == ">"
                    and price > fee["price_range_value"]
                ):
                    amazon_referral_fee = (
                        max(price * fee["referral_fee_rate"], fee["minimum_fee"])
                        + fee["extra_fee"]
                    )
                    return amazon_referral_fee  # 계산 완료 후 반환
            elif fee["type"] == "cumulative":
                fee_type_found = True
                # 'cumulative' 타입: 각 구간에 대해 수수료 누적
                if fee["price_range_operator"] == "<=":
                    current_max_price = fee["price_range_value"]
                    if price > current_max_price:
                        fee_to_add = (current_max_price - previous_max_price) * fee[
                            "referral_fee_rate"
                        ]
                        amazon_referral_fee += fee_to_add
                        previous_max_price = current_max_price
                    else:
                        fee_to_add = (price - previous_max_price) * fee[
                            "referral_fee_rate"
                        ]
                        amazon_referral_fee += fee_to_add
                        break
                elif (
                    fee["price_range_operator"] == ">"
                    and price > fee["price_range_value"]
                ):
                    fee_to_add = (price - previous_max_price) * fee["referral_fee_rate"]
                    amazon_referral_fee += fee_to_add
                    break

        # 누적 수수료에 최소 수수료 및 extra_fee 추가
        if applicable_fees and applicable_fees[-1]["type"] == "cumulative":
            amazon_referral_fee = max(
                amazon_referral_fee + applicable_fees[-1]["extra_fee"],
                applicable_fees[-1]["minimum_fee"],
            )

        # 유효한 타입이 한 번도 확인되지 않은 경우
        if not fee_type_found:
            return 0.0

        return amazon_referral_fee


# [Cost Center 10_A] Amazon FBA 물류비 계산 모듈
class AmazonFBALogisticsCostCalculator:
    """
    Amazon FBA 물류비 계산 모듈

    - 주어진 상품의 카테고리와 가격에 따른 물류비 계산
    - Product Tier 산출
    - Product Tier별 Fulfillment Fee, Storage Fee, Inbound Fee 계산
    - 조건에 따른 추가 조정값 계산, 자연어 condition 문자열 파싱 및 연산
    """

    def __init__(self, data):
        # Tier 데이터
        self.tier_data = AmazonProductTier.objects.all().values()

        # Fulfillment, Storage, Inbound 데이터 로드
        self.fulfillment_data = AmazonFulfillmentFee.objects.all().values()
        self.storage_data = CommonStorageFee.objects.all().values()
        self.inbound_data = AmazonInboundFee.objects.all().values()
        self.month_value = float(VariableConfigurations.objects.get(name="month").value)

        # 사용자 입력 데이터를 인치 및 파운드 단위로 변환
        self.category = data.get("category", "")
        self.price = float(data.get("amazonPrice", 0))
        self.product_weight = float(data.get("productWeight", 0))
        self.product_width = float(data.get("productWidth", 0))
        self.product_length = float(data.get("productLength", 0))
        self.product_height = float(data.get("productHeight", 0))

        # 파운드 및 인치로 변환된 제품 정보
        self.weight_lbs = self.product_weight * 2.205
        self.width_in = self.product_width * 0.3937
        self.length_in = self.product_length * 0.3937
        self.height_in = self.product_height * 0.3937

        # 디멘셔널 웨이트와 실제 파운드 무게 비교
        dimensional_weight = (self.width_in * self.length_in * self.height_in) / 139
        self.shipping_weight = max(self.weight_lbs, dimensional_weight)

        # 치수 정렬
        dimensions = sorted([self.width_in, self.length_in, self.height_in])
        self.shortest, self.median, self.longest = dimensions
        self.length_girth = self.longest + 2 * (self.median + self.shortest)

        # Product Tier 계산
        self.product_tier_1, self.product_tier_2 = self.calculate_product_tier()

    def calculate_product_tier(self):
        """
        제품의 물리적 속성을 바탕으로 제품 티어를 계산

        :return: (product_tier_1, product_tier_2) 튜플
        """
        for tier in self.tier_data:
            try:
                # 연산자 함수 초기화
                shipping_wgt_lbs_opr = get_operator_func(tier["shipping_wgt_lbs_opr"])
                longest_inch_opr = get_operator_func(tier["longest_inch_opr"])
                median_inch_opr = get_operator_func(tier["median_inch_opr"])
                shortest_inch_opr = get_operator_func(tier["shortes_inch_opr"])
                lengirth_inch_opr = get_operator_func(tier["lengirth_inch_opr"])

                # Shipping Weight는 모든 카테고리에서 필수
                shipping_weight_valid = shipping_wgt_lbs_opr(
                    self.shipping_weight, tier["shipping_wgt_lbs_val"]
                )

                # Extra-large 카테고리에 대한 OR 로직
                if "ex_large" in tier["product_tier_2"]:
                    if shipping_weight_valid and (
                        longest_inch_opr(self.longest, tier["longest_inch_val"])
                        or median_inch_opr(self.median, tier["median_inch_val"])
                        or shortest_inch_opr(self.shortest, tier["shortes_inch_val"])
                        or (
                            tier["lengirth_inch_val"] is None
                            or lengirth_inch_opr(
                                self.length_girth, tier["lengirth_inch_val"]
                            )
                        )
                    ):
                        return (tier["product_tier_1"], tier["product_tier_2"])

                # 기타 티어에 대한 AND 로직
                else:
                    if (
                        shipping_weight_valid
                        and longest_inch_opr(self.longest, tier["longest_inch_val"])
                        and median_inch_opr(self.median, tier["median_inch_val"])
                        and shortest_inch_opr(self.shortest, tier["shortes_inch_val"])
                        and (
                            tier["lengirth_inch_val"] is None
                            or lengirth_inch_opr(
                                self.length_girth, tier["lengirth_inch_val"]
                            )
                        )
                    ):
                        return (tier["product_tier_1"], tier["product_tier_2"])

            except KeyError as e:
                logger.error(f"티어 데이터에서 키가 누락됨: {e}")

        return (None, "others")

    def _calculate_condition_adjustment(self, condition, shipping_wgt_round_up):
        """
        조건에 따른 추가 조정값 계산

        :param condition: 조건 문자열
        :return: 계산된 조정값
        """
        # 조건이 비어 있으면 0.0을 반환
        if not condition:
            return 0.0

        # 조건 문자열 구문 분석
        try:
            rate_part, _, threshold_str = condition.partition("above")
            rate_value = rate_part.strip().split(" ")[0]  # 예: '/lb', '/2', '/0.5'
            increment = (
                float(rate_value[1:])
                if rate_value[1:].replace(".", "", 1).isdigit()
                else 1.0
            )
            threshold_value = float(
                threshold_str.strip().rstrip("lbs")
            )  # "lb" 또는 "lbs" 제거
        except (ValueError, IndexError):
            return 0.0

        # 초과 무게 계산
        excess_weight = shipping_wgt_round_up - threshold_value
        if excess_weight <= 0:
            return 0.0

        # 초과 무게에 대한 조정값 계산
        adjustment = excess_weight / increment
        return max(0, adjustment)  # 음수 방지를 위한 0 처리

    def calculate_amz_fulfillment_fee(self):
        """
        아마존 Fulfillment Fee 계산

        :return: 계산된 Fulfillment Fee
        """
        # Category 조정
        category = (
            self.category
            if self.category == "Clothing and Accessories"
            else "Non Apparel"
        )
        logger.debug(f"Category for fulfillment fee calculation: {category}")

        # Applicable Fulfillment Fees 검색
        applicable_fees = [
            fee
            for fee in self.fulfillment_data
            if fee["category"] == category
            and fee["product_tier_2"] == self.product_tier_2
        ]
        logger.debug(f"Applicable fulfillment fees: {applicable_fees}")

        # 가장 적합한 Fulfillment Fee 계산
        for fee in applicable_fees:
            logger.debug(f"Checking fee: {fee}")

            # Check the shipping weight and handle rounding based on product tier

            if (
                fee["product_tier_1"] == "standard"
                and fee["product_tier_2"] == "large_std"
            ):
                shipping_wgt_round_up = math.ceil(self.shipping_weight * 4) / 4
                logger.debug(
                    f"check large standard values: {self.shipping_weight}, {shipping_wgt_round_up}"
                )
            else:
                shipping_wgt_round_up = math.ceil(self.shipping_weight)
                logger.debug(
                    f"check common product tier values: {self.shipping_weight}, {shipping_wgt_round_up}"
                )

            # operator를 이용한 조건 확인
            shipping_wgt_lbs_opr = get_operator_func(fee["shipping_wgt_lbs_opr"])
            if shipping_wgt_lbs_opr(shipping_wgt_round_up, fee["shipping_wgt_lbs_val"]):
                extra_fee = fee.get("extra_fee", 0)
                condition_adjustment = self._calculate_condition_adjustment(
                    fee["condition"], shipping_wgt_round_up
                )
                amz_fulfillment_fee = fee["fulfillment_fee"] + (
                    extra_fee * condition_adjustment
                )
                logger.debug(
                    f"Fulfillment fee before price adjustment: {amz_fulfillment_fee}"
                )

                if self.price < 10:
                    amz_fulfillment_fee -= 0.77
                    logger.debug(
                        f"Price is less than 10, applying discount: new fee = {amz_fulfillment_fee}"
                    )

                logger.info(f"Calculated Amazon fulfillment fee: {amz_fulfillment_fee}")
                return amz_fulfillment_fee

        logger.debug("No applicable fulfillment fee found, returning 0")
        logger.info("Calculated Amazon fulfillment fee: 0")
        return 0

    def calculate_amz_storage_fee(self):
        """
        아마존 Storage Fee 계산

        :return: 계산된 Storage Fee
        """
        # 아마존 Storage Fee 계산
        applicable_fees = [
            fee
            for fee in self.storage_data
            if fee["type"] == "amz" and fee["prd_tier"] == self.product_tier_1
        ]
        logger.debug(f"Applicable storage fees: {applicable_fees}")

        if applicable_fees:
            mon_weighted_avg = applicable_fees[0]["mon_weighted_avg"]
            volume_cubic_feet = (self.longest * self.median * self.shortest) / 1728
            amz_storage_fee = mon_weighted_avg * self.month_value * volume_cubic_feet
            logger.debug(
                f"Storage fee calculated: {amz_storage_fee} (volume_cubic_feet: {volume_cubic_feet}, mon_weighted_avg: {mon_weighted_avg})"
            )
            logger.info(f"Calculated Amazon storage fee: {amz_storage_fee}")
            return amz_storage_fee

        logger.debug("No applicable storage fee found, returning 0")
        logger.info("Calculated Amazon storage fee: 0")
        return 0

    def calculate_amazon_inbound_fee(self):
        """
        아마존 Inbound Fee 계산

        :return: 계산된 Inbound Fee
        """
        # product_tier_2 값이 None이 아니고 특정 값이 아니라면 'others'로 설정
        product_tier_2 = (
            self.product_tier_2
            if self.product_tier_2 in ["small_std", "large_std", "large_bulky"]
            else "others"
        )
        logger.debug(f"Product tier for inbound fee calculation: {product_tier_2}")

        # 해당하는 Inbound Fee 계산
        applicable_fees = [
            fee for fee in self.inbound_data if fee["product_tier_2"] == product_tier_2
        ]
        logger.debug(f"Applicable inbound fees: {applicable_fees}")

        # 가장 적합한 Inbound Fee 반환
        for fee in applicable_fees:
            shipping_wgt_lbs_opr = get_operator_func(fee["shipping_wgt_lbs_opr"])
            if shipping_wgt_lbs_opr(self.shipping_weight, fee["shipping_wgt_lbs_val"]):
                amz_inbound_fee = fee["inbound_fee_Med"]
                logger.debug(f"Inbound fee calculated: {amz_inbound_fee}")
                logger.info(f"Calculated Amazon inbound fee: {amz_inbound_fee}")
                return amz_inbound_fee

        logger.debug("No applicable inbound fee found, returning 0")
        logger.info("Calculated Amazon inbound fee: 0")
        return 0

    def calculate_amazon_fba_logistics_fee(self):
        """
        아마존 FBA 총 물류비 계산

        :return: 계산된 FBA 물류비 총합
        """
        try:
            amz_fulfillment_fee = self.calculate_amz_fulfillment_fee() or 0
            amz_storage_fee = self.calculate_amz_storage_fee() or 0
            amz_inbound_fee = self.calculate_amazon_inbound_fee() or 0

            amazon_fba_logistics_fee = (
                amz_fulfillment_fee + amz_storage_fee + amz_inbound_fee
            )
            logger.debug(
                f"Calculated Amazon FBA logistics fee: {amazon_fba_logistics_fee}"
            )
            return amazon_fba_logistics_fee
        except Exception as e:
            logger.error(f"Error in calculate_amazon_fba_logistics_fee: {str(e)}")
        return 0


# [Cost Center 11_A] Amazon FBA 입고비 계산 모듈
class AmazonFBAReceivingCostCalculator:
    """
    Amazon FBA 입고비 계산 모듈
    - 1. 사용자가 입력한 무게(kg)
    - 2. 'common_center_outbound_fee' 테이블의 ('fulfillment_fee' 컬럼 합계) / ('weight_kg' 컬럼 합계) 값
    :return: 2번 값 * 1번 값을 amazon_fba_receiving_cost로 return
    """

    def __init__(self, data):
        """
        초기화 함수

        :param data: 사용자 입력 데이터, {'productWeightKg': <float>}
        """
        self.product_weight_kg = float(
            data.get("productWeight", 0)
        )  # 사용자 입력 무게(kg) 가져오기

    def calculate_amazon_fba_receiving_cost(self):
        """
        Amazon FBA 입고비 계산

        :return: amazon_fba_receiving_cost
        """
        # 'fulfillment_fee' 컬럼 합계 및 'weight_kg' 컬럼 합계 계산
        total_fulfillment_fee = CommonCenterOutboundFee.objects.aggregate(
            Sum("fulfillment_fee")
        )["fulfillment_fee__sum"]
        total_weight_kg = CommonCenterOutboundFee.objects.aggregate(Sum("weight_kg"))[
            "weight_kg__sum"
        ]

        if (
            total_fulfillment_fee is None
            or total_weight_kg is None
            or total_weight_kg == 0
        ):
            # 데이터가 부족하거나 weight_kg 합계가 0인 경우, 0 반환
            return 0

        # Fulfillment Fee / Weight_kg 비율 계산
        fee_per_kg = total_fulfillment_fee / total_weight_kg

        # Amazon FBA Receiving Cost 계산
        amazon_fba_receiving_cost = fee_per_kg * self.product_weight_kg

        return amazon_fba_receiving_cost


# [Cost Center 9_W] Walmart Referral Fee 계산 모듈
class WalmartReferralFeeCalculator:
    """
    Walmart Referral Fee 계산 모듈

    - 주어진 상품의 카테고리와 가격에 따른 수수료 계산
    - 두 가지 수수료 타입 제공:
        - Simple: 고정 비율 수수료를 가격에 곱하여 계산
        - Complex: 가격 범위에 따라 단계적으로 수수료 누적 계산
    """

    def __init__(self):
        # 데이터베이스에서 수수료 정보 로드
        self.wmt_ref_fee_complex = WalmartReferralFeeComplex.objects.all().values()
        self.wmt_ref_fee_simple = WalmartReferralFeeSimple.objects.all().values()

    def calculate_walmart_referral_fee(self, data):
        """
        주어진 데이터에 따라 Amazon Referral Fee 계산

        :param data: {'category': <string>, 'price': <float>}
        :return: 계산된 수수료 금액
        """
        category = data.get("walmartCategory", "")
        price = float(data.get("walmartPrice", 0))  # 데이터에서 가격을 가져옴

        walmart_referral_fee = 0
        previous_max_price = 0
        fee_type_found = False

        # 'simple' 테이블 수수료 계산
        simple_fee = next(
            (fee for fee in self.wmt_ref_fee_simple if fee["category"] == category),
            None,
        )
        if simple_fee:
            fee_type_found = True
            walmart_referral_fee = price * simple_fee["referral_fee_rate"]
            return walmart_referral_fee

        # 'complex' 테이블 수수료 계산
        applicable_fees = sorted(
            [fee for fee in self.wmt_ref_fee_complex if fee["category"] == category],
            key=lambda x: x["price_range_value"],
        )
        # 각 수수료 구간별 조건 검토 및 수수료 계산
        for fee in applicable_fees:
            if fee["type"] == "simple":
                fee_type_found = True
                # 'simple' 타입: 매칭되는 첫 구간에서 수수료 계산 및 함수 종료
                if (
                    fee["price_range_operator"] == "<="
                    and price <= fee["price_range_value"]
                ) or (
                    fee["price_range_operator"] == ">"
                    and price > fee["price_range_value"]
                ):
                    walmart_referral_fee = price * fee["referral_fee_rate"]
                    return walmart_referral_fee  # 계산 완료 후 반환
            elif fee["type"] == "cumulative":
                fee_type_found = True
                # 'cumulative' 타입: 각 구간에 대해 수수료 누적
                if fee["price_range_operator"] == "<=":
                    current_max_price = fee["price_range_value"]
                    if price > current_max_price:
                        fee_to_add = (current_max_price - previous_max_price) * fee[
                            "referral_fee_rate"
                        ]
                        walmart_referral_fee += fee_to_add
                        previous_max_price = current_max_price
                    else:
                        fee_to_add = (price - previous_max_price) * fee[
                            "referral_fee_rate"
                        ]
                        walmart_referral_fee += fee_to_add
                        break
                elif (
                    fee["price_range_operator"] == ">"
                    and price > fee["price_range_value"]
                ):
                    fee_to_add = (price - previous_max_price) * fee["referral_fee_rate"]
                    walmart_referral_fee += fee_to_add
                    break

        # 유효한 타입이 한 번도 확인되지 않은 경우
        if not fee_type_found:
            return 0.0

        return walmart_referral_fee


# [Cost Center 10_W] Walmart FBA 물류비 계산 모듈
class WalmartWFSLogisticsCostCalculator:
    """
    Walmart WFS 물류비 계산 모듈

    - 주어진 상품의 카테고리와 가격에 따른 물류비 계산
    - Product Tier 산출
    - Product Tier별 Fulfillment Fee, Storage Fee 계산
    - 조건에 따른 추가 조정값 계산, 복잡한 fulfillment_fee 구간별 연산, config var. 내의 month값에 따른 storage_fee 계산
    """

    def __init__(self, data):

        # Fulfillment, Storage, Inbound 데이터 로드
        self.fulfillment_data = WalmartFulfillmentFee.objects.all().values()
        self.storage_data = CommonStorageFee.objects.all().values()
        self.month_value = float(VariableConfigurations.objects.get(name="month").value)

        # 사용자 입력 데이터를 인치 및 파운드 단위로 변환
        self.category = data.get("walmartCategory", "")
        self.price = float(data.get("walmartPrice", 0))
        self.product_weight = float(data.get("productWeight", 0))
        self.product_width = float(data.get("productWidth", 0))
        self.product_length = float(data.get("productLength", 0))
        self.product_height = float(data.get("productHeight", 0))

        # 파운드 및 인치로 변환된 제품 정보
        self.weight_lbs = self.product_weight * 2.205
        self.width_in = self.product_width * 0.3937
        self.length_in = self.product_length * 0.3937
        self.height_in = self.product_height * 0.3937

        # 디멘셔널 웨이트와 실제 파운드 무게 비교
        dimensional_weight = (self.width_in * self.length_in * self.height_in) / 139
        if self.weight_lbs < 1:
            self.shipping_weight = self.weight_lbs
        else:
            self.shipping_weight = max(self.weight_lbs, dimensional_weight)

        # 치수 정렬
        dimensions = sorted([self.width_in, self.length_in, self.height_in])
        self.shortest, self.median, self.longest = dimensions
        self.length_girth = self.longest + 2 * (self.median + self.shortest)

        # Product Tier 계산
        self.product_tier = self.calculate_product_tier()

    def calculate_product_tier(self):
        """
        Walmart 제품의 물리적 속성을 바탕으로 제품 티어 계산

        :return: 'big&bulky' 또는 'standard'
        """
        if (
            (150 < self.shipping_weight <= 500)
            or (108 < self.longest <= 120)
            or (self.length_girth > 165)
        ):
            return "big&bulky"
        return "standard"

    def calculate_wmt_fulfillment_fee(self):
        """
        Walmart Fulfillment Fee 계산

        :return: 계산된 Fulfillment Fee
        """
        # shipping_weight_ceil 계산
        shipping_weight_ceil = math.ceil(self.shipping_weight + 0.25)

        # 조건에 맞는 Fulfillment Fee 검색
        applicable_fees = [
            fee
            for fee in self.fulfillment_data
            if fee["product_tier"] == self.product_tier
            and get_operator_func(fee["shipping_wgt_lbs_from_opr"])(
                shipping_weight_ceil, fee["shipping_wgt_lbs_from_val"]
            )
            and get_operator_func(fee["shipping_wgt_lbs_to_opr"])(
                shipping_weight_ceil, fee["shipping_wgt_lbs_to_val"]
            )
        ]

        if not applicable_fees:
            logger.error("No applicable fulfillment fee found.")
            raise ValueError("No applicable fulfillment fee for this product.")

        fee = applicable_fees[0]
        fulfillment_fee = fee["fulfillment_fee"]

        # 추가 수수료 계산
        if fee.get("extra_fee", 0):
            if self.product_tier == "standard":
                fulfillment_fee += (
                    shipping_weight_ceil - (fee["shipping_wgt_lbs_from_val"] + 1)
                ) * fee["extra_fee"]
            elif self.product_tier == "big&bulky":
                fulfillment_fee += (shipping_weight_ceil - 90) * fee["extra_fee"]

        # 'Apparel & Accessories' 카테고리 체크
        if self.product_tier == "standard" and self.category == fee.get("add_category"):
            fulfillment_fee += fee.get("add_val", 0)

        # 가격이 $10 미만일 때 추가 비용
        if self.product_tier == "standard" and self.price < fee.get("add_min_val"):
            fulfillment_fee += fee.get("add_min_fee")

        # 특정 크기 조건에 따른 추가 비용
        if self.product_tier == "standard":
            if (
                fee.get("long_in_fr_val_1")
                < self.longest
                <= fee.get("long_in_to_val_1")
                and self.median > fee.get("med_in_val")
            ) or (
                fee.get("lg_in_fr_val_1")
                < self.length_girth
                <= fee.get("lg_in_to_val_1")
            ):
                fulfillment_fee += fee.get("lg_in_add_1")
            if (
                fee.get("long_in_fr_val_2")
                < self.longest
                <= fee.get("long_in_to_val_2")
            ) or (
                fee.get("lg_in_fr_val_2")
                < self.length_girth
                <= fee.get("lg_in_to_val_2")
            ):
                fulfillment_fee += fee.get("lg_in_add_2")
        wmt_fullfillment_fee = fulfillment_fee

        logger.info(
            f"추가 요금 0.5달러 계상을 위한 standard & Apparel / Acc. 여부: {self.product_tier == 'standard' and fee.get('add_category') == 'Apparel & Accessories'}"
        )
        logger.info(f"Calculated Walmart fulfillment fee: {wmt_fullfillment_fee}")
        return wmt_fullfillment_fee

    def calculate_wmt_storage_fee(self):
        """
        Walmart Storage Fee 계산
        :return: 계산된 Walmart Storage Fee
        """
        # 제품의 부피를 cubic feet로 계산
        volume_cubic_feet = (self.longest * self.median * self.shortest) / 1728

        # 'type'이 'wmt'인 저장 요금 필터링
        applicable_storage_fees = [
            fee for fee in self.storage_data if fee["type"] == "wmt"
        ]

        # 기본 저장 요금 계산
        basic_storage_fee = 0
        for fee in applicable_storage_fees:
            if fee["mon_opr"] == "<=" and fee["mon_val"] == 1:
                basic_storage_fee = fee["mon_weighted_avg"] * volume_cubic_feet

        # 1번 조건: month_value가 1 이하일 때
        if self.month_value <= 1:
            wmt_storage_fee = basic_storage_fee * self.month_value
            logger.info(
                f"Calculated Walmart storage fee (month <= 1): {wmt_storage_fee}"
            )
            return wmt_storage_fee

        # 2번 조건: month_value가 1 초과일 때
        else:
            additional_storage_fee = 0
            for fee in applicable_storage_fees:
                if fee["mon_opr"] == ">" and fee["mon_val"] == 1:
                    additional_storage_fee = (
                        fee["mon_weighted_avg"]
                        * (self.month_value - 1)
                        * volume_cubic_feet
                    )

            wmt_storage_fee = (
                basic_storage_fee + additional_storage_fee
            )  # 기본 요금은 항상 1개월로 가정
            logger.info(
                f"Calculated Walmart storage fee (month > 1): {wmt_storage_fee}"
            )
            return wmt_storage_fee

    def calculate_walmart_wfs_logistics_cost(self):
        """
        월마트 WFS 총 물류비 계산

        :return: 계산된 WFS 물류비 총합
        """
        try:
            fulfillment_fee = self.calculate_wmt_fulfillment_fee()
            storage_fee = self.calculate_wmt_storage_fee()

            walmart_wfs_logistics_fee = fulfillment_fee + storage_fee
            logger.info(
                f"Calculated Walmart WFS total logistics cost: {walmart_wfs_logistics_fee}"
            )
            return walmart_wfs_logistics_fee
        except Exception as e:
            logger.error(f"Error calculating Walmart WFS logistics cost: {str(e)}")
            return 0


# [Cost Center 11_W] Walmart WFS 입고비 계산 모듈
class WalmartWFSReceivingCostCalculator:
    """
    Walmart WFS 입고비 계산 모듈
    - 1. 사용자가 입력한 무게(kg)
    - 2. 'common_center_outbound_fee' 테이블의 ('fulfillment_fee' 컬럼 합계) / ('weight_kg' 컬럼 합계) 값
    :return: 2번 값 * 1번 값을 walmart_wfs_receiving_cost로 return
    """

    def __init__(self, data):
        """
        초기화 함수

        :param data: 사용자 입력 데이터, {'productWeightKg': <float>}
        """
        self.product_weight_kg = float(
            data.get("productWeight", 0)
        )  # 사용자 입력 무게(kg) 가져오기

    def calculate_walmart_wfs_receiving_cost(self):
        """
        Walmart WFS 입고비 계산

        :return: walmart_wfs_receiving_cost
        """
        # 'fulfillment_fee' 컬럼 합계 및 'weight_kg' 컬럼 합계 계산
        total_fulfillment_fee = CommonCenterOutboundFee.objects.aggregate(
            Sum("fulfillment_fee")
        )["fulfillment_fee__sum"]
        total_weight_kg = CommonCenterOutboundFee.objects.aggregate(Sum("weight_kg"))[
            "weight_kg__sum"
        ]

        if (
            total_fulfillment_fee is None
            or total_weight_kg is None
            or total_weight_kg == 0
        ):
            # 데이터가 부족하거나 weight_kg 합계가 0인 경우, 0 반환
            return 0

        # Fulfillment Fee / Weight_kg 비율 계산
        fee_per_kg = total_fulfillment_fee / total_weight_kg

        # Walmart WFS Receiving Cost 계산
        walmart_wfs_receiving_cost = fee_per_kg * self.product_weight_kg

        return walmart_wfs_receiving_cost


# 최종 결과 출력 모듈
def output_reporting(
    data,
    freight_charges,
    customs_charges,
    devanning_cost,
    declaration_fee,
    port_charges,
    bol_value,
    receiving_charges,
    order_processing_cost,
    picking_charges,
    outbound_handling_cost,
    delivery_cost_own,
    amazon_referral_fee,
    amazon_fba_logistics_fee,
    amazon_fba_receiving_cost,
    walmart_referral_fee,
    walmart_wfs_logistics_fee,
    walmart_wfs_receiving_cost,
):

    def calculate_distance(row, longest, median, shortest):
        return math.sqrt(
            (row["longest"] - longest) ** 2
            + (row["median"] - median) ** 2
            + (row["shortest"] - shortest) ** 2
        )

    def calculate_own_box_fee(data):
        """
        calculate company box fee

        :return: calculated box fee
        """
        try:
            # 인치로 변환된 제품 정보
            product_width = float(data.get("productWidth", 0))
            product_length = float(data.get("productLength", 0))
            product_height = float(data.get("productHeight", 0))
            width_in = product_width * 0.3937
            length_in = product_length * 0.3937
            height_in = product_height * 0.3937

            # 치수 정렬
            dimensions = sorted([width_in, length_in, height_in])
            shortest, median, longest = dimensions

            aov_value = 0

            try:
                # 'AOV' 설정값 가져오기
                aov_admin = float(
                    VariableConfigurations.objects.get(name="AOV").value
                )  # float 변환

                # admin_aov=0 degenerate guard — PR #1868 case (e) root fix.
                # services.py:1479 `box_fee = closet_price / products_per_aov` 가
                # outer try-except 외부 → admin_aov=0 시 uncaught ZeroDivisionError →
                # HTTP 500 cascade. 명시적 ValueError 로 변환해 caller 가 400 처리 가능.
                if aov_admin <= 0:
                    raise ValueError("AOV configuration must be positive.")

                # ownAOV None/""/0 → admin fallback (PR #1616 패턴 cascade)
                aov_own = float(data.get("ownAOV", 0) or 0)
                aov_value = aov_own if aov_own > 0 else aov_admin

            except VariableConfigurations.DoesNotExist:
                logger.error("AOV 설정값을 찾을 수 없습니다.")
                raise ValueError("AOV configuration not found.")

            try:
                # 사용자 입력 데이터
                products_per_aov = aov_value / float(data.get("ownShopPrice", 0))

            except ValueError as ve:
                logger.error(f"Error converting input data to numbers: {str(ve)}")
                raise ValueError(
                    "Invalid input data for order processing cost calculation."
                )

            shortest = shortest * products_per_aov

            # re-sort the dimension
            dimensions = sorted([shortest, median, longest])
            shortest, median, longest = dimensions

            box_fee_data = CompanyBoxFee.objects.all().values()

            min_distance = float("inf")
            closet_price = None

            for row in box_fee_data:
                if (
                    float(row["longest"]) < longest
                    or float(row["median"]) < median
                    or float(row["shortest"]) < shortest
                ):
                    continue
                distance = calculate_distance(row, longest, median, shortest)

                if distance < min_distance:
                    min_distance = distance
                    closet_price = row["unit_price"]

            if closet_price is None:
                return 5
        except ValueError:
            # 명시적 invariant (AOV configuration / Invalid input data) — 본 PR #1868
            # case (e) root fix 의 일부. broad `except Exception` 이 ValueError 까지
            # swallow 하면 caller 가 silent UnboundLocalError 만 받아 silent fallback
            # 발생 → re-raise 로 caller view 가 400 처리 가능하게 보장.
            raise
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())
        logger.info(f"unit box price for proper size : {closet_price}")

        box_fee = closet_price / products_per_aov
        logger.debug(f"box fee: {box_fee}")

        return box_fee

    def additional_delivery_fee(data):
        def parse_condition(conditions):
            or_conditions = re.split(r"\s+or\s+", conditions)

            parsed_conditions = []

            for or_cond in or_conditions:
                and_conditions = re.split(r"\s+and\s+", or_cond)
                parsed_and_conditions = []

                for cond in and_conditions:
                    match = re.match(r"([a-zA-Z_0-9]+)\s*([><=]+)\s*([0-9\.]+)", cond)
                    if match:
                        var_name, optr, value = match.groups()
                        parsed_and_conditions.append((var_name, optr, float(value)))
                if parsed_and_conditions:
                    parsed_conditions.append(parsed_and_conditions)

            return parsed_conditions

        def evaluate_condition(variables, condition):
            var_name, optr, value = condition
            logger.debug(f"check condition and vars: {condition}, {variables}")

            if var_name not in variables:
                return False

            var_value = variables[var_name]

            operator_func = get_operator_func(optr)
            return operator_func(var_value, value)

        product_width = float(data.get("productWidth", 0))
        product_length = float(data.get("productLength", 0))
        product_height = float(data.get("productHeight", 0))
        product_weight = float(data.get("productWeight", 0))
        width_in = product_width * 0.3937
        length_in = product_length * 0.3937
        height_in = product_height * 0.3937
        weight_lbs = product_weight * 2.205

        dimensions = sorted([width_in, length_in, height_in])
        shortest, median, longest = dimensions
        length_girth = longest + 2 * (median + shortest)

        zones = AdditionalDeliveryFee.objects.all().values()

        best_zone = None
        highest_weighted_average = 0
        try:
            for zone in zones:
                logger.debug(f"check zone: {zone}")
                conditions = zone["conditions"]
                parsed_conditions = parse_condition(conditions)
                variables = {
                    "longest": longest,
                    "median": median,
                    "shortest": shortest,
                    "weight": weight_lbs,
                    "girth": length_girth,
                }

                condition_met = False

                for and_conditions in parsed_conditions:
                    if all(
                        evaluate_condition(variables, cond) for cond in and_conditions
                    ):
                        condition_met = True
                        break

                if condition_met:
                    if zone["weighted_average"] > highest_weighted_average:
                        best_zone = zone
                        highest_weighted_average = zone["weighted_average"]
            logger.debug(
                f"check additional delivery fee: {best_zone, parsed_conditions, condition_met}"
            )
            if best_zone:
                return best_zone["weighted_average"]
            else:
                return 0
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    """
    계산 결과를 포맷하여 반환
    """
    num_pallets = int(data.get("numPallets", 0))
    products_per_carton = int(data.get("productsPerCarton", 0))
    cartons_per_pallet = int(data.get("cartonsPerPallet", 0))
    product_cost = float(data.get("costPerProduct", 0))

    # 수출 제품 총 개수 계산
    total_products = num_pallets * products_per_carton * cartons_per_pallet

    # 총 수출 및 제반 비용 계산
    total_export_and_associated_costs = (
        freight_charges
        + customs_charges
        + devanning_cost
        + declaration_fee
        + port_charges
        + bol_value
        + receiving_charges
    )

    # 개당 수출 및 제반 비용 계산
    if total_products > 0:
        exp_asc_cost_per_product = total_export_and_associated_costs / total_products
    else:
        exp_asc_cost_per_product = 0  # 제품 수가 0일 경우, 개당 비용을 0으로 설정

    # [자사몰 판매] 풀필먼트 계산
    own_box_fee = calculate_own_box_fee(data)
    additional_delivery_charge = additional_delivery_fee(data)
    delivery_cost_own = delivery_cost_own + additional_delivery_charge
    total_fulfillment_cost = (
        order_processing_cost + picking_charges + outbound_handling_cost + own_box_fee
    )

    # 이익 계산
    own_shop_price = float(data.get("ownShopPrice", 0))
    amazon_price = float(data.get("amazonPrice", 0))
    walmart_price = float(data.get("walmartPrice", 0))

    profit_after_arrival_own = own_shop_price - product_cost - exp_asc_cost_per_product
    profit_after_arrival_amz = amazon_price - product_cost - exp_asc_cost_per_product
    profit_after_arrival_wmt = walmart_price - product_cost - exp_asc_cost_per_product

    # 최종 결과 계산
    own_result = (
        own_shop_price
        - exp_asc_cost_per_product
        - total_fulfillment_cost
        - delivery_cost_own
    )
    amz_result = (
        amazon_price
        - exp_asc_cost_per_product
        - amazon_referral_fee
        - amazon_fba_logistics_fee
        - amazon_fba_receiving_cost
    )
    wmt_result = (
        walmart_price
        - exp_asc_cost_per_product
        - walmart_referral_fee
        - walmart_wfs_logistics_fee
        - walmart_wfs_receiving_cost
    )

    result = {
        "Total Products": total_products,
        "[Price] Own Shop": own_shop_price,
        "[Price] Amazon": amazon_price,
        "[Price] Walmart": walmart_price,
        "[Cost_1] Product Cost": product_cost,
        "[Cost_2] Ocean Freights": freight_charges,
        "[Cost_3] Customs Charges": customs_charges,
        "[Cost_4] Devanning Cost": devanning_cost,
        "[Cost_5] Declaration Fee": declaration_fee,
        "[Cost_6] Port Charges": port_charges,
        "[Cost_7] BOL": bol_value,
        "[Cost_8] Receiving Charges": receiving_charges,
        "Export and Associated Costs Total": total_export_and_associated_costs,
        "Export and Associated Costs Per Product": exp_asc_cost_per_product,
        "[Cost_9_O_1] Order Processing Cost": order_processing_cost,
        "[Cost_9_O_2] Picking Charges": picking_charges,
        "[Cost_9_O_3] Outbound Handling Cost": outbound_handling_cost,
        "Total Fulfillment Cost": total_fulfillment_cost,
        "Total Delivery Cost per AOV": delivery_cost_own,
        "[Cost_9_A] Amazon Referral Fee": amazon_referral_fee,
        "[Cost_10_A] Amazon FBA Logistics Cost": amazon_fba_logistics_fee,
        "[Cost_11_A] Amazon FBA Receiving Cost": amazon_fba_receiving_cost,
        "[Cost_9_W] Walmart Referral Fee": walmart_referral_fee,
        "[Cost_10_W] Walmart WFS Logistics Cost": walmart_wfs_logistics_fee,
        "[Cost_11_W] Walmart WFS Receiving Cost": walmart_wfs_receiving_cost,
        "Profit After Arrival Own": profit_after_arrival_own,
        "Profit After Arrival Amz": profit_after_arrival_amz,
        "Profit After Arrival Wmt": profit_after_arrival_wmt,
        #        'Own Result': own_result,
        #        'Amz Result': amz_result,
        #        'Wmt Result': wmt_result
    }
    logger.info(f"Output report generated: {result}")
    return result
