#!/usr/bin/env python3
"""
Funding Dashboard - Real-time funding status and countdown
"""

import json
from datetime import datetime, timezone, timedelta
from core.position_manager import PositionManager

class FundingDashboard:
    def __init__(self):
        # Initialize with dummy parameters for dashboard functionality
        self.pm = None
        self.load_config()
        self.init_position_manager()
    
    def load_config(self):
        """Load funding configuration"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = {}
    
    def init_position_manager(self):
        """Initialize position manager with required parameters"""
        try:
            # Load trading results for position manager
            with open('trading_results.json', 'r') as f:
                trading_results = json.load(f)
            
            # Create dummy order executor and protective order manager
            class DummyOrderExecutor:
                def submit_order(self, *args, **kwargs):
                    return {'status': 'success', 'order_id': 'dummy'}
            
            class DummyProtectiveOrderManager:
                def __init__(self, *args, **kwargs):
                    pass
                def update_protective_orders(self, *args, **kwargs):
                    return True
            
            # Initialize position manager
            self.pm = PositionManager(
                trading_results=trading_results,
                order_executor=DummyOrderExecutor(),
                protective_order_manager=DummyProtectiveOrderManager()
            )
            
            # Add config attribute to position manager
            self.pm.config = self.config
            
        except Exception as e:
            print(f"Error initializing position manager: {e}")
            self.pm = None
    
    def get_funding_overview(self):
        """Get comprehensive funding overview"""
        try:
            funding_config = self.config.get('trading_config', {})
            
            overview = {
                'current_time': datetime.now(timezone.utc).isoformat(),
                'funding_enabled': funding_config.get('funding_countdown_enabled', False),
                'force_close_enabled': funding_config.get('force_close_before_funding', False),
                'lead_minutes': funding_config.get('funding_close_lead_minutes', 10),
                'funding_hours': funding_config.get('funding_hours', [0, 8, 16]),
                'next_funding_times': []
            }
            
            # Calculate next funding times
            if overview['funding_enabled']:
                now = datetime.now(timezone.utc)
                aligned = now.replace(minute=0, second=0, microsecond=0)
                
                for hour in overview['funding_hours']:
                    candidate = aligned.replace(hour=hour)
                    if candidate > now:
                        overview['next_funding_times'].append({
                            'time': candidate.isoformat(),
                            'hours_until': (candidate - now).total_seconds() / 3600
                        })
                
                # Add tomorrow's first funding if needed
                if len(overview['next_funding_times']) < 3:
                    tomorrow = aligned + timedelta(days=1)
                    candidate = tomorrow.replace(hour=overview['funding_hours'][0])
                    overview['next_funding_times'].append({
                        'time': candidate.isoformat(),
                        'hours_until': (candidate - now).total_seconds() / 3600
                    })
            
            return overview
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_position_funding_status(self):
        """Get funding status for all active positions"""
        try:
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
            
            active_positions = results.get('active_positions', {})
            position_status = []
            
            for symbol, position in active_positions.items():
                status = self.pm.get_funding_status(symbol, position)
                position_status.append(status)
            
            return position_status
            
        except Exception as e:
            return {'error': str(e)}
    
    def display_funding_dashboard(self):
        """Display comprehensive funding dashboard"""
        print('=' * 80)
        print('FUNDING DASHBOARD')
        print('=' * 80)
        
        # Overview
        overview = self.get_funding_overview()
        
        print(f"Current Time: {overview.get('current_time', 'N/A')}")
        print(f"Funding Enabled: {overview.get('funding_enabled', False)}")
        print(f"Force Close: {overview.get('force_close_enabled', False)}")
        print(f"Lead Time: {overview.get('lead_minutes', 0)} minutes")
        print(f"Funding Hours: {overview.get('funding_hours', [])}")
        
        print("\nNext Funding Times:")
        for funding_time in overview.get('next_funding_times', [])[:3]:
            hours_until = funding_time.get('hours_until', 0)
            time_str = funding_time.get('time', 'N/A')
            print(f"  - {time_str} (in {hours_until:.1f} hours)")
        
        # Position status
        print("\nPosition Funding Status:")
        positions = self.get_position_funding_status()
        
        for pos in positions:
            if 'error' not in pos:
                symbol = pos.get('symbol', 'Unknown')
                countdown = pos.get('countdown_minutes', 'N/A')
                close_window = pos.get('is_close_window', False)
                close_reason = pos.get('force_close_reason', 'None')
                
                print(f"  - {symbol}:")
                print(f"    * Countdown: {countdown} minutes")
                print(f"    * Close Window: {close_window}")
                print(f"    * Close Reason: {close_reason}")
        
        print('=' * 80)

if __name__ == "__main__":
    dashboard = FundingDashboard()
    dashboard.display_funding_dashboard()
