# OpenTelemetry Collector (EKS)

## Validação pós-deploy

1. Verificar pods no namespace `monitoring`:
   ```bash
   kubectl get pods -n monitoring
   ```
   Confirme que `otel-collector`, Prometheus e Loki estão `Running`.

2. Confirmar o Service do Collector:
   ```bash
   kubectl get svc -n monitoring | grep otel
   ```

3. Gerar tráfego nos microserviços (via Ingress ou port-forward):
   ```bash
   curl http://<auth-service>/health
   ```

4. **Prometheus** — port-forward e consulta:
   ```bash
   kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
   ```
   No UI (`http://localhost:9090`), busque métricas HTTP, por exemplo:
   `http_server_duration_milliseconds_count` ou `http_server_request_duration_seconds_count` com label `service_name`.

5. **Grafana / Loki** — port-forward do Grafana:
   ```bash
   kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
   ```
   Login padrão: `admin` / senha definida em `prometheus-values.yaml`.  
   Explore → Loki → query: `{service_name="auth-service"}` (ajuste o label conforme aparecer no Explore).

6. Se métricas não chegarem:
   - Logs do Collector: `kubectl logs -n monitoring -l app.kubernetes.io/name=opentelemetry-collector`
   - Confirme `prometheus.prometheusSpec.enableRemoteWriteReceiver: true` no kube-prometheus-stack.
