"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import {
  Calculator as CalculatorIcon,
  Copy,
  Download,
  Loader2,
} from "lucide-react";

import { BASE_PATH } from "@/lib/constants";
import { getCSRFToken } from "@/lib/csrf";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  RESULT_FIELDS,
  buildExportRows,
  type CalculatorResults,
  type ResultGroup,
} from "@/lib/result-labels";

// API contract: Django POST /api/calculate_costs/ 응답 shape.
// key 는 backend 한글/공백/특수문자 포함 — string index signature.
interface CalculatorAPIResponse {
  [key: string]: number;
}

const apiUrl = BASE_PATH;

// zod schema — coerce string → number, optional category.
const schema = z.object({
  numPallets: z.coerce.number().min(0, "0 이상"),
  productsPerCarton: z.coerce.number().min(0, "0 이상"),
  cartonsPerPallet: z.coerce.number().min(0, "0 이상"),
  productWidth: z.coerce.number().min(0, "0 이상"),
  productHeight: z.coerce.number().min(0, "0 이상"),
  productLength: z.coerce.number().min(0, "0 이상"),
  productWeight: z.coerce.number().positive("상품 무게는 0 보다 커야 합니다"),
  costPerProduct: z.coerce.number().min(0, "0 이상"),
  amazonPrice: z.coerce.number().min(0, "0 이상"),
  amazonCategory: z.string(),
  walmartPrice: z.coerce.number().min(0, "0 이상"),
  walmartCategory: z.string(),
  ownShopPrice: z.coerce
    .number()
    .positive(
      "자사몰 가격은 0 보다 커야 합니다. 자사몰 미판매 시 임의 양수 입력",
    ),
  ownAOV: z.coerce.number().min(0, "0 이상"),
  productName: z.string().max(200, "200자 이내").optional().default(""),
  memo: z.string().max(2000, "2000자 이내").optional().default(""),
});

// zod `z.coerce.number()` 는 input=unknown / output=number.
// useForm 의 3-generic 으로 input/output 분리 — defaultValues 는 input (unknown 호환),
// onSubmit data 는 output (number 정합).
type FormInput = z.input<typeof schema>;
type FormValues = z.output<typeof schema>;

const defaultValues: FormInput = {
  numPallets: 0,
  productsPerCarton: 0,
  cartonsPerPallet: 0,
  productWidth: 0,
  productHeight: 0,
  productLength: 0,
  productWeight: 0,
  costPerProduct: 0,
  amazonPrice: 0,
  amazonCategory: "",
  walmartPrice: 0,
  walmartCategory: "",
  ownShopPrice: 0,
  ownAOV: 0,
  productName: "",
  memo: "",
};

function fmt(n: number, digits = 2): string {
  if (!Number.isFinite(n)) return "-";
  return n.toFixed(digits);
}

function computeResults(data: CalculatorAPIResponse): CalculatorResults {
  const totalProducts = data["Total Products"] || 0;
  const priceOwn = data["[Price] Own Shop"] || 0;
  const priceAmz = data["[Price] Amazon"] || 0;
  const priceWmt = data["[Price] Walmart"] || 0;
  const productCost = data["[Cost_1] Product Cost"] || 0;
  const exportPerProduct = data["Export and Associated Costs Per Product"] || 0;
  const ocean = data["[Cost_2] Ocean Freights"] || 0;
  const customs = data["[Cost_3] Customs Charges"] || 0;
  const devanning = data["[Cost_4] Devanning Cost"] || 0;
  const declaration = data["[Cost_5] Declaration Fee"] || 0;
  const port = data["[Cost_6] Port Charges"] || 0;
  const bol = data["[Cost_7] BOL"] || 0;
  const receiving = data["[Cost_8] Receiving Charges"] || 0;
  const fulfill = data["Total Fulfillment Cost"] || 0;
  const delivery = data["Total Delivery Cost per AOV"] || 0;
  const amzReferral = data["[Cost_9_A] Amazon Referral Fee"] || 0;
  const amzFbaLog = data["[Cost_10_A] Amazon FBA Logistics Cost"] || 0;
  const amzFbaRecv = data["[Cost_11_A] Amazon FBA Receiving Cost"] || 0;
  const wmtReferral = data["[Cost_9_W] Walmart Referral Fee"] || 0;
  const wmtWfsLog = data["[Cost_10_W] Walmart WFS Logistics Cost"] || 0;
  const wmtWfsRecv = data["[Cost_11_W] Walmart WFS Receiving Cost"] || 0;

  const safeDiv = (a: number, b: number) => (b ? a / b : 0);

  return {
    estimatedPriceOwn: fmt(priceOwn, 2),
    estimatedPriceAmz: fmt(priceAmz, 2),
    estimatedPriceWmt: fmt(priceWmt, 2),
    productCost: fmt(productCost, 4),
    freightCharges: fmt(safeDiv(ocean, totalProducts), 4),
    customsCharges: fmt(safeDiv(customs, totalProducts), 4),
    devanningCost: fmt(safeDiv(devanning, totalProducts), 4),
    declarationFee: fmt(safeDiv(declaration, totalProducts), 4),
    portCharges: fmt(safeDiv(port, totalProducts), 4),
    bolValue: fmt(safeDiv(bol, totalProducts), 6),
    receivingCharges: fmt(safeDiv(receiving, totalProducts), 4),
    totalExportAndAssociatedCosts: fmt(
      data["Export and Associated Costs Total"] || 0,
      2,
    ),
    exportAndAssociatedCostsPerProduct: fmt(exportPerProduct, 4),
    profitAfterArrivalOwn: fmt(priceOwn - productCost - exportPerProduct, 3),
    profitAfterArrivalAmz: fmt(priceAmz - productCost - exportPerProduct, 3),
    profitAfterArrivalWmt: fmt(priceWmt - productCost - exportPerProduct, 3),
    fulfillmentCost: fmt(fulfill, 4),
    deliveryCostOwn: fmt(delivery, 4),
    amazonReferralFee: fmt(amzReferral, 4),
    amazonFbaLogisticsFee: fmt(amzFbaLog, 4),
    amazonFbaReceivingCost: fmt(amzFbaRecv, 4),
    walmartReferralFee: fmt(wmtReferral, 4),
    walmartWfsLogisticsFee: fmt(wmtWfsLog, 4),
    walmartWfsReceivingCost: fmt(wmtWfsRecv, 4),
    ownResult: fmt(
      priceOwn - productCost - exportPerProduct - fulfill - delivery,
      3,
    ),
    amzResult: fmt(
      priceAmz -
        productCost -
        exportPerProduct -
        amzReferral -
        amzFbaLog -
        amzFbaRecv,
      3,
    ),
    wmtResult: fmt(
      priceWmt -
        productCost -
        exportPerProduct -
        wmtReferral -
        wmtWfsLog -
        wmtWfsRecv,
      3,
    ),
  };
}

function CalculatorForm() {
  const [amazonCategories, setAmazonCategories] = useState<string[]>([]);
  const [walmartCategories, setWalmartCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<CalculatorResults | null>(null);
  const [resultProductName, setResultProductName] = useState("");

  const form = useForm<FormInput, undefined, FormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  });

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const [aRes, wRes] = await Promise.all([
          fetch(`${apiUrl}/api/amazon-categories/`),
          fetch(`${apiUrl}/api/walmart-categories/`),
        ]);
        const aData: unknown = await aRes.json();
        const wData: unknown = await wRes.json();
        const aList = Array.isArray(aData)
          ? aData.filter((s): s is string => typeof s === "string").sort()
          : [];
        const wList = Array.isArray(wData)
          ? wData.filter((s): s is string => typeof s === "string").sort()
          : [];
        setAmazonCategories(aList);
        setWalmartCategories(wList);
      } catch (err) {
        console.error("category fetch fail:", err);
        toast.error("카테고리 목록을 불러오지 못했습니다.");
      }
    };
    fetchCategories();
  }, []);

  const onSubmit = async (values: FormValues) => {
    setLoading(true);
    const toastId = toast.loading("계산 중…");
    try {
      const res = await fetch(`${apiUrl}/api/calculate_costs/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken() ?? "",
        },
        body: JSON.stringify(values),
      });
      if (!res.ok) throw new Error(`서버 응답 오류: ${res.status}`);
      const data = (await res.json()) as CalculatorAPIResponse;
      setResults(computeResults(data));
      setResultProductName(values.productName ?? "");
      toast.success("계산이 완료되었습니다.", { id: toastId });
    } catch (err) {
      console.error("calculate fail:", err);
      toast.error(
        err instanceof Error ? err.message : "계산 중 오류가 발생했습니다.",
        { id: toastId },
      );
    } finally {
      setLoading(false);
    }
  };

  const renderNumberField = (
    name: keyof FormInput,
    label: string,
    step = "any",
    required = false,
  ) => (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>
            {label}
            {required && (
              <span className="ml-0.5 text-destructive" aria-hidden="true">
                *
              </span>
            )}
          </FormLabel>
          <FormControl>
            <Input
              type="number"
              step={step}
              name={field.name}
              ref={field.ref}
              onBlur={field.onBlur}
              value={
                field.value === 0 || field.value === undefined
                  ? ""
                  : String(field.value)
              }
              onChange={(e) => field.onChange(e.target.value)}
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  );

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <header className="flex items-center gap-3">
        <CalculatorIcon className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            수출 계산기
          </h1>
          <p className="text-sm text-muted-foreground">
            제품 규격 · 원가 · 채널별 판매가 입력으로 미국 도착 후 손익을
            계산합니다.
          </p>
        </div>
      </header>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">제품 정보 (선택)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="productName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>제품명</FormLabel>
                    <FormControl>
                      <Input placeholder="예: 베이비 욕조 A형" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="memo"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>메모</FormLabel>
                    <FormControl>
                      <textarea
                        {...field}
                        rows={2}
                        placeholder="견적 메모(거래처 · 조건 등)"
                        className="border-input placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 flex w-full rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px]"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">수출 규격 (공통)</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {renderNumberField("productsPerCarton", "카톤 당 내입 개수")}
              {renderNumberField("cartonsPerPallet", "팔렛트별 적재 카톤 수")}
              {renderNumberField("numPallets", "수출 팔렛트 수")}
              {renderNumberField("productWidth", "제품 가로 (cm)")}
              {renderNumberField("productHeight", "제품 세로 (cm)")}
              {renderNumberField("productLength", "제품 높이 (cm)")}
              {renderNumberField(
                "productWeight",
                "제품 무게 (kg)",
                "any",
                true,
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">셀러 원가 정보</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              {renderNumberField("costPerProduct", "제품당 매출 원가")}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                미국 판매 채널별 예상 정보
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-6 lg:grid-cols-3">
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground">
                  자사몰
                </h3>
                {renderNumberField("ownShopPrice", "예상 판매가", "any", true)}
                {renderNumberField("ownAOV", "기준 객단가")}
              </div>
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground">
                  아마존
                </h3>
                {renderNumberField("amazonPrice", "예상 판매가")}
                <FormField
                  control={form.control}
                  name="amazonCategory"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>예상 판매 카테고리</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="카테고리 선택" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {amazonCategories.map((c) => (
                            <SelectItem key={c} value={c}>
                              {c}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground">
                  월마트
                </h3>
                {renderNumberField("walmartPrice", "예상 판매가")}
                <FormField
                  control={form.control}
                  name="walmartCategory"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>예상 판매 카테고리</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="카테고리 선택" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {walmartCategories.map((c) => (
                            <SelectItem key={c} value={c}>
                              {c}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button
              type="submit"
              disabled={loading}
              size="lg"
              className="gap-2"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <CalculatorIcon className="h-4 w-4" />
              )}
              {loading ? "계산 중…" : "계산하기"}
            </Button>
          </div>
        </form>
      </Form>

      {results && (
        <ResultsView results={results} productName={resultProductName} />
      )}
    </div>
  );
}

function ResultsView({
  results,
  productName,
}: {
  results: CalculatorResults;
  productName?: string;
}) {
  // 라벨/그룹/키 = RESULT_FIELDS 단일 소스. 화면·복사·CSV·이력상세가 동일 소스를 본다.
  const byGroup = (g: ResultGroup) =>
    RESULT_FIELDS.filter((f) => f.group === g).map((f) => ({
      label: f.label,
      value: results[f.camel],
    }));

  const onCopy = () => {
    const text = buildExportRows(results, productName)
      .map(([l, v]) => `${l}\t${v}`)
      .join("\n");
    navigator.clipboard
      .writeText(text)
      .then(() => toast.success("계산 결과를 복사했습니다."))
      .catch(() => toast.error("복사에 실패했습니다."));
  };

  const onDownloadCsv = () => {
    // UTF-8 BOM(﻿) — Excel 한글 깨짐 방지.
    const csv =
      "﻿" +
      buildExportRows(results, productName)
        .map(
          ([l, v]) =>
            `"${l.replace(/"/g, '""')}","${String(v).replace(/"/g, '""')}"`,
        )
        .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `수출계산결과${productName ? `_${productName}` : ""}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">계산 결과</CardTitle>
        <CardAction className="flex gap-2">
          <Button type="button" variant="outline" size="sm" onClick={onCopy}>
            <Copy className="size-4" />
            복사
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onDownloadCsv}
          >
            <Download className="size-4" />
            CSV
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent className="space-y-6">
        <KPIRow variant="positive" rows={byGroup("price")} />
        <Separator />
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-foreground">
            수출 및 제반비 (개당)
          </h4>
          <DetailGrid items={byGroup("exportUnit")} />
          <div className="grid gap-2 pt-2 text-sm sm:grid-cols-2">
            {byGroup("subtotal").map((s) => (
              <Subtotal key={s.label} label={s.label} value={s.value} />
            ))}
          </div>
        </div>
        <Separator />
        <KPIRow variant="positive" rows={byGroup("profit")} />
        <Separator />
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-foreground">
            채널별 부가 비용
          </h4>
          <DetailGrid items={byGroup("channel")} />
        </div>
        <Separator />
        <KPIRow variant="result" rows={byGroup("final")} />
      </CardContent>
    </Card>
  );
}

function KPIRow({
  rows,
  variant,
}: {
  rows: { label: string; value: number | string }[];
  variant: "positive" | "result";
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {rows.map((r) => {
        const num = Number(r.value);
        const isNeg = Number.isFinite(num) && num < 0;
        const colorClass =
          variant === "result"
            ? isNeg
              ? "text-destructive"
              : "text-emerald-600 dark:text-emerald-400"
            : "text-emerald-700 dark:text-emerald-300";
        return (
          <div
            key={r.label}
            className="rounded-md border bg-muted/30 px-4 py-3"
          >
            <p className="text-xs text-muted-foreground">{r.label}</p>
            <p className={`mt-1 text-lg font-semibold ${colorClass}`}>
              {r.value}
            </p>
          </div>
        );
      })}
    </div>
  );
}

function DetailGrid({
  items,
}: {
  items: { label: string; value: number | string }[];
}) {
  return (
    <div className="grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2 lg:grid-cols-3">
      {items.map((i) => (
        <div
          key={i.label}
          className="flex items-baseline justify-between border-b border-dashed border-border/60 py-1"
        >
          <span className="text-muted-foreground">{i.label}</span>
          <span className="font-mono text-foreground">{i.value}</span>
        </div>
      ))}
    </div>
  );
}

function Subtotal({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="flex items-center justify-between rounded-md bg-secondary px-3 py-2">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-semibold text-foreground">{value}</span>
    </div>
  );
}

export default CalculatorForm;
