#!/usr/bin/env python3
"""
Final Logic Check - Comprehensive check of all system logic
"""

import json
from datetime import datetime

def final_logic_check():
    """Comprehensive check of all system logic"""
    print('=' * 80)
    print('FINAL LOGIC CHECK - COMPREHENSIVE SYSTEM VERIFICATION')
    print('=' * 80)
    
    print(f'Final Check Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 1. System Architecture Check
    print('\n[1] SYSTEM ARCHITECTURE CHECK')
    
    try:
        # Check all core components
        components = {
            'Strategy Registry': 'core.strategy_registry',
            'Market Data Service': 'core.market_data_service',
            'Market Regime Service': 'core.market_regime_service',
            'Signal Engine': 'core.signal_engine',
            'Trade Orchestrator': 'core.trade_orchestrator',
            'Position Manager': 'core.position_manager'
        }
        
        working_components = 0
        total_components = len(components)
        
        print('  - Core Components Status:')
        
        for component_name, module_path in components.items():
            try:
                exec(f"import {module_path}")
                print(f'    - {component_name}: WORKING')
                working_components += 1
            except Exception as e:
                print(f'    - {component_name}: ERROR - {str(e)[:50]}...')
        
        architecture_score = (working_components / total_components) * 100
        print(f'  - Architecture Health Score: {architecture_score:.1f}%')
        
        if architecture_score >= 90:
            architecture_status = 'EXCELLENT'
        elif architecture_score >= 75:
            architecture_status = 'GOOD'
        elif architecture_score >= 50:
            architecture_status = 'FAIR'
        else:
            architecture_status = 'POOR'
        
        print(f'  - Architecture Status: {architecture_status}')
        
    except Exception as e:
        print(f'  - Error in architecture check: {e}')
    
    # 2. Signal Engine Logic Check
    print('\n[2] SIGNAL ENGINE LOGIC CHECK')
    
    try:
        from core.signal_engine import SignalEngine
        from core.market_data_service import MarketDataService
        
        se = SignalEngine()
        mds = MarketDataService('https://demo-fapi.binance.com')
        
        print('  - Signal Engine Logic Verification:')
        
        # Test with known data
        test_cases = [
            {
                'name': 'Price Above SMA',
                'price': 105.0,
                'sma_10': 100.0,
                'volume': 2000,
                'expected_signal': 'BUY'
            },
            {
                'name': 'Price Below SMA',
                'price': 95.0,
                'sma_10': 100.0,
                'volume': 2000,
                'expected_signal': 'SELL'
            },
            {
                'name': 'Price at SMA',
                'price': 100.0,
                'sma_10': 100.0,
                'volume': 2000,
                'expected_signal': 'HOLD'
            },
            {
                'name': 'Low Volume',
                'price': 105.0,
                'sma_10': 100.0,
                'volume': 500,
                'expected_signal': 'HOLD'
            }
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for test_case in test_cases:
            indicators = {
                'price': test_case['price'],
                'sma_10': test_case['sma_10'],
                'volume': test_case['volume']
            }
            
            strategy_config = {
                'name': 'test',
                'entry_filters': {'min_confidence': 0.3}
            }
            
            signal_result = se.generate_strategy_signal(
                {'prices': {'current': test_case['price']}},
                indicators,
                {'regime': 'RANGING'},
                strategy_config
            )
            
            actual_signal = signal_result.get('signal', 'HOLD')
            expected_signal = test_case['expected_signal']
            
            if actual_signal == expected_signal:
                status = 'PASS'
                passed_tests += 1
            else:
                status = 'FAIL'
            
            confidence = signal_result.get('confidence', 0)
            reason = signal_result.get('reason', 'No reason')
            
            print(f'    - {test_case["name"]}: {status}')
            print(f'      * Expected: {expected_signal}, Actual: {actual_signal}')
            print(f'      * Confidence: {confidence:.2f}, Reason: {reason}')
        
        signal_logic_score = (passed_tests / total_tests) * 100
        print(f'  - Signal Logic Score: {signal_logic_score:.1f}%')
        
        if signal_logic_score >= 90:
            signal_logic_status = 'EXCELLENT'
        elif signal_logic_score >= 75:
            signal_logic_status = 'GOOD'
        elif signal_logic_score >= 50:
            signal_logic_status = 'FAIR'
        else:
            signal_logic_status = 'POOR'
        
        print(f'  - Signal Logic Status: {signal_logic_status}')
        
    except Exception as e:
        print(f'  - Error in signal engine check: {e}')
    
    # 3. Strategy Configuration Check
    print('\n[3] STRATEGY CONFIGURATION CHECK')
    
    try:
        from core.strategy_registry import StrategyRegistry
        
        sr = StrategyRegistry()
        
        strategies = ['ma_trend_follow', 'ema_crossover']
        
        print('  - Strategy Configuration Verification:')
        
        strategy_checks = {
            'valid_config': 0,
            'valid_filters': 0,
            'valid_risk': 0,
            'valid_selection': 0
        }
        
        for strategy_name in strategies:
            strategy_config = sr.get_strategy_profile(strategy_name)
            
            if strategy_config:
                print(f'    - {strategy_name.upper()}:')
                
                # Check configuration structure
                required_keys = ['name', 'entry_filters', 'risk_config', 'symbol_selection']
                config_valid = all(key in strategy_config for key in required_keys)
                
                if config_valid:
                    strategy_checks['valid_config'] += 1
                    print(f'      * Configuration: VALID')
                else:
                    print(f'      * Configuration: INVALID (missing keys)')
                
                # Check entry filters
                entry_filters = strategy_config.get('entry_filters', {})
                filter_keys = ['min_confidence', 'min_trend_strength', 'max_volatility']
                filters_valid = all(key in entry_filters for key in filter_keys)
                
                if filters_valid:
                    strategy_checks['valid_filters'] += 1
                    print(f'      * Entry Filters: VALID')
                else:
                    print(f'      * Entry Filters: INVALID')
                
                # Check risk configuration
                risk_config = strategy_config.get('risk_config', {})
                risk_keys = ['stop_loss_pct', 'take_profit_pct', 'max_position_size_usdt']
                risk_valid = all(key in risk_config for key in risk_keys)
                
                if risk_valid:
                    strategy_checks['valid_risk'] += 1
                    print(f'      * Risk Config: VALID')
                else:
                    print(f'      * Risk Config: INVALID')
                
                # Check symbol selection
                symbol_selection = strategy_config.get('symbol_selection', {})
                selection_keys = ['candidate_limit', 'symbol_mode']
                selection_valid = all(key in symbol_selection for key in selection_keys)
                
                if selection_valid:
                    strategy_checks['valid_selection'] += 1
                    print(f'      * Symbol Selection: VALID')
                else:
                    print(f'      * Symbol Selection: INVALID')
            else:
                print(f'    - {strategy_name.upper()}: NOT FOUND')
        
        # Calculate strategy configuration score
        total_checks = sum(strategy_checks.values())
        max_checks = len(strategies) * 4  # 4 checks per strategy
        
        if max_checks > 0:
            strategy_config_score = (total_checks / max_checks) * 100
        else:
            strategy_config_score = 0
        
        print(f'  - Strategy Configuration Score: {strategy_config_score:.1f}%')
        
        if strategy_config_score >= 90:
            strategy_config_status = 'EXCELLENT'
        elif strategy_config_score >= 75:
            strategy_config_status = 'GOOD'
        elif strategy_config_score >= 50:
            strategy_config_status = 'FAIR'
        else:
            strategy_config_status = 'POOR'
        
        print(f'  - Strategy Configuration Status: {strategy_config_status}')
        
    except Exception as e:
        print(f'  - Error in strategy configuration check: {e}')
    
    # 4. Market Data Logic Check
    print('\n[4] MARKET DATA LOGIC CHECK')
    
    try:
        from core.market_data_service import MarketDataService
        
        mds = MarketDataService('https://demo-fapi.binance.com')
        
        print('  - Market Data Logic Verification:')
        
        # Test market data fetching
        symbols = ['BTCUSDT', 'ETHUSDT']
        
        market_data = mds.update_market_data(symbols)
        
        if market_data:
            print(f'    - Market Data Fetch: SUCCESS ({len(market_data)} symbols)')
            
            # Check data structure
            data_structure_valid = True
            
            for symbol, data in market_data.items():
                required_keys = ['symbol', 'price', 'klines']
                if not all(key in data for key in required_keys):
                    data_structure_valid = False
                    break
                
                # Check klines structure
                klines = data.get('klines', {})
                if '1h' not in klines or not klines['1h']:
                    data_structure_valid = False
                    break
            
            if data_structure_valid:
                print('    - Data Structure: VALID')
                market_data_score = 100
            else:
                print('    - Data Structure: INVALID')
                market_data_score = 50
        else:
            print('    - Market Data Fetch: FAILED')
            market_data_score = 0
        
        print(f'  - Market Data Score: {market_data_score:.1f}%')
        
        if market_data_score >= 90:
            market_data_status = 'EXCELLENT'
        elif market_data_score >= 75:
            market_data_status = 'GOOD'
        elif market_data_score >= 50:
            market_data_status = 'FAIR'
        else:
            market_data_status = 'POOR'
        
        print(f'  - Market Data Status: {market_data_status}')
        
    except Exception as e:
        print(f'  - Error in market data check: {e}')
        market_data_score = 0
        market_data_status = 'ERROR'
    
    # 5. Trade Execution Logic Check
    print('\n[5] TRADE EXECUTION LOGIC CHECK')
    
    try:
        from core.trade_orchestrator import TradeOrchestrator
        
        print('  - Trade Execution Logic Verification:')
        
        # Check if trade orchestrator can be instantiated
        # Note: We won't actually execute trades, just check the logic
        
        try:
            # This might fail due to dependencies, but we can check the structure
            import inspect
            to_methods = dir(TradeOrchestrator)
            
            required_methods = [
                'execute_strategy_trade',
                '_check_duplicate_entry',
                'can_open_new_positions'
            ]
            
            methods_valid = all(method in to_methods for method in required_methods)
            
            if methods_valid:
                print('    - Trade Orchestrator Methods: VALID')
                trade_execution_score = 100
            else:
                print('    - Trade Orchestrator Methods: INVALID')
                trade_execution_score = 50
        except Exception as e:
            print(f'    - Trade Orchestrator Check: ERROR - {e}')
            trade_execution_score = 50
        
        print(f'  - Trade Execution Score: {trade_execution_score:.1f}%')
        
        if trade_execution_score >= 90:
            trade_execution_status = 'EXCELLENT'
        elif trade_execution_score >= 75:
            trade_execution_status = 'GOOD'
        elif trade_execution_score >= 50:
            trade_execution_status = 'FAIR'
        else:
            trade_execution_status = 'POOR'
        
        print(f'  - Trade Execution Status: {trade_execution_status}')
        
    except Exception as e:
        print(f'  - Error in trade execution check: {e}')
        trade_execution_score = 0
        trade_execution_status = 'ERROR'
    
    # 6. Risk Management Logic Check
    print('\n[6] RISK MANAGEMENT LOGIC CHECK')
    
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        print('  - Risk Management Logic Verification:')
        
        # Check position limits
        active_positions = results.get('active_positions', {})
        max_positions = 5
        
        position_limit_check = len(active_positions) <= max_positions
        
        if position_limit_check:
            print(f'    - Position Limits: VALID ({len(active_positions)}/{max_positions})')
            risk_management_score = 100
        else:
            print(f'    - Position Limits: EXCEEDED ({len(active_positions)}/{max_positions})')
            risk_management_score = 50
        
        # Check TP/SL settings
        tp_sl_valid = True
        
        for symbol, position in active_positions.items():
            if 'stop_loss_pct' not in position or 'take_profit_pct' not in position:
                tp_sl_valid = False
                break
        
        if tp_sl_valid:
            print('    - TP/SL Settings: VALID')
        else:
            print('    - TP/SL Settings: INVALID')
            risk_management_score = min(risk_management_score, 75)
        
        # Check duplicate prevention
        pending_trades = results.get('pending_trades', [])
        duplicate_symbols = set()
        
        for trade in pending_trades:
            symbol = trade.get('symbol', '')
            if symbol in duplicate_symbols:
                duplicate_found = True
                break
            duplicate_symbols.add(symbol)
        else:
            duplicate_found = False
        
        if not duplicate_found:
            print('    - Duplicate Prevention: VALID')
        else:
            print('    - Duplicate Prevention: DUPLICATES FOUND')
            risk_management_score = min(risk_management_score, 75)
        
        print(f'  - Risk Management Score: {risk_management_score:.1f}%')
        
        if risk_management_score >= 90:
            risk_management_status = 'EXCELLENT'
        elif risk_management_score >= 75:
            risk_management_status = 'GOOD'
        elif risk_management_score >= 50:
            risk_management_status = 'FAIR'
        else:
            risk_management_status = 'POOR'
        
        print(f'  - Risk Management Status: {risk_management_status}')
        
    except Exception as e:
        print(f'  - Error in risk management check: {e}')
        risk_management_score = 0
        risk_management_status = 'ERROR'
    
    # 7. End-to-End Logic Check
    print('\n[7] END-TO-END LOGIC CHECK')
    
    try:
        print('  - End-to-End Logic Verification:')
        
        # Simulate complete trading cycle
        end_to_end_steps = [
            'Market Data Update',
            'Regime Analysis',
            'Signal Generation',
            'Signal Evaluation',
            'Trade Execution',
            'Risk Management'
        ]
        
        step_results = {}
        
        # Step 1: Market Data Update
        try:
            mds = MarketDataService('https://demo-fapi.binance.com')
            market_data = mds.update_market_data(['BTCUSDT'])
            step_results['Market Data Update'] = 'PASS' if market_data else 'FAIL'
        except:
            step_results['Market Data Update'] = 'FAIL'
        
        # Step 2: Regime Analysis
        try:
            from core.market_regime_service import MarketRegimeService
            mrs = MarketRegimeService()
            test_prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119]
            regime = mrs.analyze_market_regime(test_prices, [1000] * 20)
            step_results['Regime Analysis'] = 'PASS' if regime else 'FAIL'
        except:
            step_results['Regime Analysis'] = 'FAIL'
        
        # Step 3: Signal Generation
        try:
            se = SignalEngine()
            signal = se.generate_strategy_signal(
                {'prices': {'current': 105}},
                {'price': 105, 'sma_10': 100, 'volume': 2000},
                {'regime': 'RANGING'},
                {'name': 'test', 'entry_filters': {'min_confidence': 0.3}}
            )
            step_results['Signal Generation'] = 'PASS' if signal else 'FAIL'
        except:
            step_results['Signal Generation'] = 'FAIL'
        
        # Step 4: Signal Evaluation
        try:
            signal_type = signal.get('signal', 'HOLD')
            confidence = signal.get('confidence', 0)
            step_results['Signal Evaluation'] = 'PASS' if confidence > 0 else 'FAIL'
        except:
            step_results['Signal Evaluation'] = 'FAIL'
        
        # Step 5: Trade Execution (Logic Check Only)
        try:
            # Check if trade orchestrator has required methods
            to_methods = dir(TradeOrchestrator)
            step_results['Trade Execution'] = 'PASS' if 'execute_strategy_trade' in to_methods else 'FAIL'
        except:
            step_results['Trade Execution'] = 'FAIL'
        
        # Step 6: Risk Management
        try:
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
            active_positions = results.get('active_positions', {})
            step_results['Risk Management'] = 'PASS' if len(active_positions) <= 5 else 'FAIL'
        except:
            step_results['Risk Management'] = 'FAIL'
        
        # Calculate end-to-end score
        passed_steps = sum(1 for result in step_results.values() if result == 'PASS')
        total_steps = len(step_results)
        
        end_to_end_score = (passed_steps / total_steps) * 100
        
        print('  - End-to-End Steps:')
        for step, result in step_results.items():
            print(f'    - {step}: {result}')
        
        print(f'  - End-to-End Score: {end_to_end_score:.1f}%')
        
        if end_to_end_score >= 90:
            end_to_end_status = 'EXCELLENT'
        elif end_to_end_score >= 75:
            end_to_end_status = 'GOOD'
        elif end_to_end_score >= 50:
            end_to_end_status = 'FAIR'
        else:
            end_to_end_status = 'POOR'
        
        print(f'  - End-to-End Status: {end_to_end_status}')
        
    except Exception as e:
        print(f'  - Error in end-to-end check: {e}')
        end_to_end_score = 0
        end_to_end_status = 'ERROR'
    
    # 8. Overall System Health
    print('\n[8] OVERALL SYSTEM HEALTH')
    
    try:
        # Calculate overall score
        scores = {
            'Architecture': architecture_score,
            'Signal Logic': signal_logic_score,
            'Strategy Config': strategy_config_score,
            'Market Data': market_data_score,
            'Trade Execution': trade_execution_score,
            'Risk Management': risk_management_score,
            'End-to-End': end_to_end_score
        }
        
        total_score = sum(scores.values())
        num_scores = len(scores)
        overall_score = total_score / num_scores
        
        print('  - Component Scores:')
        for component, score in scores.items():
            print(f'    - {component}: {score:.1f}%')
        
        print(f'  - Overall System Score: {overall_score:.1f}%')
        
        if overall_score >= 90:
            overall_status = 'EXCELLENT'
            status_emoji = 'EXCELLENT'
        elif overall_score >= 75:
            overall_status = 'GOOD'
            status_emoji = 'GOOD'
        elif overall_score >= 50:
            overall_status = 'FAIR'
            status_emoji = 'FAIR'
        else:
            overall_status = 'POOR'
            status_emoji = 'POOR'
        
        print(f'  - Overall System Status: {overall_status}')
        
        # System readiness assessment
        if overall_score >= 80:
            readiness = 'PRODUCTION READY'
        elif overall_score >= 60:
            readiness = 'TESTING READY'
        elif overall_score >= 40:
            readiness = 'DEVELOPMENT NEEDED'
        else:
            readiness = 'MAINTENANCE REQUIRED'
        
        print(f'  - System Readiness: {readiness}')
        
    except Exception as e:
        print(f'  - Error calculating overall score: {e}')
        overall_score = 0
        overall_status = 'ERROR'
        readiness = 'MAINTENANCE REQUIRED'
    
    # 9. Final Recommendations
    print('\n[9] FINAL RECOMMENDATIONS')
    
    recommendations = []
    
    if architecture_score < 90:
        recommendations.append('Review and fix core component issues')
    
    if signal_logic_score < 90:
        recommendations.append('Optimize signal generation logic')
    
    if strategy_config_score < 90:
        recommendations.append('Review and update strategy configurations')
    
    if market_data_score < 90:
        recommendations.append('Improve market data fetching and processing')
    
    if trade_execution_score < 90:
        recommendations.append('Enhance trade execution logic')
    
    if risk_management_score < 90:
        recommendations.append('Strengthen risk management controls')
    
    if end_to_end_score < 90:
        recommendations.append('Fix end-to-end workflow issues')
    
    if overall_score >= 80:
        recommendations.append('System is ready for production trading')
    elif overall_score >= 60:
        recommendations.append('System needs minor improvements before production')
    else:
        recommendations.append('System requires significant improvements')
    
    print('  - Recommendations:')
    for i, rec in enumerate(recommendations, 1):
        print(f'    {i}. {rec}')
    
    # 10. Conclusion
    print('\n[10] CONCLUSION')
    
    print('  - Final Logic Check Summary:')
    print(f'    - Architecture: {architecture_score:.1f}%')
    print(f'    - Signal Logic: {signal_logic_score:.1f}%')
    print(f'    - Strategy Config: {strategy_config_score:.1f}%')
    print(f'    - Market Data: {market_data_score:.1f}%')
    print(f'    - Trade Execution: {trade_execution_score:.1f}%')
    print(f'    - Risk Management: {risk_management_score:.1f}%')
    print(f'    - End-to-End: {end_to_end_score:.1f}%')
    print(f'    - Overall: {overall_score:.1f}%')
    
    print(f'  - System Status: {overall_status}')
    print(f'  - Readiness: {readiness}')
    
    if overall_score >= 80:
        print('  - Conclusion: SYSTEM IS READY FOR PRODUCTION TRADING')
    elif overall_score >= 60:
        print('  - Conclusion: SYSTEM IS MOSTLY READY WITH MINOR ISSUES')
    else:
        print('  - Conclusion: SYSTEM NEEDS SIGNIFICANT IMPROVEMENTS')
    
    print('\n' + '=' * 80)
    print('[FINAL LOGIC CHECK COMPLETE]')
    print('=' * 80)
    print(f'Overall Score: {overall_score:.1f}%')
    print(f'System Status: {overall_status}')
    print(f'Readiness: {readiness}')
    print('=' * 80)

if __name__ == "__main__":
    final_logic_check()
