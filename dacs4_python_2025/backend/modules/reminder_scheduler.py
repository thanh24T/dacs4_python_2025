"""
AI Reminder Scheduler
Checks for pending reminders and triggers notifications
"""

import asyncio
import colorama
from typing import Callable
from datetime import datetime

colorama.init()


class ReminderScheduler:
    def __init__(self, database, check_interval: int = 30):
        """
        Initialize reminder scheduler
        
        Args:
            database: Database instance
            check_interval: How often to check for reminders (seconds)
        """
        self.database = database
        self.check_interval = check_interval
        self.is_running = False
        self.callback = None
        
        print(colorama.Fore.CYAN + f"[REMINDER] Scheduler initialized (check every {check_interval}s)" + colorama.Style.RESET_ALL)
    
    def set_callback(self, callback: Callable):
        """Set callback function to trigger when reminder is due"""
        self.callback = callback
    
    async def start(self):
        """Start the scheduler loop"""
        self.is_running = True
        print(colorama.Fore.GREEN + "[REMINDER] Scheduler started" + colorama.Style.RESET_ALL)
        
        while self.is_running:
            try:
                # Check for pending reminders
                pending = self.database.get_pending_reminders()
                
                if pending:
                    print(colorama.Fore.YELLOW + f"[REMINDER] Found {len(pending)} pending reminder(s)" + colorama.Style.RESET_ALL)
                    
                    for reminder in pending:
                        # Trigger callback if set (callback will mark as notified)
                        if self.callback:
                            await self.callback(reminder)
                        else:
                            # No callback set, mark as notified anyway
                            self.database.mark_reminder_notified(reminder['id'])
                        
                        print(colorama.Fore.GREEN + 
                              f"[REMINDER] ✅ Triggered: {reminder['title']} for {reminder['username']}" + 
                              colorama.Style.RESET_ALL)
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                print(colorama.Fore.RED + f"[REMINDER] Error: {e}" + colorama.Style.RESET_ALL)
                await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        print(colorama.Fore.YELLOW + "[REMINDER] Scheduler stopped" + colorama.Style.RESET_ALL)


# Test
if __name__ == "__main__":
    from database import ChatDatabase
    
    db = ChatDatabase()
    scheduler = ReminderScheduler(db, check_interval=10)
    
    async def test_callback(reminder):
        print(f"🔔 REMINDER: {reminder['title']} at {reminder['reminder_time']}")
    
    scheduler.set_callback(test_callback)
    
    print("Starting scheduler test...")
    asyncio.run(scheduler.start())
