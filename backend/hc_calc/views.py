"""hc_calc 계산기 뷰 — calculations/views.py 의 계산 3뷰 슬림 포크 + 계산이력 조회.

calculate_costs_view / get_amazon_categories / get_walmart_categories (95~459).
documentform/inventory 뷰는 범위 밖. 전역 IsAuthenticated(settings) 로 보호.
"""

import logging
import traceback

from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    AmazonReferralFeeComplex,
    AmazonReferralFeeSimple,
    CalculationLog,
    DeliveryIndicesSummary,
    ShippingRecordsSummary,
    WalmartReferralFeeComplex,
    WalmartReferralFeeSimple,
)
from .serializers import CalculationLogSerializer
from .services import (
    AmazonFBALogisticsCostCalculator,
    AmazonFBAReceivingCostCalculator,
    AmazonReferralFeeCalculator,
    WalmartReferralFeeCalculator,
    WalmartWFSLogisticsCostCalculator,
    WalmartWFSReceivingCostCalculator,
    calculate_customs_charges,
    calculate_declaration_fee,
    calculate_delivery_cost_per_aov,
    calculate_devanning_cost,
    calculate_freight_charges,
    calculate_order_processing_cost,
    calculate_outbound_handling_cost,
    calculate_picking_charges,
    calculate_port_charges,
    calculate_receiving_charges,
    get_bol_value,
    output_reporting,
)

logger = logging.getLogger(__name__)


@api_view(["GET"])
def get_amazon_categories(request):
    # 두 모델의 카테고리를 합쳐서 중복을 제거
    categories_simple = AmazonReferralFeeSimple.objects.values_list(
        "category", flat=True
    )
    categories_complex = AmazonReferralFeeComplex.objects.values_list(
        "category", flat=True
    )
    categories = set(categories_simple).union(set(categories_complex))

    return Response(list(categories), status=200)


@api_view(["GET"])
def get_walmart_categories(request):
    categories_simple = WalmartReferralFeeSimple.objects.values_list(
        "category", flat=True
    )
    categories_complex = WalmartReferralFeeComplex.objects.values_list(
        "category", flat=True
    )
    categories = set(categories_simple).union(set(categories_complex))

    return Response(list(categories), status=200)


@api_view(["POST"])
def calculate_costs_view(request):
    """
    고객 인풋 데이터를 받아 해상 운임 및 관세 관련 비용을 계산하여 반환하는 뷰
    """
    logger.info("calculate_costs_view called")

    try:
        data = request.data
        logger.debug(f"Received data: {data}")

        # 데이터 검증
        if not data:
            logger.error("요청 데이터가 비어 있습니다.")
            return Response({"error": "데이터가 제공되지 않았습니다."}, status=400)

        # 입력 데이터 파싱 및 변환
        try:
            num_pallets = int(data.get("numPallets", 0))
            products_per_carton = int(data.get("productsPerCarton", 0))
            cartons_per_pallet = int(data.get("cartonsPerPallet", 0))
            cost_per_product = float(data.get("costPerProduct", 0))
            product_width = float(data.get("productWidth", 0))
            product_height = float(data.get("productHeight", 0))
            product_length = float(data.get("productLength", 0))
            dimensions = {
                "width": product_width,
                "height": product_height,
                "depth": product_length,
            }
            own_aov = float(data.get("ownAOV", 0))
            product_weight = float(data.get("productWeight", 0))
            own_shop_price = float(data.get("ownShopPrice", 0))

            logger.debug(
                f"Parsed input data: num_pallets={num_pallets}, products_per_carton={products_per_carton}, cartons_per_pallet={cartons_per_pallet}, cost_per_product={cost_per_product}, product_width={product_width}, product_height={product_height}, product_length={product_length}, own_aov={own_aov}, product_weight={product_weight}, own_shop_price={own_shop_price}"
            )

            # 입력 데이터 검증
            if product_weight <= 0 or own_shop_price <= 0:
                raise ValueError("Invalid weight or shop price provided.")

        except ValueError as ve:
            logger.error(f"입력 데이터가 유효하지 않습니다: {ve}")
            return Response(
                {
                    "error": f"입력 데이터가 유효하지 않습니다: {ve}. 모든 수치 입력이 올바르게 형식화되었는지 확인하세요."
                },
                status=400,
            )

        # 기본 값으로 초기화
        recent_teu = 0
        avg_real_per_idx_teu = 0
        recent_feu = 0
        avg_real_per_idx_feu = 0
        recent_3_months_avg_cbm = 0
        avg_cbm_inv_per_pl = 0

        # 요약 데이터 가져오기
        try:
            delivery_summary = DeliveryIndicesSummary.objects.get(key=1)
            shipping_summary = ShippingRecordsSummary.objects.get(key=1)
            summary_data = {
                "recent_3_months_avg_cbm": delivery_summary.recent_3_months_avg_cbm,
                "recent_teu": delivery_summary.recent_teu,
                "avg_real_per_idx_teu": delivery_summary.avg_real_per_idx_teu,
                "recent_feu": delivery_summary.recent_feu,
                "avg_real_per_idx_feu": delivery_summary.avg_real_per_idx_feu,
                "avg_cbm_inv_per_pl": shipping_summary.avg_cbm_inv_per_pl,  # 배송 요약 데이터 추가
            }
        except DeliveryIndicesSummary.DoesNotExist:
            logger.error("DeliveryIndicesSummary 데이터를 찾을 수 없습니다.")
            return Response(
                {"error": "배송 지표 요약 데이터를 찾을 수 없습니다."}, status=400
            )
        except ShippingRecordsSummary.DoesNotExist:
            logger.error("ShippingRecordsSummary 데이터를 찾을 수 없습니다.")
            return Response(
                {"error": "배송 기록 요약 데이터를 찾을 수 없습니다."}, status=400
            )

        # 해상 운임 비용 계산
        try:
            freight_charges = calculate_freight_charges(data, summary_data)
            logger.info(f"Calculated freight charges: {freight_charges}")
        except Exception as e:
            logger.error(f"운임 비용 계산 중 오류 발생: {e}")
            return Response({"error": "Error calculating freight charges."}, status=500)

        # 관세 관련 비용 계산
        try:
            customs_charges = calculate_customs_charges(data)
            logger.info(f"Calculated customs charges: {customs_charges}")
        except ValueError as e:
            logger.error(f"Error calculating customs charges: {str(e)}")
            return Response({"error": "Error calculating customs charges."}, status=500)

        # 하역 비용 계산
        try:
            devanning_cost = calculate_devanning_cost(num_pallets)
            logger.info(f"Calculated devanning cost: {devanning_cost}")
        except ValueError as e:
            logger.error(f"Error calculating devanning cost: {str(e)}")
            return Response({"error": "Error calculating devanning cost."}, status=500)

        # 신고 수수료 계산
        try:
            declaration_fee = calculate_declaration_fee(data)
            logger.info(f"Calculated declaration fee: {declaration_fee}")
        except ValueError as e:
            logger.error(f"Error calculating declaration fee: {str(e)}")
            return Response({"error": "Error calculating declaration fee."}, status=500)

        # 항만료 계산
        try:
            port_charges = calculate_port_charges(
                data, summary_data["avg_cbm_inv_per_pl"]
            )
            logger.info(f"Calculated port charges: {port_charges}")
        except ValueError as e:
            logger.error(f"Error calculating port charges: {str(e)}")
            return Response({"error": "Error calculating port charges."}, status=500)

        # 'BOL' 값 호출
        try:
            bol_value = get_bol_value()
            logger.info(f"Calculated BOL value: {bol_value}")
        except ValueError as e:
            logger.error(f"Error retrieving BOL value: {str(e)}")
            return Response({"error": "Error retrieving BOL value."}, status=500)

        # 수취료 계산
        try:
            receiving_charges = calculate_receiving_charges(data)
            logger.info(f"Calculated receiving charges: {receiving_charges}")
        except ValueError as e:
            logger.error(f"Error calculating receiving charges: {str(e)}")
            return Response(
                {"error": "Error calculating receiving charges."}, status=500
            )

        # 중간 정산 로직 반영 (total_export_and_associated_costs 및 export_and_associated_costs_per_product 계산)
        total_export_and_associated_costs = sum(
            [
                freight_charges,
                customs_charges,
                devanning_cost,
                declaration_fee,
                port_charges,
                bol_value,
                receiving_charges,
            ]
        )
        total_products = num_pallets * products_per_carton * cartons_per_pallet
        exportAndAssociatedCostsPerProduct = (
            total_export_and_associated_costs / total_products if total_products else 0
        )

        # [자사몰] 풀필먼트 중간 정산 로직 반영 (order_processing_cost, picking_charges, outbound_handling_cost 합산)
        try:
            # own_aov 값을 float로 변환하고 사용
            own_aov = float(data.get("ownAOV", 0))  # 자사몰 평균 객단가
            # 전체 제품 수
            total_products = num_pallets * products_per_carton * cartons_per_pallet

            order_processing_cost = calculate_order_processing_cost(data)
            picking_charges = calculate_picking_charges(data)
            outbound_handling_cost = calculate_outbound_handling_cost(data)

            total_fulfillment_costs = sum(
                [order_processing_cost, picking_charges, outbound_handling_cost]
            )
            logger.info(
                f"Calculated total fulfillment costs: {total_fulfillment_costs}"
            )
        except Exception as e:
            logger.error(f"Error calculating fulfillment costs: {str(e)}")
            return Response(
                {"error": "Error calculating fulfillment costs."}, status=500
            )

        # [자사몰] 배송비 중간 정산 로직 반영 (delivery_cost_own)
        try:
            delivery_cost_own = calculate_delivery_cost_per_aov(data)
            logger.info(f"Calculated delivery cost per AOV: {delivery_cost_own}")
        except Exception as e:
            logger.error(f"Error calculating delivery cost per AOV: {str(e)}")
            return Response(
                {"error": "Error calculating delivery cost per AOV."}, status=500
            )

        # Amazon Referral Fee 계산
        try:
            amazon_referral_fee_calculator = AmazonReferralFeeCalculator()
            amazon_referral_fee = (
                amazon_referral_fee_calculator.calculate_amazon_referral_fee(data)
            )
            logger.info(f"Calculated Amazon referral fee: {amazon_referral_fee}")
        except Exception as e:
            logger.error(f"Error calculating Amazon referral fee: {str(e)}")
            return Response(
                {"error": "Error calculating Amazon referral fee."}, status=500
            )

        # Amazon FBA Logistics Cost 계산
        try:
            amazon_fba_logistics_calculator = AmazonFBALogisticsCostCalculator(data)
            amazon_fba_logistics_cost = (
                amazon_fba_logistics_calculator.calculate_amazon_fba_logistics_fee()
            )
            logger.info(
                f"Calculated Amazon FBA logistics fee: {amazon_fba_logistics_cost}"
            )
        except Exception as e:
            logger.error(f"Error calculating Amazon FBA logistics fee: {str(e)}")
            return Response(
                {"error": "Error calculating Amazon FBA logistics fee."}, status=500
            )

        # Amazon FBA Receiving Cost 계산
        try:
            amazon_fba_receiving_calculator = AmazonFBAReceivingCostCalculator(data)
            amazon_fba_receiving_cost = (
                amazon_fba_receiving_calculator.calculate_amazon_fba_receiving_cost()
            )
            logger.info(
                f"Calculated Amazon FBA receiving cost: {amazon_fba_receiving_cost}"
            )
        except Exception as e:
            logger.error(f"Error calculating Amazon FBA receiving cost: {str(e)}")
            return Response(
                {"error": "Error calculating Amazon FBA receiving cost."}, status=500
            )

        # Walmart Referral Fee 계산
        try:
            walmart_referral_fee_calculator = WalmartReferralFeeCalculator()
            walmart_referral_fee = (
                walmart_referral_fee_calculator.calculate_walmart_referral_fee(data)
            )
            logger.info(f"Calculated Walmart referral fee: {walmart_referral_fee}")
        except Exception as e:
            logger.error(f"Error calculating Walmart referral fee: {str(e)}")
            return Response(
                {"error": "Error calculating Walmart referral fee."}, status=500
            )

        # Walmart WFS Logistics Cost 계산
        try:
            walmart_wfs_logistics_calculator = WalmartWFSLogisticsCostCalculator(data)
            walmart_wfs_logistics_cost = (
                walmart_wfs_logistics_calculator.calculate_walmart_wfs_logistics_cost()
            )
            logger.info(
                f"Calculated Walmart WFS logistics fee: {walmart_wfs_logistics_cost}"
            )
        except Exception as e:
            logger.error(f"Error calculating Walmart WFS logistics fee: {str(e)}")
            return Response(
                {"error": "Error calculating Walmart WFS logistics fee."}, status=500
            )

        # Walmart WFS Receiving Cost 계산
        try:
            walmart_wfs_receiving_calculator = WalmartWFSReceivingCostCalculator(data)
            walmart_wfs_receiving_cost = (
                walmart_wfs_receiving_calculator.calculate_walmart_wfs_receiving_cost()
            )
            logger.info(
                f"Calculated Walmart WFS receiving cost: {walmart_wfs_receiving_cost}"
            )
        except Exception as e:
            logger.error(f"Error calculating Walmart WFS receiving cost: {str(e)}")
            return Response(
                {"error": "Error calculating Walmart WFS receiving cost."}, status=500
            )

        # 결과 반환
        try:
            result = output_reporting(
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
                amazon_fba_logistics_cost,
                amazon_fba_receiving_cost,
                walmart_referral_fee,
                walmart_wfs_logistics_cost,
                walmart_wfs_receiving_cost,
            )

            # 세부 항목 분리
            amazon_fulfillment_fee = (
                amazon_fba_logistics_calculator.calculate_amz_fulfillment_fee()
            )
            amazon_storage_fee = (
                amazon_fba_logistics_calculator.calculate_amz_storage_fee()
            )
            amazon_inbound_fee = (
                amazon_fba_logistics_calculator.calculate_amazon_inbound_fee()
            )

            walmart_fulfillment_fee = (
                walmart_wfs_logistics_calculator.calculate_wmt_fulfillment_fee()
            )
            walmart_storage_fee = (
                walmart_wfs_logistics_calculator.calculate_wmt_storage_fee()
            )

            # CalculationLog에 결과 저장
            CalculationLog.objects.create(
                num_pallets=data["numPallets"],
                products_per_carton=data["productsPerCarton"],
                cartons_per_pallet=data["cartonsPerPallet"],
                product_width=data["productWidth"],
                product_height=data["productHeight"],
                product_length=data["productLength"],
                product_weight=data["productWeight"],
                cost_per_product=data["costPerProduct"],
                amazon_price=data["amazonPrice"],
                amazon_category=data["amazonCategory"],
                walmart_price=data["walmartPrice"],
                walmart_category=data["walmartCategory"],
                own_shop_price=data["ownShopPrice"],
                own_aov=data["ownAOV"],
                # 제품 식별(선택). str 강제 + 길이 방어(DB CharField(200)/TextField 보호).
                product_name=str(data.get("productName", ""))[:200],
                memo=str(data.get("memo", ""))[:2000],
                total_products=result["Total Products"],
                estimated_price_own=result["[Price] Own Shop"],
                estimated_price_amz=result["[Price] Amazon"],
                estimated_price_wmt=result["[Price] Walmart"],
                product_cost=result["[Cost_1] Product Cost"],
                freight_charges=result["[Cost_2] Ocean Freights"]
                / result["Total Products"],
                customs_charges=result["[Cost_3] Customs Charges"]
                / result["Total Products"],
                devanning_cost=result["[Cost_4] Devanning Cost"]
                / result["Total Products"],
                declaration_fee=result["[Cost_5] Declaration Fee"]
                / result["Total Products"],
                port_charges=result["[Cost_6] Port Charges"] / result["Total Products"],
                bol_value=result["[Cost_7] BOL"] / result["Total Products"],
                receiving_charges=result["[Cost_8] Receiving Charges"],
                total_export_and_associated_costs=result[
                    "Export and Associated Costs Total"
                ],
                export_and_associated_costs_per_product=result[
                    "Export and Associated Costs Per Product"
                ],
                profit_after_arrival_own=result.get("Profit After Arrival Own", 0),
                profit_after_arrival_amz=result.get("Profit After Arrival Amz", 0),
                profit_after_arrival_wmt=result.get("Profit After Arrival Wmt", 0),
                fulfillment_cost=result.get("Total Fulfillment Cost", 0),
                delivery_cost_own=result.get("Total Delivery Cost per AOV", 0),
                amazon_referral_fee=result.get("[Cost_9_A] Amazon Referral Fee", 0),
                amazon_fulfillment_fee=amazon_fulfillment_fee,
                amazon_storage_fee=amazon_storage_fee,
                amazon_inbound_fee=amazon_inbound_fee,
                amazon_fba_logistics_fee=result.get(
                    "[Cost_10_A] Amazon FBA Logistics Cost", 0
                ),
                amazon_fba_receiving_cost=result.get(
                    "[Cost_11_A] Amazon FBA Receiving Cost", 0
                ),
                walmart_referral_fee=result.get("[Cost_9_W] Walmart Referral Fee", 0),
                walmart_fulfillment_fee=walmart_fulfillment_fee,
                walmart_storage_fee=walmart_storage_fee,
                walmart_wfs_logistics_fee=result.get(
                    "[Cost_10_W] Walmart WFS Logistics Cost", 0
                ),
                walmart_wfs_receiving_cost=result.get(
                    "[Cost_11_W] Walmart WFS Receiving Cost", 0
                ),
                own_result=result.get("Profit After Arrival Own", 0)
                - result.get("Total Fulfillment Cost", 0)
                - result.get("Total Delivery Cost per AOV", 0),
                amz_result=result.get("Profit After Arrival Amz", 0)
                - result.get("[Cost_9_A] Amazon Referral Fee", 0)
                - result.get("[Cost_10_A] Amazon FBA Logistics Cost", 0)
                - result.get("[Cost_11_A] Amazon FBA Receiving Cost", 0),
                wmt_result=result.get("Profit After Arrival Wmt", 0)
                - result.get("[Cost_9_W] Walmart Referral Fee", 0)
                - result.get("[Cost_10_W] Walmart WFS Logistics Cost", 0)
                - result.get("[Cost_11_W] Walmart WFS Receiving Cost", 0),
            )
            logger.info(f"결과 보고서 생성됨: {result}")
            return Response(result, status=200)
        except Exception as e:
            logger.error(f"Error generating output report: {str(e)}")
            return Response({"error": "Error generating output report."}, status=500)

    except Exception as e:
        logger.error(f"calculate_costs_view 처리 중 오류: {str(e)}")
        logger.error(f"stacktrace: {traceback.format_exc()}")
        return Response({"error": "비용 계산 중 오류가 발생했습니다."}, status=500)


# ==== documentsform apis ====


class CalculationLogListView(generics.ListAPIView):
    """계산 이력 조회 — 단일계정이라 전체 로그 최신순.

    권한 필터 불필요(HC 1계정), 전역 IsAuthenticated 로 보호. PAGE_SIZE 페이지네이션.
    """

    serializer_class = CalculationLogSerializer
    queryset = CalculationLog.objects.all().order_by("-created_at")


class CalculationLogDetailView(generics.RetrieveAPIView):
    """계산 이력 상세 — 단일 로그 전체(입력+결과, fields='__all__').

    단일계정이라 소유자 필터 불필요, 전역 IsAuthenticated 로 보호.
    RetrieveAPIView 라 응답은 평면 객체(목록의 페이지네이션 envelope 와 다름).
    """

    serializer_class = CalculationLogSerializer
    queryset = CalculationLog.objects.all()
