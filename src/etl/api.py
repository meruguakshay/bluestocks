import os
import json
import sqlite3
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_PATH = os.getenv("DB_PATH", "db/nifty100.db")

class FinancialApiHandler(BaseHTTPRequestHandler):
    def connect_db(self):
        return sqlite3.connect(DB_PATH)
        
    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path.strip("/")
        parts = path.split("/")
        
        # 1. /api/companies
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "companies":
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT company_id, company_name, market_cap_category FROM companies")
            rows = cursor.fetchall()
            conn.close()
            
            companies = [{"ticker": r[0], "name": r[1], "cap": r[2]} for r in rows]
            self._send_response(200, companies)
            return

        # 2. /api/company/<ticker>
        elif len(parts) == 3 and parts[0] == "api" and parts[1] == "company":
            ticker = parts[2].upper()
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM companies WHERE company_id = ?", (ticker,))
            col_names = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            conn.close()
            
            if row:
                company_profile = dict(zip(col_names, row))
                self._send_response(200, company_profile)
            else:
                self._send_response(404, {"error": f"Company {ticker} not found"})
            return

        # 3. /api/sector/<sector_name>
        elif len(parts) == 3 and parts[0] == "api" and parts[1] == "sector":
            sector_name = urllib.parse.unquote(parts[2])
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.company_id, c.company_name
                FROM companies c
                JOIN sectors s ON c.sector_id = s.sector_id
                WHERE s.broad_sector LIKE ?
            """, (f"%{sector_name}%",))
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                constituents = [{"ticker": r[0], "name": r[1]} for r in rows]
                self._send_response(200, {"sector": sector_name, "companies": constituents})
            else:
                self._send_response(404, {"error": f"Sector {sector_name} not found"})
            return

        # 4. /api/ratios/<ticker>
        elif len(parts) == 3 and parts[0] == "api" and parts[1] == "ratios":
            ticker = parts[2].upper()
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year DESC", (ticker,))
            col_names = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                ratios_history = [dict(zip(col_names, row)) for row in rows]
                self._send_response(200, {"ticker": ticker, "ratios": ratios_history})
            else:
                self._send_response(404, {"error": f"No ratios found for company {ticker}"})
            return
            
        else:
            self._send_response(404, {"error": "Invalid API Endpoint", "valid_endpoints": [
                "/api/companies",
                "/api/company/<ticker>",
                "/api/sector/<sector_name>",
                "/api/ratios/<ticker>"
            ]})

def run(port=8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, FinancialApiHandler)
    print(f"Starting REST API server on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping REST API server...")
        httpd.server_close()

if __name__ == "__main__":
    run()
