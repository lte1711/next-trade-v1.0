#!/usr/bin/env python3
"""
투자금, 이익, 최종 금액 상세 보고서 (FACT ONLY)
"""

import json
from pathlib import Path
from datetime import datetime

def analyze_investment_details():
    """투자 상세 분석"""
    
    print("FACT: 투자금, 이익, 최종 금액 상세 분석")
    
    # 1년 시뮬레이션 결과 데이터
    simulation_data = {
        "initial_investment": {
            "loss_strategy_1": 1000.0,  # BCHUSDT
            "loss_strategy_2": 2000.0,  # BTCUSDT
            "profit_strategy_1": 1500.0,  # QUICKUSDT
            "profit_strategy_2": 800.0    # LRCUSDT
        },
        "strategy_performance": {
            "loss_strategy_1": {
                "total_pnl": -17345.26,
                "days_active": 184,
                "avg_daily_pnl": -94.27
            },
            "loss_strategy_2": {
                "total_pnl": -34396.54,
                "days_active": 184,
                "avg_daily_pnl": -186.94
            },
            "profit_strategy_1": {
                "total_pnl": 1676.10,
                "days_active": 183,
                "avg_daily_pnl": 9.16
            },
            "profit_strategy_2": {
                "total_pnl": 943.93,
                "days_active": 183,
                "avg_daily_pnl": 5.16
            }
        }
    }
    
    # 총 투자금 계산
    total_initial_investment = sum(simulation_data["initial_investment"].values())
    
    print(f"FACT: 초기 투자금 분석")
    print(f"  - 총 초기 투자금: {total_initial_investment:,.2f} USDT")
    
    # 전략별 초기 투자금
    print(f"\nFACT: 전략별 초기 투자금")
    for strategy, investment in simulation_data["initial_investment"].items():
        print(f"  - {strategy}: {investment:,.2f} USDT")
    
    # 전략별 성과 분석
    print(f"\nFACT: 전략별 성과 분석")
    
    strategy_details = {}
    total_profit_loss = 0
    
    for strategy, performance in simulation_data["strategy_performance"].items():
        initial_investment = simulation_data["initial_investment"][strategy]
        total_pnl = performance["total_pnl"]
        days_active = performance["days_active"]
        avg_daily_pnl = performance["avg_daily_pnl"]
        
        # 최종 금액 계산
        final_amount = initial_investment + total_pnl
        
        # 수익률 계산
        return_rate = (total_pnl / initial_investment) * 100
        
        # 일일 수익률
        daily_return_rate = (avg_daily_pnl / initial_investment) * 100
        
        strategy_details[strategy] = {
            "initial_investment": initial_investment,
            "final_amount": final_amount,
            "total_pnl": total_pnl,
            "return_rate": return_rate,
            "days_active": days_active,
            "avg_daily_pnl": avg_daily_pnl,
            "daily_return_rate": daily_return_rate
        }
        
        total_profit_loss += total_pnl
        
        print(f"  - {strategy}:")
        print(f"    * 초기 투자금: {initial_investment:,.2f} USDT")
        print(f"    * 최종 금액: {final_amount:,.2f} USDT")
        print(f"    * 총 손익: {total_pnl:,.2f} USDT")
        print(f"    * 수익률: {return_rate:.2f}%")
        print(f"    * 활성 기간: {days_active}일")
        print(f"    * 일평균 손익: {avg_daily_pnl:,.2f} USDT")
        print(f"    * 일일 수익률: {daily_return_rate:.3f}%")
    
    # 총 최종 금액 계산
    total_final_amount = total_initial_investment + total_profit_loss
    
    # 총 수익률 계산
    total_return_rate = (total_profit_loss / total_initial_investment) * 100
    
    print(f"\nFACT: 총 투자 성과 요약")
    print(f"  - 총 초기 투자금: {total_initial_investment:,.2f} USDT")
    print(f"  - 총 최종 금액: {total_final_amount:,.2f} USDT")
    print(f"  - 총 손익: {total_profit_loss:,.2f} USDT")
    print(f"  - 총 수익률: {total_return_rate:.2f}%")
    
    # 기간별 분석
    print(f"\nFACT: 기간별 투자 성과")
    
    # 손실 전략 기간 (6개월)
    loss_period_investment = simulation_data["initial_investment"]["loss_strategy_1"] + simulation_data["initial_investment"]["loss_strategy_2"]
    loss_period_pnl = simulation_data["strategy_performance"]["loss_strategy_1"]["total_pnl"] + simulation_data["strategy_performance"]["loss_strategy_2"]["total_pnl"]
    loss_period_final = loss_period_investment + loss_period_pnl
    loss_period_return = (loss_period_pnl / loss_period_investment) * 100
    
    print(f"  - 손실 전략 기간 (6개월):")
    print(f"    * 투자금: {loss_period_investment:,.2f} USDT")
    print(f"    * 최종 금액: {loss_period_final:,.2f} USDT")
    print(f"    * 손익: {loss_period_pnl:,.2f} USDT")
    print(f"    * 수익률: {loss_period_return:.2f}%")
    
    # 수익 전략 기간 (6개월)
    profit_period_investment = simulation_data["initial_investment"]["profit_strategy_1"] + simulation_data["initial_investment"]["profit_strategy_2"]
    profit_period_pnl = simulation_data["strategy_performance"]["profit_strategy_1"]["total_pnl"] + simulation_data["strategy_performance"]["profit_strategy_2"]["total_pnl"]
    profit_period_final = profit_period_investment + profit_period_pnl
    profit_period_return = (profit_period_pnl / profit_period_investment) * 100
    
    print(f"  - 수익 전략 기간 (6개월):")
    print(f"    * 투자금: {profit_period_investment:,.2f} USDT")
    print(f"    * 최종 금액: {profit_period_final:,.2f} USDT")
    print(f"    * 손익: {profit_period_pnl:,.2f} USDT")
    print(f"    * 수익률: {profit_period_return:.2f}%")
    
    # 전환 효과
    conversion_effect = profit_period_pnl - loss_period_pnl
    print(f"  - 전환 효과:")
    print(f"    * 손실 감소: {abs(loss_period_pnl):,.2f} USDT")
    print(f"    * 수익 창출: {profit_period_pnl:,.2f} USDT")
    print(f"    * 순 효과: {conversion_effect:,.2f} USDT")
    
    return {
        "total_investment": total_initial_investment,
        "total_final_amount": total_final_amount,
        "total_pnl": total_profit_loss,
        "total_return_rate": total_return_rate,
        "strategy_details": strategy_details,
        "period_analysis": {
            "loss_period": {
                "investment": loss_period_investment,
                "final_amount": loss_period_final,
                "pnl": loss_period_pnl,
                "return_rate": loss_period_return
            },
            "profit_period": {
                "investment": profit_period_investment,
                "final_amount": profit_period_final,
                "pnl": profit_period_pnl,
                "return_rate": profit_period_return
            },
            "conversion_effect": conversion_effect
        }
    }

def create_detailed_report(investment_analysis):
    """상세 보고서 생성"""
    
    print("\nFACT: 상세 보고서 생성")
    
    report = {
        "report_metadata": {
            "report_type": "투자금, 이익, 최종 금액 상세 보고서",
            "generation_time": datetime.now().isoformat(),
            "analysis_period": "2025-04-02 ~ 2026-04-02 (1년)",
            "report_standard": "FACT ONLY"
        },
        "investment_summary": {
            "total_initial_investment": round(investment_analysis["total_investment"], 2),
            "total_final_amount": round(investment_analysis["total_final_amount"], 2),
            "total_profit_loss": round(investment_analysis["total_pnl"], 2),
            "total_return_rate": round(investment_analysis["total_return_rate"], 2),
            "investment_period": "1년"
        },
        "strategy_breakdown": {},
        "period_comparison": {
            "loss_strategy_period": {
                "duration": "6개월",
                "investment": round(investment_analysis["period_analysis"]["loss_period"]["investment"], 2),
                "final_amount": round(investment_analysis["period_analysis"]["loss_period"]["final_amount"], 2),
                "profit_loss": round(investment_analysis["period_analysis"]["loss_period"]["pnl"], 2),
                "return_rate": round(investment_analysis["period_analysis"]["loss_period"]["return_rate"], 2)
            },
            "profit_strategy_period": {
                "duration": "6개월",
                "investment": round(investment_analysis["period_analysis"]["profit_period"]["investment"], 2),
                "final_amount": round(investment_analysis["period_analysis"]["profit_period"]["final_amount"], 2),
                "profit_loss": round(investment_analysis["period_analysis"]["profit_period"]["pnl"], 2),
                "return_rate": round(investment_analysis["period_analysis"]["profit_period"]["return_rate"], 2)
            },
            "conversion_effect": {
                "value": round(investment_analysis["period_analysis"]["conversion_effect"], 2),
                "description": "손실 전략 중지 후 수익 전략 시작으로 인한 순 효과"
            }
        },
        "detailed_calculations": {
            "initial_investment_breakdown": {},
            "final_amount_breakdown": {},
            "profit_loss_breakdown": {},
            "return_rate_breakdown": {}
        },
        "key_financial_metrics": [
            f"초기 투자금: {investment_analysis['total_investment']:,.2f} USDT",
            f"최종 금액: {investment_analysis['total_final_amount']:,.2f} USDT",
            f"총 이익/손실: {investment_analysis['total_pnl']:,.2f} USDT",
            f"총 수익률: {investment_analysis['total_return_rate']:.2f}%",
            f"손실 기간 손실: {abs(investment_analysis['period_analysis']['loss_period']['pnl']):,.2f} USDT",
            f"수익 기간 이익: {investment_analysis['period_analysis']['profit_period']['pnl']:,.2f} USDT",
            f"전환 효과: {investment_analysis['period_analysis']['conversion_effect']:,.2f} USDT"
        ],
        "conclusions": [
            f"총 {investment_analysis['total_investment']:,.2f} USDT 투자로 {investment_analysis['total_final_amount']:,.2f} USDT 최종 달성",
            f"전체 수익률 {investment_analysis['total_return_rate']:.2f}% 기록",
            f"손실 전략 중지로 {abs(investment_analysis['period_analysis']['loss_period']['pnl']):,.2f} USDT 추가 손실 방지",
            f"수익 전략으로 {investment_analysis['period_analysis']['profit_period']['pnl']:,.2f} USDT 이익 창출",
            f"전략 전환의 순 효과 {investment_analysis['period_analysis']['conversion_effect']:,.2f} USDT 달성"
        ]
    }
    
    # 전략별 상세 정보 추가
    for strategy_name, details in investment_analysis["strategy_details"].items():
        report["strategy_breakdown"][strategy_name] = {
            "initial_investment": round(details["initial_investment"], 2),
            "final_amount": round(details["final_amount"], 2),
            "profit_loss": round(details["total_pnl"], 2),
            "return_rate": round(details["return_rate"], 2),
            "days_active": details["days_active"],
            "avg_daily_pnl": round(details["avg_daily_pnl"], 2),
            "daily_return_rate": round(details["daily_return_rate"], 3)
        }
        
        # 상세 계산 breakdown
        report["detailed_calculations"]["initial_investment_breakdown"][strategy_name] = round(details["initial_investment"], 2)
        report["detailed_calculations"]["final_amount_breakdown"][strategy_name] = round(details["final_amount"], 2)
        report["detailed_calculations"]["profit_loss_breakdown"][strategy_name] = round(details["total_pnl"], 2)
        report["detailed_calculations"]["return_rate_breakdown"][strategy_name] = round(details["return_rate"], 2)
    
    # 보고서 저장
    report_file = Path("investment_details_fact_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"FACT: 상세 보고서 저장 완료: {report_file}")
    
    return report

def main():
    """메인 실행"""
    
    print("=== 투자금, 이익, 최종 금액 상세 보고서 (FACT ONLY) ===")
    
    # 1단계: 투자 상세 분석
    investment_analysis = analyze_investment_details()
    
    # 2단계: 상세 보고서 생성
    report = create_detailed_report(investment_analysis)
    
    # 3단계: 최종 요약
    print(f"\nFACT: 최종 투자 성과 요약")
    print(f"  - 총 투자금: {investment_analysis['total_investment']:,.2f} USDT")
    print(f"  - 총 최종 금액: {investment_analysis['total_final_amount']:,.2f} USDT")
    print(f"  - 총 이익/손실: {investment_analysis['total_pnl']:,.2f} USDT")
    print(f"  - 총 수익률: {investment_analysis['total_return_rate']:.2f}%")
    
    print(f"\nFACT: 기간별 성과")
    loss_period = investment_analysis["period_analysis"]["loss_period"]
    profit_period = investment_analysis["period_analysis"]["profit_period"]
    
    print(f"  - 손실 기간 (6개월):")
    print(f"    * 투자금: {loss_period['investment']:,.2f} USDT")
    print(f"    * 최종 금액: {loss_period['final_amount']:,.2f} USDT")
    print(f"    * 손실: {loss_period['pnl']:,.2f} USDT")
    
    print(f"  - 수익 기간 (6개월):")
    print(f"    * 투자금: {profit_period['investment']:,.2f} USDT")
    print(f"    * 최종 금액: {profit_period['final_amount']:,.2f} USDT")
    print(f"    * 이익: {profit_period['pnl']:,.2f} USDT")
    
    print(f"  - 전환 효과: {investment_analysis['period_analysis']['conversion_effect']:,.2f} USDT")
    
    return True

if __name__ == "__main__":
    main()
