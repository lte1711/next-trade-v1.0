#!/usr/bin/env python3
"""
Position Cross Logic Check - Check if position crossing logic exists in the system
"""

import json
import os
import re
from datetime import datetime

def check_file_for_cross_logic(filepath, search_terms):
    """Check if file contains position crossing logic"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        found_terms = {}
        for term in search_terms:
            if term.lower() in content.lower():
                # Find line numbers where term appears
                lines = content.split('\n')
                line_numbers = []
                for i, line in enumerate(lines, 1):
                    if term.lower() in line.lower():
                        line_numbers.append(i)
                found_terms[term] = line_numbers
        
        return found_terms, content
    
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return {}, ""

def analyze_position_cross_logic():
    """Analyze if position crossing logic exists in the system"""
    print('=' * 80)
    print('POSITION CROSS LOGIC ANALYSIS')
    print('=' * 80)
    
    print(f'Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # Search terms related to position crossing
    cross_search_terms = [
        'cross',
        'reverse',
        'flip',
        'switch',
        'short_to_long',
        'long_to_short',
        'position_cross',
        'position_reverse',
        'position_flip',
        'close_and_open',
        'cross_position',
        'cross_trade',
        'cross_strategy'
    ]
    
    # Additional trading logic terms
    trading_logic_terms = [
        'close_position',
        'open_position',
        'close_short',
        'open_long',
        'buy_short',
        'sell_long',
        'position_management',
        'position_switch',
        'direction_change',
        'side_change'
    ]
    
    all_search_terms = cross_search_terms + trading_logic_terms
    
    # Files to check
    files_to_check = [
        'main_runtime.py',
        'core/signal_engine.py',
        'core/trade_orchestrator.py',
        'core/strategy_registry.py',
        'core/market_data_service.py',
        'core/indicator_service.py',
        'core/position_manager.py',
        'core/order_executor.py',
        'core/risk_manager.py'
    ]
    
    print('\n[1] SEARCHING FOR POSITION CROSS LOGIC')
    
    cross_logic_found = False
    cross_logic_details = []
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            print(f'\n  🔍 Checking: {filepath}')
            
            found_terms, content = check_file_for_cross_logic(filepath, all_search_terms)
            
            if found_terms:
                cross_logic_found = True
                print(f'    ✅ Found cross-related terms:')
                
                for term, line_numbers in found_terms.items():
                    print(f'      - {term}: lines {line_numbers}')
                    
                    # Get context for each found term
                    lines = content.split('\n')
                    for line_num in line_numbers[:3]:  # Show first 3 occurrences
                        if 1 <= line_num <= len(lines):
                            context_line = lines[line_num - 1].strip()
                            print(f'        Line {line_num}: {context_line}')
                
                cross_logic_details.append({
                    'file': filepath,
                    'found_terms': found_terms,
                    'has_cross_logic': any(term in cross_search_terms for term in found_terms.keys())
                })
            else:
                print(f'    ❌ No cross-related terms found')
        else:
            print(f'\n  ⚠️  File not found: {filepath}')
    
    # Check configuration files
    print('\n[2] CHECKING CONFIGURATION FILES')
    
    config_files = [
        'config.json',
        'trading_results.json',
        'strategy_config.json'
    ]
    
    config_cross_logic = []
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f'\n  🔍 Checking: {config_file}')
            
            try:
                with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                found_terms = {}
                for term in cross_search_terms:
                    if term.lower() in content.lower():
                        found_terms[term] = True
                
                if found_terms:
                    print(f'    ✅ Found cross-related terms:')
                    for term in found_terms:
                        print(f'      - {term}')
                    
                    config_cross_logic.append({
                        'file': config_file,
                        'found_terms': found_terms
                    })
                else:
                    print(f'    ❌ No cross-related terms found')
            
            except Exception as e:
                print(f'    ⚠️  Error reading {config_file}: {e}')
    
    # Check strategy files
    print('\n[3] CHECKING STRATEGY FILES')
    
    strategy_files = []
    
    # Look for strategy files in various directories
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('_strategy.py') or file.endswith('strategies.py'):
                strategy_files.append(os.path.join(root, file))
    
    strategy_cross_logic = []
    
    for strategy_file in strategy_files[:10]:  # Limit to first 10 files
        print(f'\n  🔍 Checking: {strategy_file}')
        
        found_terms, content = check_file_for_cross_logic(strategy_file, all_search_terms)
        
        if found_terms:
            print(f'    ✅ Found cross-related terms:')
            for term, line_numbers in found_terms.items():
                print(f'      - {term}: lines {line_numbers}')
            
            strategy_cross_logic.append({
                'file': strategy_file,
                'found_terms': found_terms
            })
        else:
            print(f'    ❌ No cross-related terms found')
    
    # Analyze position manager specifically
    print('\n[4] DETAILED POSITION MANAGER ANALYSIS')
    
    position_manager_file = 'core/position_manager.py'
    if os.path.exists(position_manager_file):
        print(f'\n  🔍 Deep Analysis: {position_manager_file}')
        
        try:
            with open(position_manager_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for specific position management functions
            position_functions = [
                'def close_position',
                'def open_position',
                'def manage_position',
                'def update_position',
                'def reverse_position',
                'def switch_position',
                'def cross_position'
            ]
            
            found_functions = []
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                for func in position_functions:
                    if func in line:
                        found_functions.append({
                            'function': func,
                            'line': i,
                            'content': line.strip()
                        })
            
            if found_functions:
                print(f'    ✅ Found position management functions:')
                for func_info in found_functions:
                    print(f'      - {func_info["function"]} at line {func_info["line"]}: {func_info["content"]}')
            else:
                print(f'    ❌ No position management functions found')
            
            # Check for position switching logic
            switching_patterns = [
                r'if.*side.*==.*["\']SHORT["\'].*else.*LONG',
                r'if.*side.*==.*["\']LONG["\'].*else.*SHORT',
                r'side.*=.*["\']LONG["\']',
                r'side.*=.*["\']SHORT["\']',
                r'position.*side.*switch',
                r'position.*direction.*change'
            ]
            
            found_patterns = []
            for pattern in switching_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    start_line = content[:match.start()].count('\n') + 1
                    found_patterns.append({
                        'pattern': pattern,
                        'line': start_line,
                        'match': match.group()
                    })
            
            if found_patterns:
                print(f'    ✅ Found position switching logic:')
                for pattern_info in found_patterns:
                    print(f'      - Pattern at line {pattern_info["line"]}: {pattern_info["match"][:50]}...')
            else:
                print(f'    ❌ No position switching logic found')
        
        except Exception as e:
            print(f'    ⚠️  Error analyzing {position_manager_file}: {e}')
    
    # Check trade orchestrator for cross logic
    print('\n[5] DETAILED TRADE ORCHESTRATOR ANALYSIS')
    
    trade_orchestrator_file = 'core/trade_orchestrator.py'
    if os.path.exists(trade_orchestrator_file):
        print(f'\n  🔍 Deep Analysis: {trade_orchestrator_file}')
        
        try:
            with open(trade_orchestrator_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for trade execution logic
            trade_patterns = [
                r'close.*position',
                r'open.*position',
                r'execute.*trade',
                r'place.*order',
                r'sell.*order',
                r'buy.*order',
                r'market.*order',
                r'limit.*order'
            ]
            
            found_trade_patterns = []
            for pattern in trade_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    start_line = content[:match.start()].count('\n') + 1
                    found_trade_patterns.append({
                        'pattern': pattern,
                        'line': start_line,
                        'match': match.group()
                    })
            
            if found_trade_patterns:
                print(f'    ✅ Found trade execution patterns:')
                for pattern_info in found_trade_patterns[:10]:  # Show first 10
                    print(f'      - {pattern_info["pattern"]} at line {pattern_info["line"]}')
            else:
                print(f'    ❌ No trade execution patterns found')
        
        except Exception as e:
            print(f'    ⚠️  Error analyzing {trade_orchestrator_file}: {e}')
    
    # Summary analysis
    print('\n[6] CROSS LOGIC SUMMARY')
    
    total_files_checked = len(files_to_check) + len(config_files) + len(strategy_files)
    files_with_cross_logic = len([d for d in cross_logic_details if d['has_cross_logic']])
    
    print(f'  - Total Files Checked: {total_files_checked}')
    print(f'  - Files with Cross Logic: {files_with_cross_logic}')
    print(f'  - Configuration Files with Cross Logic: {len(config_cross_logic)}')
    print(f'  - Strategy Files with Cross Logic: {len(strategy_cross_logic)}')
    
    if cross_logic_found:
        print(f'\n  ✅ CROSS LOGIC FOUND:')
        
        for detail in cross_logic_details:
            if detail['has_cross_logic']:
                print(f'    - {detail["file"]}: {list(detail["found_terms"].keys())}')
        
        # Show specific cross logic files
        cross_logic_files = [d['file'] for d in cross_logic_details if d['has_cross_logic']]
        print(f'\n  📋 FILES CONTAINING CROSS LOGIC:')
        for file in cross_logic_files:
            print(f'    - {file}')
    else:
        print(f'\n  ❌ NO CROSS LOGIC FOUND')
        print(f'  - No position crossing logic detected in the system')
    
    # Check for manual cross implementation possibility
    print('\n[7] MANUAL CROSS IMPLEMENTATION ANALYSIS')
    
    # Check if system has components needed for manual cross
    required_components = [
        ('Position Manager', 'core/position_manager.py'),
        ('Trade Orchestrator', 'core/trade_orchestrator.py'),
        ('Order Executor', 'core/order_executor.py'),
        ('Signal Engine', 'core/signal_engine.py')
    ]
    
    available_components = []
    
    for component_name, filepath in required_components:
        if os.path.exists(filepath):
            print(f'  ✅ {component_name}: Available')
            available_components.append(component_name)
        else:
            print(f'  ❌ {component_name}: Not available')
    
    print(f'\n  📊 MANUAL CROSS FEASIBILITY:')
    if len(available_components) >= 3:
        print(f'  ✅ Manual cross implementation is POSSIBLE')
        print(f'  - Required components are available')
        print(f'  - Can implement cross logic using existing components')
    else:
        print(f'  ❌ Manual cross implementation is DIFFICULT')
        print(f'  - Missing required components')
        print(f'  - Need to implement missing components first')
    
    # Final recommendation
    print('\n[8] FINAL ANALYSIS')
    
    if cross_logic_found:
        print(f'  ✅ CONCLUSION: POSITION CROSS LOGIC EXISTS')
        print(f'  - System has built-in position crossing functionality')
        print(f'  - Cross logic found in {files_with_cross_logic} files')
        print(f'  - Can use existing cross functionality')
    else:
        print(f'  ❌ CONCLUSION: NO POSITION CROSS LOGIC')
        print(f'  - System does not have built-in position crossing functionality')
        print(f'  - Would need to implement cross logic manually')
        print(f'  - Can implement using existing components: {len(available_components)}/4')
    
    print('\n' + '=' * 80)
    print('POSITION CROSS LOGIC ANALYSIS COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    analyze_position_cross_logic()
