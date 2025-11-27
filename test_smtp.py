#!/usr/bin/env python3
"""
Script to test SMTP credentials and connection
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys

def test_smtp(host, port, username, password, use_ssl=True, use_tls=False):
    """Test SMTP connection and authentication"""
    
    print(f"\n{'='*60}")
    print(f"Testing SMTP Connection")
    print(f"{'='*60}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print(f"Use SSL: {use_ssl}")
    print(f"Use TLS: {use_tls}")
    print(f"{'='*60}\n")
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        
        print(f"[1] Creating SMTP connection...")
        
        if use_ssl:
            print(f"    → Using SSL/TLS (port {port})")
            server = smtplib.SMTP_SSL(host, port, context=context, timeout=10)
        else:
            print(f"    → Using plain connection (port {port})")
            server = smtplib.SMTP(host, port, timeout=10)
            
            if use_tls:
                print(f"    → Upgrading to TLS...")
                server.starttls(context=context)
        
        print(f"✅ Connection established\n")
        
        print(f"[2] Authenticating...")
        server.login(username, password)
        print(f"✅ Authentication successful\n")
        
        print(f"[3] Testing email sending...")
        from_email = "GPSControl4U <orders@gpscontrol.com.mx>"
        to_email = "test@example.com"
        
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "SMTP Test"
        
        body = "This is a test email from SMTP validation script."
        msg.attach(MIMEText(body, 'plain'))
        
        # Don't actually send, just verify we can send
        print(f"    → From: {from_email}")
        print(f"    → To: {to_email}")
        print(f"    → Message prepared (not actually sending)\n")
        
        print(f"[4] Closing connection...")
        server.quit()
        print(f"✅ Connection closed gracefully\n")
        
        print(f"{'='*60}")
        print(f"✅ ALL TESTS PASSED!")
        print(f"{'='*60}\n")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ AUTHENTICATION FAILED")
        print(f"   Error: {str(e)}")
        print(f"   → Check username and password\n")
        return False
        
    except smtplib.SMTPServerDisconnected as e:
        print(f"\n❌ SERVER DISCONNECTED")
        print(f"   Error: {str(e)}")
        print(f"   → Server closed connection unexpectedly")
        print(f"   → Check host, port, and SSL/TLS settings\n")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP ERROR")
        print(f"   Error: {str(e)}")
        print(f"   → Check SMTP configuration\n")
        return False
        
    except ConnectionRefusedError as e:
        print(f"\n❌ CONNECTION REFUSED")
        print(f"   Error: {str(e)}")
        print(f"   → Cannot connect to host {host}:{port}")
        print(f"   → Check host and port settings\n")
        return False
        
    except TimeoutError as e:
        print(f"\n❌ CONNECTION TIMEOUT")
        print(f"   Error: {str(e)}")
        print(f"   → Connection timed out to {host}:{port}")
        print(f"   → Check network connectivity\n")
        return False
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Configuration from .env
    host = "pro.turbo-smtp.com"
    port = 465
    username = "datacollect@madd.com.mx"
    password = "GPSc0ntr0l01"
    use_ssl = True
    use_tls = False
    
    print(f"\n🧪 Testing SMTP Configuration for GPSControl4U\n")
    
    success = test_smtp(host, port, username, password, use_ssl, use_tls)
    
    # Also test alternate configurations
    print(f"\n{'='*60}")
    print(f"Testing alternative configurations...")
    print(f"{'='*60}\n")
    
    configs = [
        {"name": "Port 587 with TLS", "port": 587, "ssl": False, "tls": True},
        {"name": "Port 25 with TLS", "port": 25, "ssl": False, "tls": True},
        {"name": "Port 465 without SSL", "port": 465, "ssl": False, "tls": False},
    ]
    
    for config in configs:
        print(f"\nTrying: {config['name']}")
        print(f"-" * 40)
        result = test_smtp(host, config['port'], username, password, config['ssl'], config['tls'])
        if result:
            print(f"✅ This configuration works!")
            break
    
    sys.exit(0 if success else 1)
