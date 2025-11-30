from http.server import BaseHTTPRequestHandler
import json

def build_diff_report(text_a: str, text_b: str) -> str:
    """
    Compara dos textos línea por línea y genera
    un reporte tipo diferencias.txt.
    """
    lines_a = text_a.splitlines()
    lines_b = text_b.splitlines()
    max_lines = max(len(lines_a), len(lines_b))

    out_lines = []
    diff_count = 0

    for i in range(max_lines):
        la = lines_a[i] if i < len(lines_a) else ""
        lb = lines_b[i] if i < len(lines_b) else ""
        if la != lb:
            diff_count += 1
            out_lines.append(f"=== Diferencia en línea {i+1} ===")
            out_lines.append(f"A: {la}")
            out_lines.append(f"B: {lb}")
            out_lines.append("")

    header = [f"Total de diferencias: {diff_count}", ""]
    return "\n".join(header + out_lines)


class handler(BaseHTTPRequestHandler):
    """
    Vercel busca una clase llamada `handler` que herede de BaseHTTPRequestHandler.
    """

    def _set_headers_ok_with_file(self):
        self.send_response(200)
        # Indicamos que es texto plano
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        # Para que el navegador lo trate como archivo descargable
        self.send_header("Content-Disposition", 'attachment; filename="diferencias.txt"')
        self.end_headers()

    def _send_error(self, code: int, message: str):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode("utf-8"))

    def do_GET(self):
        """
        GET simple para probar que la función está viva.
        """
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        body = {
            "message": "API de comparación de ADN (usa POST para /api/compare).",
            "usage": "POST con JSON: {\"seqA\": \"...\", \"seqB\": \"...\"}"
        }
        self.wfile.write(json.dumps(body).encode("utf-8"))

    def do_POST(self):
        """
        Espera un JSON como:
          { "seqA": "texto de A", "seqB": "texto de B" }
        y devuelve un archivo diferencias.txt
        """
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._send_error(400, "Content-Length inválido.")

        if length <= 0:
            return self._send_error(400, "Body vacío.")

        body_bytes = self.rfile.read(length)
        try:
            data = json.loads(body_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            return self._send_error(400, "El body debe ser JSON válido.")

        seq_a = data.get("seqA")
        seq_b = data.get("seqB")

        if not isinstance(seq_a, str) or not isinstance(seq_b, str):
            return self._send_error(400, "JSON debe tener campos 'seqA' y 'seqB' como strings.")

        report = build_diff_report(seq_a, seq_b)

        # Responder con el "archivo"
        self._set_headers_ok_with_file()
        self.wfile.write(report.encode("utf-8"))


# ---- Modo local opcional para probar sin Vercel ----
if __name__ == "__main__":
    from http.server import HTTPServer
    print("Servidor local en http://localhost:8000 (POST con seqA y seqB en JSON)")
    server = HTTPServer(("0.0.0.0", 8000), handler)
    server.serve_forever()
