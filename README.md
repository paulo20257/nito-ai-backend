# ZANGUI CRÉDITO

Protótipo demonstrativo de uma plataforma de informação e simulação de crédito em kwanzas.

## Estado atual
- Interface web responsiva em português.
- Simulador ilustrativo de prestações.
- API FastAPI com endpoint de saúde, configuração e simulação.
- A receção de pedidos reais está desativada.
- Não recolhe nem armazena documentos, dados pessoais ou dados bancários.

## Executar localmente
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Endpoints
- `GET /` — estado da aplicação.
- `GET /health` — verificação de saúde.
- `GET /api/config` — limites e estado do protótipo.
- `POST /api/simular` — simulação ilustrativa.
- `POST /api/pedidos` — permanece desativado (503).

## Exemplo de simulação
```json
{
  "amount": 200000,
  "months": 12,
  "monthly_rate": 0.03
}
```

## Antes de qualquer operação real
É obrigatório avaliar e cumprir os requisitos legais e regulatórios aplicáveis em Angola, incluindo licenciamento/autorização, identificação da entidade, contratos, informação pré-contratual, proteção de dados, segurança, controlo de acesso, gestão de reclamações e auditoria. Não recolher BI, biometria, credenciais ou dados bancários nesta versão.
