#!/usr/bin/env python3
"""
바이낸스 5년 데이터 분석 - 하루 거래량이 가장 많은 시간대 분석 (30분 간격)
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

class BinanceVolumeAnalyzer:
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.major_symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
            "XRPUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "MATICUSDT",
            "LINKUSDT", "UNIUSDT", "LTCUSDT", "ATOMUSDT", "FILUSDT"
        ]
        self.volume_data = defaultdict(list)
        self.time_volume_analysis = defaultdict(float)
        
    def get_klines_data(self, symbol, interval, start_time, end_time):
        """Klines 데이터 가져오기"""
        try:
            url = f"{self.base_url}/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "startTime": start_time,
                "endTime": end_time,
                "limit": 1000
            }
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ {symbol} 데이터 가져오기 실패: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ {symbol} 데이터 오류: {e}")
            return None
    
    def analyze_5_year_data(self):
        """5년 데이터 분석"""
        print("🚀 바이낸스 5년 데이터 분석 시작...")
        print(f"📊 대상 심볼: {len(self.major_symbols)}개")
        print("=" * 80)
        
        # 5년 전 날짜 계산
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=365*5)).timestamp() * 1000)
        
        print(f"⏰ 분석 기간: {datetime.fromtimestamp(start_time/1000).strftime('%Y-%m-%d')} ~ {datetime.fromtimestamp(end_time/1000).strftime('%Y-%m-%d')}")
        print(f"📈 데이터 간격: 30분 (30m)")
        
        # 각 심볼별 데이터 수집
        for i, symbol in enumerate(self.major_symbols):
            print(f"\n📊 {symbol} 데이터 분석 중... ({i+1}/{len(self.major_symbols)})")
            
            # 30분 간격 데이터 수집 (5년간)
            current_start = start_time
            all_klines = []
            
            while current_start < end_time:
                current_end = min(current_start + (1000 * 30 * 60 * 1000), end_time)  # 1000개 30분봉
                
                klines = self.get_klines_data(symbol, "30m", current_start, current_end)
                if klines:
                    all_klines.extend(klines)
                
                current_start = current_end
                time.sleep(0.1)  # API 레이트 리밋
            
            # 시간대별 거래량 분석
            self.analyze_volume_by_time(symbol, all_klines)
            
            print(f"✅ {symbol} 분석 완료: {len(all_klines)}개 데이터")
        
        print("\n🎯 모든 심볼 분석 완료!")
        
    def analyze_volume_by_time(self, symbol, klines):
        """시간대별 거래량 분석"""
        for kline in klines:
            timestamp = int(kline[0])
            volume = float(kline[5])  # 거래량
            
            # UTC 시간으로 변환
            dt = datetime.fromtimestamp(timestamp / 1000, tz=None)
            hour = dt.hour
            minute = dt.minute
            
            # 30분 간격으로 그룹화
            time_slot = f"{hour:02d}:{minute//30*30:02d}-{hour:02d}:{(minute//30+1)*30:02d}"
            
            # 시간대별 거래량 누적
            self.time_volume_analysis[time_slot] += volume
            
            # 심볼별 데이터 저장
            self.volume_data[symbol].append({
                'timestamp': timestamp,
                'datetime': dt,
                'volume': volume,
                'time_slot': time_slot
            })
    
    def generate_volume_report(self):
        """거래량 분석 보고서 생성"""
        print("\n📋 하루 거래량 분석 보고서 생성...")
        
        # 시간대별 거래량 정렬
        sorted_times = sorted(self.time_volume_analysis.items(), key=lambda x: x[1], reverse=True)
        
        # 총 거래량 계산
        total_volume = sum(self.time_volume_analysis.values())
        
        print(f"\n📊 5년간 총 거래량: {total_volume:,.0f}")
        print("=" * 80)
        
        # 상위 10개 시간대 표시
        print("🏆 거래량이 가장 많은 시간대 TOP 10 (30분 간격):")
        print("-" * 80)
        
        for i, (time_slot, volume) in enumerate(sorted_times[:10]):
            percentage = (volume / total_volume) * 100
            print(f"{i+1:2d}. {time_slot} | 거래량: {volume:,.0f} | 비중: {percentage:.2f}%")
        
        # 시간대별 거래량 분석
        print("\n📈 시간대별 거래량 분석:")
        print("-" * 80)
        
        # 시간대별 그룹화
        hourly_volume = defaultdict(float)
        for time_slot, volume in self.time_volume_analysis.items():
            hour = int(time_slot.split(':')[0])
            hourly_volume[hour] += volume
        
        # 시간대별 정렬
        sorted_hours = sorted(hourly_volume.items(), key=lambda x: x[1], reverse=True)
        
        print("🏆 거래량이 가장 많은 시간대 (시간별):")
        for i, (hour, volume) in enumerate(sorted_hours[:8]):
            percentage = (volume / total_volume) * 100
            print(f"{i+1:2d}. {hour:02d}:00-{hour:02d}:59 | 거래량: {volume:,.0f} | 비중: {percentage:.2f}%")
        
        # 피크 타임 분석
        peak_times = [time_slot for time_slot, volume in sorted_times[:5]]
        print(f"\n🎯 피크 타임 (상위 5개): {', '.join(peak_times)}")
        
        return sorted_times, sorted_hours
    
    def create_visualization(self, sorted_times, sorted_hours):
        """시각화 생성"""
        try:
            # 시간대별 거래량 시각화
            plt.figure(figsize=(15, 10))
            
            # 30분 간격 거래량
            plt.subplot(2, 2, 1)
            times = [item[0] for item in sorted_times[:24]]  # 상위 24개
            volumes = [item[1] for item in sorted_times[:24]]
            
            plt.bar(range(len(times)), volumes)
            plt.title('거래량 TOP 24 시간대 (30분 간격)', fontsize=14, fontweight='bold')
            plt.xlabel('시간대')
            plt.ylabel('거래량')
            plt.xticks(range(len(times)), times, rotation=45)
            plt.grid(True, alpha=0.3)
            
            # 시간별 거래량
            plt.subplot(2, 2, 2)
            hours = [f"{item[0]:02d}:00" for item in sorted_hours]
            hour_volumes = [item[1] for item in sorted_hours]
            
            plt.bar(range(len(hours)), hour_volumes, color='orange')
            plt.title('시간별 거래량', fontsize=14, fontweight='bold')
            plt.xlabel('시간')
            plt.ylabel('거래량')
            plt.xticks(range(len(hours)), hours, rotation=45)
            plt.grid(True, alpha=0.3)
            
            # 24시간 거래량 분포
            plt.subplot(2, 2, 3)
            hour_labels = [f"{h:02d}:00" for h in range(24)]
            hour_volumes_24 = [hourly_volume.get(h, 0) for h in range(24)]
            
            plt.plot(range(24), hour_volumes_24, marker='o', linewidth=2, markersize=6)
            plt.title('24시간 거래량 추이', fontsize=14, fontweight='bold')
            plt.xlabel('시간')
            plt.ylabel('거래량')
            plt.xticks(range(24), hour_labels, rotation=45)
            plt.grid(True, alpha=0.3)
            
            # 거래량 비중 파이 차트
            plt.subplot(2, 2, 4)
            top_5_times = sorted_times[:5]
            labels = [item[0] for item in top_5_times]
            sizes = [item[1] for item in top_5_times]
            others = total_volume - sum(sizes)
            labels.append('기타')
            sizes.append(others)
            
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            plt.title('TOP 5 시간대 거래량 비중', fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig('binance_volume_analysis.png', dpi=300, bbox_inches='tight')
            print("📊 시각화 차트 저장: binance_volume_analysis.png")
            
        except Exception as e:
            print(f"❌ 시각화 생성 오류: {e}")
    
    def save_detailed_report(self, sorted_times, sorted_hours):
        """상세 보고서 저장"""
        report = {
            "analysis_date": datetime.now().isoformat(),
            "analysis_period": "5년",
            "symbols_analyzed": self.major_symbols,
            "data_interval": "30분",
            "total_volume": sum(self.time_volume_analysis.values()),
            "top_30min_intervals": [
                {
                    "rank": i+1,
                    "time_slot": time_slot,
                    "volume": volume,
                    "percentage": (volume / sum(self.time_volume_analysis.values())) * 100
                }
                for i, (time_slot, volume) in enumerate(sorted_times)
            ],
            "top_hourly_intervals": [
                {
                    "rank": i+1,
                    "hour": hour,
                    "volume": volume,
                    "percentage": (volume / sum(self.time_volume_analysis.values())) * 100
                }
                for i, (hour, volume) in enumerate(sorted_hours)
            ],
            "peak_trading_times": [time_slot for time_slot, volume in sorted_times[:5]],
            "recommendations": self.generate_recommendations(sorted_times, sorted_hours)
        }
        
        with open('binance_volume_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("📁 상세 보고서 저장: binance_volume_analysis_report.json")
    
    def generate_recommendations(self, sorted_times, sorted_hours):
        """거래 추천 생성"""
        recommendations = []
        
        # 피크 타임 기반 추천
        peak_times = sorted_times[:3]
        recommendations.append({
            "type": "peak_trading",
            "description": "가장 활발한 거래 시간대",
            "times": [time_slot for time_slot, volume in peak_times],
            "reason": "거래량이 가장 많아 유동성이 높음"
        })
        
        # 저성장 시간대
        low_times = sorted_times[-3:]
        recommendations.append({
            "type": "low_volume",
            "description": "거래량이 적은 시간대",
            "times": [time_slot for time_slot, volume in low_times],
            "reason": "유동성이 낮아 슬리피지 발생 가능성"
        })
        
        # 시간대별 전략
        if sorted_hours[0][0] >= 0 and sorted_hours[0][0] < 6:
            recommendations.append({
                "type": "strategy",
                "description": "새벽 시간대 전략",
                "strategy": "단기 스캘핑 및 뉴스 기반 거래",
                "reason": "아시아 시장 개장 전후 변동성"
            })
        elif sorted_hours[0][0] >= 13 and sorted_hours[0][0] < 16:
            recommendations.append({
                "type": "strategy",
                "description": "유럽 시간대 전략",
                "strategy": "중기 스윙 트레이딩",
                "reason": "유럽 시장 활동으로 인한 변동성"
            })
        elif sorted_hours[0][0] >= 20 and sorted_hours[0][0] < 23:
            recommendations.append({
                "type": "strategy",
                "description": "미국 시간대 전략",
                "strategy": "단기 및 장기 포지션",
                "reason": "미국 시장 활동으로 인한 높은 거래량"
            })
        
        return recommendations
    
    def run_analysis(self):
        """전체 분석 실행"""
        print("🚀 바이낸스 5년 데이터 거래량 분석 시작!")
        print("=" * 80)
        
        # 5년 데이터 분석
        self.analyze_5_year_data()
        
        # 보고서 생성
        sorted_times, sorted_hours = self.generate_volume_report()
        
        # 시각화 생성
        self.create_visualization(sorted_times, sorted_hours)
        
        # 상세 보고서 저장
        self.save_detailed_report(sorted_times, sorted_hours)
        
        print("\n🎉 분석 완료!")
        print("=" * 80)
        
        return sorted_times, sorted_hours

if __name__ == "__main__":
    analyzer = BinanceVolumeAnalyzer()
    sorted_times, sorted_hours = analyzer.run_analysis()
