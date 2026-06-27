import time
import subprocess
import sys
import os
from datetime import datetime
import logging

# ========== LOGGING CONFIGURATION ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scanner.log')
    ]
)
logger = logging.getLogger(__name__)

# ========== CONFIGURATION ==========
SCAN_INTERVAL = 3600  # 1 hour in seconds
MAX_RETRIES = 3
RETRY_DELAY = 60  # 1 minute between retries

# ========== GET CORRECT PATH ==========
# Get the directory where this script (scheduler.py) is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCANNER_PATH = os.path.join(SCRIPT_DIR, 'delta_scanner.py')

logger.info(f"📁 Scheduler directory: {SCRIPT_DIR}")
logger.info(f"📁 Looking for scanner at: {SCANNER_PATH}")
logger.info(f"📁 File exists: {os.path.exists(SCANNER_PATH)}")

def run_scanner():
    """
    Run the main scanner script with error handling and retries
    """
    logger.info("=" * 60)
    logger.info(f"🚀 Starting scanner at {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    logger.info("=" * 60)
    
    # Check if scanner file exists
    if not os.path.exists(SCANNER_PATH):
        logger.error(f"❌ Scanner file not found at: {SCANNER_PATH}")
        logger.error("Please make sure delta_scanner.py is in the same directory as scheduler.py")
        return False
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Run the scanner script using absolute path
            result = subprocess.run(
                [sys.executable, SCANNER_PATH],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            # Print output to console
            if result.stdout:
                logger.info("📊 Scanner Output:")
                logger.info(result.stdout)
            
            if result.stderr:
                logger.warning("⚠️ Scanner Errors:")
                logger.warning(result.stderr)
            
            # Check if successful
            if result.returncode == 0:
                logger.info(f"✅ Scanner completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
                return True
            else:
                logger.error(f"❌ Scanner failed with return code: {result.returncode}")
                
                if attempt < MAX_RETRIES:
                    logger.info(f"🔄 Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("❌ All retry attempts failed")
                    
        except subprocess.TimeoutExpired:
            logger.error("❌ Scanner timed out after 10 minutes")
            if attempt < MAX_RETRIES:
                logger.info(f"🔄 Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("❌ All retry attempts failed due to timeout")
                
        except Exception as e:
            logger.error(f"❌ Unexpected error running scanner: {e}")
            if attempt < MAX_RETRIES:
                logger.info(f"🔄 Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("❌ All retry attempts failed")
    
    return False

def send_telegram_test_message():
    """
    Send a test message to verify Telegram integration is working
    """
    try:
        import requests
        
        BOT_TOKEN = "8809200223:AAHmR969mpLw_jEuH2iVeLJ1RcGY8DeosXA"
        CHAT_ID = "503404993"
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': f"🔄 Scheduler started!\n📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n⏰ Will run every hour\n📁 Scanner path: {SCANNER_PATH}",
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Test message sent to Telegram")
            return True
        else:
            logger.error(f"❌ Failed to send test message: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Could not send test message: {e}")
        return False

def main():
    """
    Main scheduler loop
    """
    logger.info("=" * 60)
    logger.info("🔄 DELTA SCANNER SCHEDULER STARTED")
    logger.info(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    logger.info(f"⏰ Scan interval: {SCAN_INTERVAL // 3600} hour(s)")
    logger.info(f"🔄 Max retries: {MAX_RETRIES}")
    logger.info(f"📁 Scanner path: {SCANNER_PATH}")
    logger.info("=" * 60)
    
    # Check if scanner exists before starting
    if not os.path.exists(SCANNER_PATH):
        logger.error("❌ CRITICAL: delta_scanner.py not found!")
        logger.error(f"Please make sure delta_scanner.py is in: {SCRIPT_DIR}")
        return
    
    # Send notification to Telegram that scheduler is running
    send_telegram_test_message()
    
    # Track statistics
    run_count = 0
    success_count = 0
    failure_count = 0
    
    # Run first scan immediately
    logger.info("\n🔄 Running initial scan...")
    if run_scanner():
        success_count += 1
    else:
        failure_count += 1
    run_count += 1
    
    # Main loop - run every hour
    while True:
        logger.info(f"\n⏰ Next scan in {SCAN_INTERVAL // 60} minutes...")
        logger.info(f"📊 Statistics: {run_count} runs, {success_count} successful, {failure_count} failed")
        
        # Wait for the next interval
        time.sleep(SCAN_INTERVAL)
        
        # Run the scanner
        logger.info(f"\n🔄 Running scan #{run_count + 1}...")
        if run_scanner():
            success_count += 1
        else:
            failure_count += 1
        run_count += 1

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error in scheduler: {e}")
        sys.exit(1)