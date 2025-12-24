output "api_gateway_url" {
  value       = yandex_api_gateway.gateway.domain
  description = "API Gateway endpoint URL"
}
