// 계산 결과 필드 단일 소스(SoT) — 라벨/그룹/키 매핑.
// ResultsView(화면) · 내보내기(복사/CSV) · 이력 상세 3곳이 모두 이 배열을 소비해
// 라벨 drift 를 구조적으로 차단한다. RESULT_FIELDS.camel = computeResults(CalculatorForm)
// 반환 27키와 1:1 (CalculatorResults 타입으로 빌드 시 강제 — 누락/오타 시 tsc 에러).

export interface CalculatorResults {
  estimatedPriceOwn: string;
  estimatedPriceAmz: string;
  estimatedPriceWmt: string;
  productCost: string;
  freightCharges: string;
  customsCharges: string;
  devanningCost: string;
  declarationFee: string;
  portCharges: string;
  bolValue: string;
  receivingCharges: string;
  totalExportAndAssociatedCosts: string;
  exportAndAssociatedCostsPerProduct: string;
  profitAfterArrivalOwn: string;
  profitAfterArrivalAmz: string;
  profitAfterArrivalWmt: string;
  fulfillmentCost: string;
  deliveryCostOwn: string;
  amazonReferralFee: string;
  amazonFbaLogisticsFee: string;
  amazonFbaReceivingCost: string;
  walmartReferralFee: string;
  walmartWfsLogisticsFee: string;
  walmartWfsReceivingCost: string;
  ownResult: string;
  amzResult: string;
  wmtResult: string;
}

export type ResultGroup =
  | "price"
  | "exportUnit"
  | "subtotal"
  | "profit"
  | "channel"
  | "final";

export interface ResultField {
  camel: keyof CalculatorResults; // ← computeResults 키 강제
  snake: string; // CalculationLog DB 필드(이력 상세용)
  label: string;
  group: ResultGroup;
}

export const RESULT_FIELDS: ResultField[] = [
  { camel: "estimatedPriceOwn", snake: "estimated_price_own", label: "자사몰 예상 판매가", group: "price" },
  { camel: "estimatedPriceAmz", snake: "estimated_price_amz", label: "아마존 예상 판매가", group: "price" },
  { camel: "estimatedPriceWmt", snake: "estimated_price_wmt", label: "월마트 예상 판매가", group: "price" },
  { camel: "productCost", snake: "product_cost", label: "[1] 제품 원가", group: "exportUnit" },
  { camel: "freightCharges", snake: "freight_charges", label: "[2] Ocean Freights", group: "exportUnit" },
  { camel: "customsCharges", snake: "customs_charges", label: "[3] Customs", group: "exportUnit" },
  { camel: "devanningCost", snake: "devanning_cost", label: "[4] Devanning", group: "exportUnit" },
  { camel: "declarationFee", snake: "declaration_fee", label: "[5] Declaration", group: "exportUnit" },
  { camel: "portCharges", snake: "port_charges", label: "[6] Port", group: "exportUnit" },
  { camel: "bolValue", snake: "bol_value", label: "[7] BOL", group: "exportUnit" },
  { camel: "receivingCharges", snake: "receiving_charges", label: "[8] Receiving", group: "exportUnit" },
  { camel: "totalExportAndAssociatedCosts", snake: "total_export_and_associated_costs", label: "수출 및 제반비 총계", group: "subtotal" },
  { camel: "exportAndAssociatedCostsPerProduct", snake: "export_and_associated_costs_per_product", label: "개당 수출 및 제반비", group: "subtotal" },
  { camel: "profitAfterArrivalOwn", snake: "profit_after_arrival_own", label: "미국 도착 후 이익 (자사몰)", group: "profit" },
  { camel: "profitAfterArrivalAmz", snake: "profit_after_arrival_amz", label: "미국 도착 후 이익 (아마존)", group: "profit" },
  { camel: "profitAfterArrivalWmt", snake: "profit_after_arrival_wmt", label: "미국 도착 후 이익 (월마트)", group: "profit" },
  { camel: "fulfillmentCost", snake: "fulfillment_cost", label: "풀필먼트 (자사몰)", group: "channel" },
  { camel: "deliveryCostOwn", snake: "delivery_cost_own", label: "배송비 (자사몰)", group: "channel" },
  { camel: "amazonReferralFee", snake: "amazon_referral_fee", label: "아마존 판매수수료", group: "channel" },
  { camel: "amazonFbaLogisticsFee", snake: "amazon_fba_logistics_fee", label: "아마존 FBA 물류", group: "channel" },
  { camel: "amazonFbaReceivingCost", snake: "amazon_fba_receiving_cost", label: "아마존 FBA 입고", group: "channel" },
  { camel: "walmartReferralFee", snake: "walmart_referral_fee", label: "월마트 판매수수료", group: "channel" },
  { camel: "walmartWfsLogisticsFee", snake: "walmart_wfs_logistics_fee", label: "월마트 WFS 물류", group: "channel" },
  { camel: "walmartWfsReceivingCost", snake: "walmart_wfs_receiving_cost", label: "월마트 WFS 입고", group: "channel" },
  { camel: "ownResult", snake: "own_result", label: "최종 이익 (자사몰)", group: "final" },
  { camel: "amzResult", snake: "amz_result", label: "최종 이익 (아마존)", group: "final" },
  { camel: "wmtResult", snake: "wmt_result", label: "최종 이익 (월마트)", group: "final" },
];

export interface InputField {
  snake: string; // CalculationLog DB 입력 필드
  label: string;
}

// 이력 상세 입력 섹션 — CalculationLog 입력 필드(snake) 선별(49필드 raw dump 대신).
export const INPUT_FIELDS: InputField[] = [
  { snake: "product_name", label: "제품명" },
  { snake: "products_per_carton", label: "카톤 당 내입 개수" },
  { snake: "cartons_per_pallet", label: "팔렛트별 적재 카톤 수" },
  { snake: "num_pallets", label: "수출 팔렛트 수" },
  { snake: "product_width", label: "제품 가로 (cm)" },
  { snake: "product_height", label: "제품 세로 (cm)" },
  { snake: "product_length", label: "제품 높이 (cm)" },
  { snake: "product_weight", label: "제품 무게 (kg)" },
  { snake: "cost_per_product", label: "제품당 매출 원가" },
  { snake: "own_shop_price", label: "자사몰 예상 판매가" },
  { snake: "own_aov", label: "기준 객단가" },
  { snake: "amazon_price", label: "아마존 예상 판매가" },
  { snake: "amazon_category", label: "아마존 카테고리" },
  { snake: "walmart_price", label: "월마트 예상 판매가" },
  { snake: "walmart_category", label: "월마트 카테고리" },
];

/** 내보내기(복사/CSV) 행 — 제품명(있으면) + 결과 27. ResultsView 표시와 동일 소스. */
export function buildExportRows(
  results: CalculatorResults,
  productName?: string,
): [string, string][] {
  const rows: [string, string][] = [];
  if (productName) rows.push(["제품명", productName]);
  for (const f of RESULT_FIELDS) rows.push([f.label, String(results[f.camel])]);
  return rows;
}
