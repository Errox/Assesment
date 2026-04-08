# K8s Service Monitor API

Deze applicatie monitort interne services binnen een Kubernetes cluster (REST API en PostgreSQL) en exposeert de status via een beveiligde REST API endpoint.

## Architectuur Keuzes

1. **Omgevingsonafhankelijk**: Alle service endpoints en credentials worden geconfigureerd via omgevingsvariabelen (`.env` of K8s ConfigMaps/Secrets). Geen code wijzigingen nodig voor verschillende omgevingen (Dev/Test/Prod).
2. **Authenticatie**: Beveiligd met een `X-API-KEY` header. Deze sleutel is configureerbaar per omgeving.
3. **Uitbreidbaarheid**: Gebruikt een base `Checker` klasse. Nieuwe service types (bv. Redis, RabbitMQ) kunnen eenvoudig worden toegevoegd door een nieuwe klasse te maken die gebruik maakt van `BaseChecker`.

## Lokaal Testen (Zonder K8s)

### 1. Voorbereiding

```bash
pip install -r requirements.txt
cp .env .example-env # Pas waarden aan in .env indien nodig
```

### 2. Fake Targets starten

Om de monitor "echte" resultaten te laten geven zonder cluster:

* **REST API**: Start een simpele Python server in een aparte terminal:
  `python3 demo.py` (Dit simuleert een werkende API op poort 8001 met een werkende /health endpoint).
* **Postgres**: Gebruik Docker om een tijdelijke database te draaien:
  `docker run --name monitor-pg -e POSTGRES_PASSWORD=postgres_password -p 5432:5432 -d postgres`

### 3. De Monitor draaien

```bash
python3 main.py
```

### 4. Status opvragen

Gebruik `curl` of een browser/Postman:

```bash
curl -H "X-API-KEY: BCF2C1AF6C6214E205AC298EBEFC8CC0EA832435" http://localhost:8000/status
```
